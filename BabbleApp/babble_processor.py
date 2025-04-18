from operator import truth
from dataclasses import dataclass
import sys
import asyncio

sys.path.append(".")
from config import BabbleCameraConfig, BabbleSettingsConfig, BabbleConfig
import queue
import threading
import numpy as np
import cv2
from enum import Enum
from one_euro_filter import OneEuroFilter
from utils.misc_utils import playSound, onnx_providers
import importlib
from osc import Tab
from osc_calibrate_filter import *
from tab import CamInfo, CamInfoOrigin
from babble_model_loader import *
import os

os.environ["OMP_NUM_THREADS"] = "1"
import onnxruntime as ort
from lang_manager import LocaleStringManager as lang


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


async def delayed_setting_change(setting, value):
    await asyncio.sleep(5)
    setting = value
    playSound(os.path.join("Audio", "completed.wav"))


class BabbleProcessor:
    def __init__(
        self,
        config: "BabbleCameraConfig",
        settings: "BabbleSettingsConfig",
        fullconfig: "BabbleConfig",
        cancellation_event: "threading.Event",
        capture_event: "threading.Event",
        capture_queue_incoming: "queue.Queue(maxsize=2)",
        image_queue_outgoing: "queue.Queue(maxsize=2)",
        cam_id,
        osc_queue: queue.Queue,
    ):
        self.main_config = BabbleSettingsConfig
        self.config = config
        self.settings = settings
        self.cam_id = cam_id
        self.config_class = fullconfig
        # Cross-thread communication management
        self.capture_queue_incoming = capture_queue_incoming
        self.image_queue_outgoing = image_queue_outgoing
        self.cancellation_event = cancellation_event
        self.capture_event = capture_event
        self.cam_id = cam_id
        self.osc_queue = osc_queue

        # Image state
        self.previous_image = None
        self.current_image = None
        self.current_image_gray = None
        self.current_frame_number = None
        self.current_fps = None
        self.FRAMESIZE = [0, 0, 1]

        self.calibration_frame_counter = None

        self.cccs = False
        self.ts = 10
        self.previous_rotation = self.config.rotation_angle
        self.roi_include_set = {"rotation_angle", "roi_window_x", "roi_window_y"}

        self.current_algo = CamInfoOrigin.MODEL
        self.model = self.settings.gui_model_file
        self.runtime = self.settings.gui_runtime
        self.use_gpu = self.settings.gui_use_gpu
        self.gpu_index = self.settings.gui_gpu_index
        config_default: BabbleConfig = BabbleConfig()
        self.default_model = config_default.settings.gui_model_file
        self.output = []
        self.val_list = []
        self.calibrate_config = np.empty((1, 45))
        self.min_max_array = np.empty((2, 45))

        ort.disable_telemetry_events()
        self.opts = ort.SessionOptions()
        self.opts.inter_op_num_threads = 1
        self.opts.intra_op_num_threads = settings.gui_inference_threads
        self.opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.opts.add_session_config_entry("session.intra_op.allow_spinning", "0")  # ~3% savings worth ~6ms avg latency. Not noticeable at 60fps?
        self.opts.enable_mem_pattern = False
        if self.runtime in ("ONNX", "Default (ONNX)"):  # ONNX
            if self.use_gpu:
                provider = onnx_providers
            else:
                provider = [onnx_providers[-1]]
            try:
                self.sess = ort.InferenceSession(
                    f"{self.model}/onnx/model.onnx",
                    self.opts,
                    providers=provider,
                )
            except:                                                 # Load default model if we can't find the specified model
                print(
                f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("error.modelLoad")} {self.model}\033[0m'
                )
                print(f'\033[91mLoading Default model: {self.default_model}.\033[0m')
                self.sess = ort.InferenceSession(
                    f"{self.default_model}/onnx/model.onnx",  
                    self.opts,
                    providers=[provider],
                    provider_options=[{"device_id": self.gpu_index}],
                )
            self.input_name = self.sess.get_inputs()[0].name
            self.output_name = self.sess.get_outputs()[0].name
        try:
            min_cutoff = float(self.settings.gui_min_cutoff)
            beta = float(self.settings.gui_speed_coefficient)
        except:
            print(
                f'\033[93m[{lang._instance.get_string("log.warn")}] {lang._instance.get_string("warn.oneEuroValues")}.\033[0m'
            )
            min_cutoff = 0.9
            beta = 0.9
        noisy_point = np.array([45])
        self.one_euro_filter = OneEuroFilter(
            noisy_point, min_cutoff=min_cutoff, beta=beta
        )
        # Persistent calibrator instance for continuous calibration
        self._calibrator = None

    def process_output(self, output_array):
        # Called after model inference, applies calibration if enabled
        if self.settings.use_calibration:
            if self._calibrator is None or (hasattr(self._calibrator, 'calibrator') and self._calibrator.calibrator is not None and self._calibrator.calibrator.num_blendshapes != len(output_array)):
                from osc_calibrate_filter import cal
                self._calibrator = cal(self.settings)
            return self._calibrator.cal_osc(output_array)
        else:
            return output_array

    def output_images_and_update(self, output_information: CamInfo):
        try:
            image_stack = np.concatenate(
                (cv2.cvtColor(self.current_image_gray, cv2.COLOR_GRAY2BGR),),
                axis=1,
            )
            self.image_queue_outgoing.put((image_stack, output_information))
            if self.image_queue_outgoing.qsize() > 1:
                self.image_queue_outgoing.get()
                
            self.previous_image = self.current_image
            self.previous_rotation = self.config.rotation_angle

            # Relay information to OSC
            self.osc_queue.put((None, output_information))
        except:  # If this fails it likely means that the images are not the same size for some reason.
            print(
                f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("error.size")}.\033[0m'
            )

    def capture_crop_rotate_image(self):
        # Get our current frame

        try:
            # Get frame from capture source, crop to ROI
            self.FRAMESIZE = self.current_image.shape
            self.current_image = self.current_image[
                int(self.config.roi_window_y) : int(
                    self.config.roi_window_y + self.config.roi_window_h
                ),
                int(self.config.roi_window_x) : int(
                    self.config.roi_window_x + self.config.roi_window_w
                ),
            ]

        except:
            # Failure to process frame, reuse previous frame.
            self.current_image = self.previous_image
            print(
                f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("error.capture")}.\033[0m'
            )

        try:
            # Apply rotation to cropped area. For any rotation area outside of the bounds of the image,
            # fill with white.
            try:
                rows, cols, _ = self.current_image.shape
            except:
                rows, cols, _ = self.previous_image.shape

            if self.config.gui_vertical_flip:
                self.current_image = cv2.flip(self.current_image, 0)

            if self.config.gui_horizontal_flip:
                self.current_image = cv2.flip(self.current_image, 1)

            img_center = (cols / 2, rows / 2)
            rotation_matrix = cv2.getRotationMatrix2D(
                img_center, self.config.rotation_angle, 1
            )
            avg_color_per_row = np.average(self.current_image, axis=0)
            avg_color = np.average(avg_color_per_row, axis=0)
            ar, ag, ab = avg_color
            self.current_image = cv2.warpAffine(
                self.current_image,
                rotation_matrix,
                (cols, rows),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(ar + 10, ag + 10, ab + 10),  # (255, 255, 255),
            )
            self.current_image_white = cv2.warpAffine(
                self.current_image,
                rotation_matrix,
                (cols, rows),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255, 255, 255),
            )
            return True
        except:
            pass

    def run(self):

        while True:
            # Check to make sure we haven't been requested to close
            if self.cancellation_event.is_set():
                print(
                    f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.exitTrackingThread")}\033[0m'
                )
                return

            if self.config.roi_window_w <= 0 or self.config.roi_window_h <= 0:
                # At this point, we're waiting for the user to set up the ROI window in the GUI.
                # Sleep a bit while we wait.
                if self.cancellation_event.wait(0.1):
                    return
                continue

            try:
                if self.capture_queue_incoming.empty():
                    self.capture_event.set()
                # Wait a bit for images here. If we don't get one, just try again.
                (
                    self.current_image,
                    self.current_frame_number,
                    self.current_fps,
                ) = self.capture_queue_incoming.get(block=True, timeout=0.1)
            except queue.Empty:
                # print("No image available")
                continue

            if not self.capture_crop_rotate_image():
                continue

            if self.settings.gui_use_red_channel:  # Make G and B channels equal to red.
                blue_channel, green_channel, red_channel = cv2.split(self.current_image)
                new_blue_channel = red_channel
                new_green_channel = red_channel
                self.current_image = cv2.merge(
                    (new_blue_channel, new_green_channel, red_channel)
                )
            self.current_image_gray = cv2.cvtColor(
                self.current_image, cv2.COLOR_BGR2GRAY
            )
            self.current_image_gray_clean = (
                self.current_image_gray.copy()
            )  # copy this frame to have a clean image for blink algo

            run_model(self)
            # Replace the old calibration logic with the new persistent calibrator usage
            # if self.settings.use_calibration:
            #     self.output = cal(self.settings).cal_osc(self.output)
            # New code:
            self.output = self.process_output(self.output)
            # else:
            #   pass
            # print(self.output)
            
            self.output_images_and_update(CamInfo(self.current_algo, self.output))

    def get_framesize(self):
        return self.FRAMESIZE
