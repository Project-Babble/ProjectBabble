from queue import Queue, Empty
from threading import Event, Thread
import os

import kivy_ui as ui  # Must be imported before any other Kivy module
from kivy.uix.boxlayout import BoxLayout

from babble_processor import BabbleProcessor, CamInfoOrigin
from camera import Camera, CameraState
from config import BabbleConfig
from osc import Tab
from utils.misc_utils import (
    playSound,
    list_camera_names,
    bg_color_highlight,
    is_valid_int_input
)
from lang_manager import LocaleStringManager as lang


class CameraWidget:
    def __init__(self, widget_id: Tab, main_config: BabbleConfig, osc_queue: Queue):
        self.osc_queue = osc_queue
        self.main_config = main_config
        self.cam_id = widget_id
        self.settings_config = main_config.settings
        self.config = main_config.cam
        self.settings = main_config.settings
        self.camera_list = list_camera_names()
        self.maybe_image = None
        if self.cam_id == Tab.CAM:
            self.config = main_config.cam
        else:
            raise RuntimeError(
                f'\033[91m[{lang._instance.get_string("log.warn")}] {lang._instance.get_string("error.improperTabValue")}\033[0m'
            )

        self.cancellation_event = Event()
        # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.capture_event = Event()
        self.capture_queue = Queue(maxsize=2)
        self.roi_queue = Queue(maxsize=2)
        self.image_queue = Queue(maxsize=500) # This is needed to prevent the UI from freezing during widget changes.

        self.babble_cnn = BabbleProcessor(
            self.config,
            self.settings_config,
            self.main_config,
            self.cancellation_event,
            self.capture_event,
            self.capture_queue,
            self.image_queue,
            self.cam_id,
            self.osc_queue,
        )

        self.camera_status_queue = Queue(maxsize=2)
        self.camera = Camera(
            self.config,
            0,
            self.cancellation_event,
            self.capture_event,
            self.camera_status_queue,
            self.capture_queue,
            self.settings,
        )

        self.in_roi_mode = False
        self.bps = 0
        self._build_layout()

    # ------------------------------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------------------------------
    def _build_layout(self):
        s = lang._instance.get_string

        # --- Cropping (ROI) view ---
        self.roi_layout = ui.Panel(bg=bg_color_highlight)
        self.roi_layout.add_widget(
            ui.row(
                ui.button(
                    s("camera.selectEntireFrame"),
                    on_press=self.on_select_entire_frame,
                    tooltip=s("camera.selectEntireFrameTooltip"),
                )
            )
        )
        self.roi_selector = ui.ROISelector(on_select=self.on_roi_selected)
        self.roi_layout.add_widget(self.roi_selector)

        # --- Tracking view ---
        self.tracking_layout = ui.Panel(bg=bg_color_highlight)
        self.rotation_value = ui.label(str(int(self.config.rotation_angle)), bg=bg_color_highlight)
        self.tracking_layout.add_widget(
            ui.row(
                ui.label(s("camera.rotation"), bg=bg_color_highlight),
                ui.slider(
                    0,
                    360,
                    self.config.rotation_angle,
                    on_change=self.on_rotation_changed,
                    tooltip=s("camera.rotationTooltip"),
                ),
                self.rotation_value,
            )
        )
        # Calibration is controlled by the checkbox only (continuous auto-calibration).
        self.use_calibration_checkbox = ui.checkbox(
            f'{s("camera.enableCalibration")}:',
            self.settings_config.use_calibration,
            on_change=self.on_use_calibration_changed,
            tooltip=s("camera.enableCalibrationTooltip"),
        )
        self.tracking_layout.add_widget(ui.row(self.use_calibration_checkbox))

        self.mode_readout = ui.label(s("camera.calibrating"), bg=ui.BUTTON_COLOR)
        self.tracking_fps = ui.label("")
        self.tracking_bps = ui.label("")
        self.tracking_layout.add_widget(
            ui.row(
                ui.label(f'{s("camera.mode")}:'),
                self.mode_readout,
                self.tracking_fps,
                self.tracking_bps,
            )
        )
        self.tracking_layout.add_widget(
            ui.row(
                ui.checkbox(
                    f'{s("camera.verticalFlip")}:',
                    self.config.gui_vertical_flip,
                    on_change=self.on_vertical_flip_changed,
                    tooltip=f'{s("camera.verticalFlipTooltip")}.',
                ),
                ui.checkbox(
                    f'{s("camera.horizontalFlip")}:',
                    self.config.gui_horizontal_flip,
                    on_change=self.on_horizontal_flip_changed,
                    tooltip=f'{s("camera.horizontalFlipTooltip")}:',
                ),
            )
        )
        self.roi_message = ui.wrapping_label(f'{s("camera.crop")}:')
        self.roi_message_holder = BoxLayout(size_hint_y=None, height=0)
        self.tracking_layout.add_widget(self.roi_message_holder)
        self.tracking_image = ui.FrameView()
        self.tracking_image_holder = BoxLayout()
        self.tracking_image_holder.add_widget(self.tracking_image)
        self.tracking_layout.add_widget(self.tracking_image_holder)

        # --- Page ---
        self.widget_layout = ui.Panel(bg=bg_color_highlight)
        self.camera_addr = ui.ComboInput(
            self.camera_list,
            self.config.capture_source,
            tooltip=s("camera.cameraAddressTooltip"),
        )
        self.widget_layout.add_widget(
            ui.row(
                ui.label(s("camera.cameraAddress")),
                self.camera_addr,
                ui.button(s("camera.refreshCameraList"), on_press=self.on_refresh_camera_list),
            )
        )
        self.widget_layout.add_widget(
            ui.row(ui.button(s("camera.saveAndRestartTracking"), on_press=self.on_save_and_restart))
        )
        self.widget_layout.add_widget(
            ui.row(
                ui.button(
                    s("camera.trackingMode"),
                    on_press=self.on_tracking_mode,
                    tooltip=f'{s("camera.trackingModeTooltip")}.',
                ),
                ui.button(
                    s("camera.croppingMode"),
                    on_press=self.on_roi_mode,
                    tooltip=f'{s("camera.croppingModeToolTip")}.',
                ),
            )
        )
        # Holds either the tracking view or the cropping view; fills the remaining height.
        self.body = BoxLayout()
        self.body.add_widget(self.tracking_layout)
        self.widget_layout.add_widget(self.body)

    def _set_roi_message_visible(self, visible):
        if visible and self.roi_message.parent is None:
            self.roi_message_holder.add_widget(self.roi_message)
            self.roi_message_holder.height = ui.ROW_HEIGHT
        elif not visible and self.roi_message.parent is not None:
            self.roi_message_holder.remove_widget(self.roi_message)
            self.roi_message_holder.height = 0

    def _set_body(self, widget):
        if widget is None:
            self.body.clear_widgets()
        elif widget.parent is not self.body:
            self.body.clear_widgets()
            self.body.add_widget(widget)

    # ------------------------------------------------------------------------------------------
    # Event handlers (previously dispatched from the FreeSimpleGUI event loop)
    # ------------------------------------------------------------------------------------------
    def on_save_and_restart(self):
        value = self.camera_addr.text
        if value == self.config.capture_source or value == str(self.config.capture_source):
            return
        print(
            f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.newValue")}: {value}\033[0m'
        )
        try:
            self.config.use_ffmpeg = False
            # Try storing ints as ints, for those using wired cameras.
            ports = ("COM", "/dev/ttyACM")
            if any(x in str(value) for x in ports):
                self.config.capture_source = value
            else:
                if is_valid_int_input(value):
                    self.config.capture_source = int(value)
                else:
                    self.config.capture_source = value
        except ValueError:
            if value == "":
                self.config.capture_source = None
            else:
                # If http is not in camera address, add it.
                self.config.capture_source = value

                if "udp" in value:
                    self.config.use_ffmpeg = True
                elif (
                    "http" not in value
                    and ".mp4" not in value
                    and "udp" not in value
                    and "COM" not in value
                    and "/dev/ttyACM" not in value
                    and value not in self.camera_list
                ):  # If http is not in camera address, add it.
                    self.config.capture_source = f"http://{value}/"
        self.main_config.save()

    def on_rotation_changed(self, value):
        value = int(value)
        self.rotation_value.text = str(value)
        if self.config.rotation_angle != value:
            self.config.rotation_angle = value
            self.main_config.save()

    def on_vertical_flip_changed(self, value):
        self.config.gui_vertical_flip = bool(value)
        self.main_config.save()

    def on_horizontal_flip_changed(self, value):
        self.config.gui_horizontal_flip = bool(value)
        self.main_config.save()

    def on_use_calibration_changed(self, value):
        self.settings_config.use_calibration = bool(value)
        self.main_config.save()
        if value:
            print(f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.enabled")}')
            playSound(os.path.join("Audio", "start.wav"))
        else:
            print(f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.disabled")}')
            # Stop calibration if it was running
            if self.babble_cnn.calibration_frame_counter is not None:
                self.babble_cnn.calibration_frame_counter = None

    def on_tracking_mode(self):
        print(
            f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.moveToTrackingMode")}\033[0m'
        )
        self.in_roi_mode = False
        self.camera.set_output_queue(self.capture_queue)
        self._set_body(self.tracking_layout)

    def on_roi_mode(self):
        print(
            f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.moveToROIMode")}\033[0m'
        )
        self.in_roi_mode = True
        self.camera.set_output_queue(self.roi_queue)
        self._set_body(self.roi_layout)

    def on_roi_selected(self, x, y, w, h):
        self.config.roi_window_x = int(x)
        self.config.roi_window_y = int(y)
        self.config.roi_window_w = int(w)
        self.config.roi_window_h = int(h)
        self.main_config.save()

    def on_select_entire_frame(self):
        print(lang._instance.get_string("info.setROI"))
        if self.maybe_image is None:
            return
        output = self.maybe_image[0].shape
        self.config.roi_window_x = 0
        self.config.roi_window_y = 0
        self.config.roi_window_w = output[1]
        self.config.roi_window_h = output[0]
        self.roi_selector.start = (0, 0)
        self.roi_selector.end = (output[1], output[0])
        self.main_config.save()

    def on_refresh_camera_list(self):
        print(
            f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("info.refreshedCameraList")}\033[0m'
        )
        self.camera_list = list_camera_names()
        self.camera_addr.values = self.camera_list

    def clear_calibration(self):
        """Discard the auto-calibrator's learned ranges (used by the Algorithm page's button)."""
        from osc_calibrate_filter import cal

        # Swap in a fresh calibrator rather than mutating the one the processor thread may be
        # using right now; attribute assignment is atomic, so the thread sees old or new, never None.
        self.babble_cnn._calibrator = cal(self.settings_config)
        print(f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("algorithm.clearCalibration")}\033[0m')

    # ------------------------------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------------------------------
    def _movavg_fps(self, next_fps):
        # next_fps is already averaged
        return f"{round(next_fps)} FPS {round((1 / next_fps if next_fps else 0) * 1000)} ms"

    def _movavg_bps(self, next_bps):
        self.bps = round(0.02 * next_bps + 0.98 * self.bps)
        return f"{self.bps * 0.001 * 0.001 * 8:.3f} Mbps"

    def started(self):
        return not self.cancellation_event.is_set()

    def start(self):
        # If we're already running, bail
        if not self.cancellation_event.is_set():
            return
        self.cancellation_event.clear()
        self.babble_cnn_thread = Thread(target=self.babble_cnn.run, name="BabbleProcessorThread")
        self.babble_cnn_thread.start()
        self.camera_thread = Thread(target=self.camera.run, name="CameraThread")
        self.camera_thread.start()

    def stop(self):
        # If we're not running yet, bail
        if self.cancellation_event.is_set():
            return
        self.cancellation_event.set()
        self.babble_cnn_thread.join()
        self.camera_thread.join()

    def render(self):
        """Called periodically on the UI thread to refresh status text and camera previews."""
        if self.image_queue.qsize() > 2:
            with self.image_queue.mutex:
                self.image_queue.queue.clear()

        s = lang._instance.get_string
        needs_roi_set = self.config.roi_window_h <= 0 or self.config.roi_window_w <= 0

        fps_text = ""
        bps_text = ""
        if self.config.capture_source is None or self.config.capture_source == "":
            mode = s("camera.waiting")
            self._set_roi_message_visible(False)
        elif self.camera.camera_status == CameraState.CONNECTING:
            mode = s("camera.connecting")
        elif self.camera.camera_status == CameraState.DISCONNECTED:
            mode = s("camera.reconnecting")
        elif needs_roi_set:
            mode = s("camera.waitingOnMouthCrop")
        elif self.babble_cnn.calibration_frame_counter != None:
            mode = s("camera.calibration")
        else:
            mode = s("camera.tracking")
            fps_text = self._movavg_fps(self.camera.fps)
            bps_text = self._movavg_bps(self.camera.bps)
        if self.mode_readout.text != mode:
            self.mode_readout.text = mode
        self.tracking_fps.text = fps_text
        self.tracking_bps.text = bps_text

        if self.settings_config.gui_disable_camera_preview:
            # We are hiding the previews and crop feed.
            if self.in_roi_mode:
                self.in_roi_mode = False
                self.camera.set_output_queue(self.capture_queue)
            self._set_body(None)
            return
        if self.body.children == [] :
            self._set_body(self.tracking_layout)

        if self.in_roi_mode:
            try:
                if self.roi_queue.empty():
                    self.capture_event.set()
                maybe_image = self.roi_queue.get(block=False)
                self.maybe_image = maybe_image
                self.roi_selector.show_frame(maybe_image[0])
            except Empty:
                pass
            return

        if needs_roi_set:
            self._set_roi_message_visible(True)
            return
        try:
            self._set_roi_message_visible(False)
            (maybe_image, cam_info) = self.image_queue.get(block=False)
            self.tracking_image.show_frame(maybe_image)
        except Empty:
            pass
