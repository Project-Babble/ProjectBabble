
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
from utils.misc_utils import PlaySound, SND_FILENAME, SND_ASYNC
import importlib
from osc import Tab
from osc_calibrate_filter import *
from tab import CamInfo, CamInfoOrigin
from babble_model_loader import *
import os
os.environ["OMP_NUM_THREADS"] = "1"
import onnxruntime as ort

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
    PlaySound('Audio/completed.wav', SND_FILENAME | SND_ASYNC)



class BabbleProcessor:
    def __init__(
        self,
        config: "BabbleCameraConfig",
        settings: "BabbleSettingsConfig",
        fullconfig: "BabbleConfig",
        cancellation_event: "threading.Event",
        capture_event: "threading.Event",
        capture_queue_incoming: "queue.Queue",
        image_queue_outgoing: "queue.Queue",
        cam_id,
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

        # Image state
        self.previous_image = None
        self.current_image = None
        self.current_image_gray = None
        self.current_frame_number = None
        self.current_fps = None

        self.calibration_frame_counter = None

        self.cccs = False
        self.ts = 10
        self.previous_rotation = self.config.rotation_angle
        self.roi_include_set = {"rotation_angle", "roi_window_x", "roi_window_y"}

        self.current_algo = CamInfoOrigin.MODEL
        self.model = self.settings.gui_model_file
        self.backend = self.settings.gui_backend
        self.use_gpu = self.settings.gui_use_gpu
        self.gpu_index = self.settings.gui_gpu_index
        self.output = []
        self.val_list = []
        self.calibrate_config = np.empty((1, 45))
        self.min_max_array = np.empty((2, 45))

        self.opts = ort.SessionOptions()
        self.opts.intra_op_num_threads = settings.gui_inference_threads
        self.opts.inter_op_num_threads = settings.gui_inference_threads # Figure out how to set openvino threads
        self.opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        if self.backend == 0:   # OpenVino
            if self.use_gpu: provider = f'GPU{self.gpu_index}'
            else: provider = 'CPU'
            ie = IECore()
            net = ie.read_network(model=f'{self.model}openvino/model.xml', weights=f'{self.model}openvino/model.bin')
            self.sess = ie.load_network(network=net, device_name=provider)
            self.input_name = next(iter(net.input_info))
            self.output_name = next(iter(net.outputs))
        if self.backend == 1:    # ONNX 
            if self.use_gpu: provider = 'DmlExecutionProvider' # Figure out how to set ONNX gpu index
            else: provider = "CPUExecutionProvider" 
            self.sess = ort.InferenceSession(f'{self.model}onnx/model.onnx', self.opts, providers=[provider]) 
            self.input_name = self.sess.get_inputs()[0].name
            self.output_name = self.sess.get_outputs()[0].name
        

        try:
            min_cutoff = float(self.settings.gui_min_cutoff)  # 15.5004
            beta = float(self.settings.gui_speed_coefficient)  # 0.62
        except:
            print('\033[93m[WARN] OneEuroFilter values must be a legal number.\033[0m')
            min_cutoff = 10.0004
            beta = 0.62
        noisy_point = np.array([45])
        self.one_euro_filter = OneEuroFilter(
            noisy_point,
            min_cutoff=min_cutoff,
            beta=beta
        )

    def output_images_and_update(self, output_information: CamInfo):
        try:
            image_stack = np.concatenate(
                (
                    cv2.cvtColor(self.current_image_gray, cv2.COLOR_GRAY2BGR),
                ),
                axis=1,
            )
            self.image_queue_outgoing.put((image_stack, output_information))
            self.previous_image = self.current_image
            self.previous_rotation = self.config.rotation_angle
        except: # If this fails it likely means that the images are not the same size for some reason.
            print('\033[91m[ERROR] Size of frames to display are of unequal sizes.\033[0m')

            pass
    def capture_crop_rotate_image(self):
        # Get our current frame
        
        try:
            # Get frame from capture source, crop to ROI
            self.current_image = self.current_image[
                int(self.config.roi_window_y): int(
                    self.config.roi_window_y + self.config.roi_window_h
                ),
                int(self.config.roi_window_x): int(
                    self.config.roi_window_x + self.config.roi_window_w
                ),
            ]

    
        except:
            # Failure to process frame, reuse previous frame.
            self.current_image = self.previous_image
            print("\033[91m[ERROR] Frame capture issue detected.\033[0m")

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
                borderValue=(ar + 10, ag + 10, ab + 10),#(255, 255, 255),
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
                print("\033[94m[INFO] Exiting Tracking thread\033[0m")
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
                ) = self.capture_queue_incoming.get(block=True, timeout=0.2)
            except queue.Empty:
                # print("No image available")
                continue
            
            if not self.capture_crop_rotate_image():
                continue

            if self.settings.gui_use_red_channel:     # Make G and B channels equal to red.
                blue_channel, green_channel, red_channel = cv2.split(self.current_image)
                new_blue_channel = red_channel
                new_green_channel = red_channel
                self.current_image = cv2.merge((new_blue_channel, new_green_channel, red_channel))

            self.current_image_gray = cv2.cvtColor(
            self.current_image, cv2.COLOR_BGR2GRAY
            )
            self.current_image_gray_clean = self.current_image_gray.copy() #copy this frame to have a clean image for blink algo


            run_model(self)
            if self.config.use_calibration:
                self.output = cal.cal_osc(self, self.output)

            #else:
             #   pass
            #print(self.output)
            self.output_images_and_update(CamInfo(self.current_algo, self.output))

