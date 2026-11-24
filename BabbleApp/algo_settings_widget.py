import kivy_ui as ui  # Must be imported before any other Kivy module
from kivy.uix.scrollview import ScrollView

from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
from utils.misc_utils import bg_color_highlight, bg_color_clear, is_valid_float_input, is_valid_int_input
from lang_manager import LocaleStringManager as lang


def _is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class AlgoSettingsWidget:
    def __init__(
        self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue
    ):
        self.main_config = main_config
        self.main_config.settings.widget_id = widget_id
        self.config = main_config.settings
        self.osc_queue = osc_queue
        self.runtime_list = ("Default (ONNX)", "ONNX")

        s = lang._instance.get_string
        c = self.config

        # Define the window's contents
        panel = ui.Panel(bg=bg_color_highlight, auto_height=True)
        self.model_file = ui.text_input(
            c.gui_model_file,
            on_change=self._setter("gui_model_file", str),
            chars=32,
            tooltip=f'{s("algorithm.modelFileTooptip")}.',
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("algorithm.modelFile")}:'),
                self.model_file,
                ui.button("Browse", on_press=self.on_browse_model),
                ui.label(f'{s("algorithm.inferenceThreads")}:'),
                ui.text_input(
                    c.gui_inference_threads,
                    on_change=self._setter("gui_inference_threads", int, _is_number),
                    chars=4,
                    validator=is_valid_int_input,
                    tooltip=f'{s("algorithm.inferenceThreadsTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("algorithm.runtime")}:'),
                ui.spinner(
                    self.runtime_list,
                    c.gui_runtime,
                    on_change=self._setter("gui_runtime", str),
                ),
                ui.label(f'{s("algorithm.GPUIndex")}:'),
                ui.text_input(
                    c.gui_gpu_index,
                    on_change=self._setter("gui_gpu_index", int, _is_number),
                    chars=4,
                    validator=is_valid_int_input,
                    tooltip=f'{s("algorithm.GPUIndexTooltip")}.',
                ),
                ui.checkbox(
                    s("algorithm.useGPU"),
                    c.gui_use_gpu,
                    on_change=self._setter("gui_use_gpu", bool),
                    tooltip=f'{s("algorithm.useGPUTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("algorithm.modelOutputMultiplier")}:'),
                ui.text_input(
                    c.gui_multiply,
                    on_change=self._setter("gui_multiply", float, _is_number),
                    chars=5,
                    validator=is_valid_float_input,
                    tooltip=f'{s("algorithm.modelOutputMultiplierTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("algorithm.calibrationDeadzone")}:'),
                ui.text_input(
                    c.calib_deadzone,
                    on_change=self._setter("calib_deadzone", float, _is_number),
                    chars=5,
                    validator=is_valid_float_input,
                    tooltip=f'{s("algorithm.calibrationDeadzoneTooltip")}.',
                ),
            )
        )
        panel.add_widget(ui.section_header(f'{s("algorithm.oneEuroFilterParameters")}:'))
        panel.add_widget(
            ui.row(
                ui.label(s("algorithm.minFrequencyCutoff")),
                ui.text_input(
                    c.gui_min_cutoff,
                    # Stored as a string in the config; empty input is ignored.
                    on_change=self._setter("gui_min_cutoff", str, lambda v: v != ""),
                    chars=7,
                    validator=is_valid_float_input,
                ),
                ui.label(s("algorithm.speedCoefficient")),
                ui.text_input(
                    c.gui_speed_coefficient,
                    on_change=self._setter("gui_speed_coefficient", str, lambda v: v != ""),
                    chars=5,
                    validator=is_valid_float_input,
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.button(
                    s("algorithm.clearCalibration"),
                    on_press=self.on_clear_calibration_pressed,
                    color="#d9534f",
                    tooltip=s("algorithm.clearCalibrationTooltip"),
                )
            )
        )
        # Set by the app to the camera widget's clear_calibration (the calibrator lives there).
        self.on_clear_calibration = None
        self.general_settings_layout = panel

        page = ui.Panel(bg=bg_color_clear, padding=0)
        page.add_widget(ui.section_header(s("algorithm.header")))
        scroll = ScrollView(do_scroll_x=False, bar_width=ui.dp(8), scroll_type=["bars", "content"])
        scroll.add_widget(panel)
        page.add_widget(scroll)
        self.widget_layout = page

        self.cancellation_event = (
            Event()
        )  # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue(maxsize=2)

    def on_clear_calibration_pressed(self):
        if self.on_clear_calibration is not None:
            self.on_clear_calibration()

    def on_browse_model(self):
        ui.choose_folder(self.model_file.text, lambda path: setattr(self.model_file, "text", path))

    def _setter(self, attr, convert, is_complete=None):
        """Build a change handler that converts, stores and saves a setting."""

        def handler(value):
            if is_complete is not None and not is_complete(value):
                return
            try:
                new_value = convert(value)
            except (TypeError, ValueError):
                return
            if getattr(self.config, attr) != new_value:
                setattr(self.config, attr, new_value)
                self.main_config.save()

        return handler

    def started(self):
        return not self.cancellation_event.is_set()

    def start(self):
        # If we're already running, bail
        if not self.cancellation_event.is_set():
            return
        self.cancellation_event.clear()

    def stop(self):
        # If we're not running yet, bail
        if self.cancellation_event.is_set():
            return
        self.cancellation_event.set()

    def render(self):
        # Settings are applied as soon as they are edited (see _setter); nothing to poll.
        pass
