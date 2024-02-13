import PySimpleGUI as sg
from config import BabbleConfig
from config import BabbleSettingsConfig
from collections import deque
from threading import Event, Thread
from babble_processor import BabbleProcessor, CamInfoOrigin
from landmark_processor import LandmarkProcessor
from enum import Enum
from queue import Queue, Empty
from camera import Camera, CameraState
from osc import Tab
import cv2
import sys
from utils.misc_utils import PlaySound,SND_FILENAME,SND_ASYNC
import traceback
import numpy as np

class CameraWidget:
    def __init__(self, widget_id: Tab, main_config: BabbleConfig, osc_queue: Queue):
        self.gui_camera_addr = f"-CAMERAADDR{widget_id}-"
        self.gui_rotation_slider = f"-ROTATIONSLIDER{widget_id}-"
        self.gui_roi_button = f"-ROIMODE{widget_id}-"
        self.gui_roi_layout = f"-ROILAYOUT{widget_id}-"
        self.gui_roi_selection = f"-GRAPH{widget_id}-"
        self.gui_tracking_button = f"-TRACKINGMODE{widget_id}-"
        self.gui_autoroi = f"-AUTOROI{widget_id}-"
        self.gui_save_tracking_button = f"-SAVETRACKINGBUTTON{widget_id}-"
        self.gui_tracking_layout = f"-TRACKINGLAYOUT{widget_id}-"
        self.gui_tracking_image = f"-IMAGE{widget_id}-"
        self.gui_tracking_fps = f"-TRACKINGFPS{widget_id}-"
        self.gui_tracking_bps = f"-TRACKINGBPS{widget_id}-"
        self.gui_output_graph = f"-OUTPUTGRAPH{widget_id}-"
        self.gui_restart_calibration = f"-RESTARTCALIBRATION{widget_id}-"
        self.gui_stop_calibration = f"-STOPCALIBRATION{widget_id}-"
        self.gui_mode_readout = f"-APPMODE{widget_id}-"
        self.gui_roi_message = f"-ROIMESSAGE{widget_id}-"
        self.gui_vertical_flip = f"-VERTICALFLIP{widget_id}-"
        self.gui_horizontal_flip = f"-HORIZONTALFLIP{widget_id}-"
        self.use_calibration = f"-USECALIBRATION{widget_id}-"
        self.use_n_calibration = f"-USENCALIBRATION{widget_id}-"
        self.osc_queue = osc_queue
        self.main_config = main_config
        self.cam_id = widget_id
        self.settings_config = main_config.settings
        self.config = main_config.cam
        self.settings = main_config.settings
        if self.cam_id == Tab.CAM:
            self.config = main_config.cam
        else:
            raise RuntimeError("\033[91m[WARN] Improper tab value!\033[0m")

        self.cancellation_event = Event()
        # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.capture_event = Event()
        self.capture_queue = Queue(maxsize=2)
        self.roi_queue = Queue(maxsize=2)
        self.image_queue = Queue(maxsize=500)

        self.babble_cnn = BabbleProcessor(
            self.config,
            self.settings_config,
            self.main_config,
            self.cancellation_event,
            self.capture_event,
            self.capture_queue,
            self.image_queue,
            self.cam_id,
        )

        self.babble_landmark = LandmarkProcessor(
            self.config,
            self.settings_config,
            self.main_config,
            self.cancellation_event,
            self.capture_event,
            self.capture_queue,
            self.image_queue,
            self.cam_id,
        )

        self.camera_status_queue = Queue(maxsize=2)
        self.camera = Camera(
            self.config,
            0,
            self.cancellation_event,
            self.capture_event,
            self.camera_status_queue,
            self.capture_queue,
            self.settings
        )

        self.roi_layout = [
            [
            sg.Button("Auto ROI", key=self.gui_autoroi, button_color='#539e8a', tooltip = "Automatically set ROI",),
            ],
            [
            sg.Graph( 
                (640, 480),
                (0, 480),
                (640, 0),
                key=self.gui_roi_selection,
                drag_submits=True,
                enable_events=True,
                background_color='#424042',
                )
            ]
        ]

        # Define the window's contents
        self.tracking_layout = [
            [
                sg.Text("Rotation", background_color='#424042'),
                sg.Slider(
                    range=(0, 360),
                    default_value=self.config.rotation_angle,
                    orientation="h",
                    key=self.gui_rotation_slider,
                    background_color='#424042',
                    tooltip = "Adjust the rotation of your cameras, make them level.",
                ),
            ],
            [
                sg.Button("Start Calibration", key=self.gui_restart_calibration, button_color='#539e8a', tooltip = "Start calibration. Look all arround to all extreams without blinking until sound is heard.",),
                sg.Button("Stop Calibration", key=self.gui_stop_calibration, button_color='#539e8a', tooltip = "Stop calibration manualy.",),
            ],
            [
                sg.Checkbox(
                    "Use Neutral Calibration:",
                    default=self.config.use_n_calibration,
                    key=self.use_n_calibration,
                    background_color='#424042',
                    tooltip="Toggle use of calibration using minimum values found during a neutral pose calibration step.",
                ),
                sg.Checkbox(
                    "Use Full Calibration:",
                    default=self.config.use_calibration,
                    key=self.use_calibration,
                    background_color='#424042',
                    tooltip="Toggle use of calibration.",
                ),
            ],
            [
                sg.Text("Mode:", background_color='#424042'),
                sg.Text("Calibrating", key=self.gui_mode_readout, background_color='#539e8a'),
                sg.Text("", key=self.gui_tracking_fps, background_color='#424042'),
                sg.Text("", key=self.gui_tracking_bps, background_color='#424042'),
            ],
            [
                sg.Checkbox(
                    "Vertical Flip:",
                    default=self.config.gui_vertical_flip,
                    key=self.gui_vertical_flip,
                    background_color='#424042',
                    tooltip = "Vertically flip camera feed.",
                ),
                sg.Checkbox(
                    "Horizontal Flip:",
                    default=self.config.gui_horizontal_flip,
                    key=self.gui_horizontal_flip,
                    background_color='#424042',
                    tooltip="Horizontally flip camera feed.",
                ),
            ],
            [sg.Image(filename="", key=self.gui_tracking_image)],
            [
                sg.Text("Please set a Crop.", key=self.gui_roi_message, background_color='#424042', visible=False),
            ],
        ]

        self.widget_layout = [
            [
                sg.Text("Camera Address", background_color='#424042'),
                sg.InputText(self.config.capture_source, key=self.gui_camera_addr, tooltip = "Enter the IP address or UVC port of your camera. (Include the 'http://')",),
            ],
            [
                sg.Button("Save and Restart Tracking", key=self.gui_save_tracking_button, button_color='#539e8a'),
            ],
            [
                sg.Button("Tracking Mode", key=self.gui_tracking_button, button_color='#539e8a', tooltip = "Go here to track your mouth.",),
                sg.Button("Cropping Mode", key=self.gui_roi_button, button_color='#539e8a', tooltip = "Go here to crop out your mouth.",),
            ],
            [
                sg.Column(self.tracking_layout, key=self.gui_tracking_layout, background_color='#424042'),
                sg.Column(self.roi_layout, key=self.gui_roi_layout, background_color='#424042', visible=False),
            ],
        ]

        self.x0, self.y0 = None, None
        self.x1, self.y1 = None, None
        self.figure = None
        self.is_mouse_up = True
        self.in_roi_mode = False
        self.movavg_fps_queue = deque(maxlen=120)
        self.movavg_bps_queue = deque(maxlen=120)

    def _movavg_fps(self, next_fps):
        self.movavg_fps_queue.append(next_fps)
        fps = round(sum(self.movavg_fps_queue) / len(self.movavg_fps_queue))
        millisec = round((1 / fps if fps else 0) * 1000)
        return f"{fps} Fps {millisec} ms"

    def _movavg_bps(self, next_bps):
        self.movavg_bps_queue.append(next_bps)
        return f"{sum(self.movavg_bps_queue) / len(self.movavg_bps_queue) * 0.001 * 0.001 * 8:.3f} Mbps"

    def started(self):
        return not self.cancellation_event.is_set()

    def start(self):
        # If we're already running, bail
        if not self.cancellation_event.is_set():
            return
        self.cancellation_event.clear()
        self.babble_cnn_thread = Thread(target=self.babble_cnn.run)
        self.babble_cnn_thread.start()
        self.babble_landmark_thread = Thread(target=self.babble_landmark.run)
        self.babble_landmark_thread.start()
        self.camera_thread = Thread(target=self.camera.run)
        self.camera_thread.start()

    def stop(self):
        # If we're not running yet, bail
        if self.cancellation_event.is_set():
            return
        self.cancellation_event.set()
        self.babble_cnn_thread.join()
        self.babble_landmark_thread.join()
        self.camera_thread.join()

    def render(self, window, event, values):
        if self.image_queue.qsize() > 2:
            with self.image_queue.mutex:
                self.image_queue.queue.clear()
        else:
            pass
        changed = False
        # If anything has changed in our configuration settings, change/update those.
        if (
            event == self.gui_save_tracking_button
            and values[self.gui_camera_addr] != self.config.capture_source
        ):
            print("\033[94m[INFO] New value: {}\033[0m".format(values[self.gui_camera_addr]))
            try:
                self.config.use_ffmpeg = False
                # Try storing ints as ints, for those using wired cameras.
                self.config.capture_source = int(values[self.gui_camera_addr])
            except ValueError:
                if values[self.gui_camera_addr] == "":
                    self.config.capture_source = None
                else:
                    if len(values[self.gui_camera_addr]) > 5 and "http" not in values[self.gui_camera_addr] and ".mp4" not in values[self.gui_camera_addr] and "udp" not in values[self.gui_camera_addr]: # If http is not in camera address, add it.
                        self.config.capture_source = f"http://{values[self.gui_camera_addr]}/"
                    elif "udp" in values[self.gui_camera_addr]:
                        self.config.use_ffmpeg = True
                        self.config.capture_source = values[self.gui_camera_addr]
                    else:
                        self.config.capture_source = values[self.gui_camera_addr]
            changed = True



        if self.config.rotation_angle != values[self.gui_rotation_slider]:
            self.config.rotation_angle = int(values[self.gui_rotation_slider])
            changed = True

        #print(self.config.gui_vertical_flip)
        if self.config.gui_vertical_flip != values[self.gui_vertical_flip]:
            self.config.gui_vertical_flip = values[self.gui_vertical_flip]
            changed = True

        if self.config.gui_horizontal_flip != values[self.gui_horizontal_flip]:
            self.config.gui_horizontal_flip = values[self.gui_horizontal_flip]
            changed = True

        if self.config.use_calibration != values[self.use_calibration]:
            self.config.use_calibration = values[self.use_calibration]
            changed = True

        if self.config.use_n_calibration != values[self.use_n_calibration]:
            self.config.use_n_calibration = values[self.use_n_calibration]
            changed = True

        if changed:
            self.main_config.save()

        if event == self.gui_tracking_button:
            print("\033[94m[INFO] Moving to tracking mode\033[0m")
            self.in_roi_mode = False
            self.camera.set_output_queue(self.capture_queue)
            window[self.gui_roi_layout].update(visible=False)
            window[self.gui_tracking_layout].update(visible=True)

        if event == self.gui_roi_button:
            print("\033[94m[INFO] Move to roi mode\033[0m")
            self.in_roi_mode = True
            self.camera.set_output_queue(self.roi_queue)
            window[self.gui_roi_layout].update(visible=True)
            window[self.gui_tracking_layout].update(visible=False)

        if event == "{}+UP".format(self.gui_roi_selection):
            # Event for mouse button up in ROI mode
            self.is_mouse_up = True
            if self.x1 < 0:
                    self.x1 = 0
            if self.y1 < 0:
                    self.y1 = 0 
            if abs(self.x0 - self.x1) != 0 and abs(self.y0 - self.y1) != 0:
                self.config.roi_window_x = min([self.x0, self.x1])
                self.config.roi_window_y = min([self.y0, self.y1])
                self.config.roi_window_w = abs(self.x0 - self.x1)
                self.config.roi_window_h = abs(self.y0 - self.y1)
                self.main_config.save()

        if event == self.gui_autoroi:
            print("Auto ROI")
            #image = self.image_queue.get()
            #image = self.babble_landmark.get_frame()    # Get image for pfld 
            #print(image)
            #print(len(image))
            #print(image)
            #cv2.imwrite("yeah.png", image)
            self.babble_landmark.infer_frame()
            output = self.babble_landmark.output
            print(f"Output: {output}")
            self.x1 = output[2]
            self.y1 = output[3]
            self.x0 = output[0]
            self.y0 = output[1]
            self.config.roi_window_x = min([self.x0, self.x1])
            self.config.roi_window_y = min([self.y0, self.y1])
            self.config.roi_window_w = abs(self.x0 - self.x1)
            self.config.roi_window_h = abs(self.y0 - self.y1)
            self.main_config.save()

        if event == self.gui_roi_selection:
            # Event for mouse button down or mouse drag in ROI mode
            if self.is_mouse_up:
                self.is_mouse_up = False
                self.x0, self.y0 = values[self.gui_roi_selection]
            self.x1, self.y1 = values[self.gui_roi_selection]

        if event == self.gui_restart_calibration:
            self.babble_cnn.calibration_frame_counter = 1500
            PlaySound('Audio/start.wav', SND_FILENAME | SND_ASYNC)

        if event == self.gui_stop_calibration:
            self.babble_cnn.calibration_frame_counter = 0

        needs_roi_set = self.config.roi_window_h <= 0 or self.config.roi_window_w <= 0

        # TODO: Refactor if statements below...
        window[self.gui_tracking_fps].update('')
        window[self.gui_tracking_bps].update('')

        if self.config.capture_source is None or self.config.capture_source == "":
            window[self.gui_mode_readout].update("Waiting for camera address")
            window[self.gui_roi_message].update(visible=False)
        elif self.camera.camera_status == CameraState.CONNECTING:
            window[self.gui_mode_readout].update("Camera Connecting")
        elif self.camera.camera_status == CameraState.DISCONNECTED:
            window[self.gui_mode_readout].update("Camera Reconnecting...")
        elif needs_roi_set:
            window[self.gui_mode_readout].update("Awaiting Mouth Crop")
        elif self.babble_cnn.calibration_frame_counter != None:
            window[self.gui_mode_readout].update("Calibration")
        else:
            window[self.gui_mode_readout].update("Tracking")
            window[self.gui_tracking_fps].update(self._movavg_fps(self.camera.fps))
            window[self.gui_tracking_bps].update(self._movavg_bps(self.camera.bps))

        if self.in_roi_mode:
            try:    
                if self.roi_queue.empty():
                    self.capture_event.set()
                maybe_image = self.roi_queue.get(block=False)
                imgbytes = cv2.imencode(".ppm", maybe_image[0])[1].tobytes()
                graph = window[self.gui_roi_selection]
                if self.figure:
                    graph.delete_figure(self.figure)
                # INCREDIBLY IMPORTANT ERASE. Drawing images does NOT overwrite the buffer, the fucking
                # graph keeps every image fed in until you call this. Therefore we have to make sure we
                # erase before we redraw, otherwise we'll leak memory *very* quickly.
                graph.erase()
                graph.draw_image(data=imgbytes, location=(0, 0))
                if None not in (self.x0, self.y0, self.x1, self.y1):
                    self.figure = graph.draw_rectangle(
                        (self.x0, self.y0), (self.x1, self.y1), line_color="#6f4ca1"
                    )
            except Empty:
                pass
        else:
            if needs_roi_set:
                window[self.gui_roi_message].update(visible=True)
                return
            try:
                window[self.gui_roi_message].update(visible=False)
                (maybe_image, cam_info) = self.image_queue.get(block=False)
                imgbytes = cv2.imencode(".ppm", maybe_image)[1].tobytes()
                window[self.gui_tracking_image].update(data=imgbytes)


                # Relay information to OSC
                if cam_info.info_type != CamInfoOrigin.FAILURE:
                    self.osc_queue.put((self.cam_id, cam_info))
            except Empty:
                pass
