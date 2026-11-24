import kivy_ui as ui  # Must be imported before any other Kivy module
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
import numpy as np
from calib_settings_values import set_shapes
from utils.misc_utils import bg_color_highlight, bg_color_clear, is_valid_float_input
from lang_manager import LocaleStringManager as lang

INPUT_CHARS = 7


class CalibSettingsWidget:
    def __init__(
        self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue
    ):
        self.main_config = main_config
        self.config = main_config.settings
        self.array = np.fromstring(
            self.config.calib_array.replace("[", "").replace("]", ""), sep=","
        ).reshape(2, 45)
        self.calibration_list = ["Neutral", "Full"]
        self.osc_queue = osc_queue
        self.shape_index, self.shape = set_shapes(widget_id)
        self.refreshed = False
        self._suppress_events = False
        self.inputs = {}  # shape key (from calib_settings_values) -> TextInput

        s = lang._instance.get_string

        # Define the window's contents
        self.grid = GridLayout(cols=5, size_hint_y=None, spacing=ui.SPACING, padding=ui.PADDING, row_default_height=ui.ROW_HEIGHT, row_force_default=True)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        ui.paint_background(self.grid, bg_color_highlight)

        sh = self.single_shape
        d = self.double_shape
        for kind, name in [
            (d, "cheekPuff"),
            (d, "cheekSuck"),
            (sh, "jawOpen"),
            (sh, "jawForward"),
            (d, "jaw"),
            (d, "noseSneer"),
            (sh, "mouthFunnel"),
            (sh, "mouthPucker"),
            (d, "mouth"),
            (sh, "mouthRollUpper"),
            (sh, "mouthRollLower"),
            (sh, "mouthShrugUpper"),
            (sh, "mouthShrugLower"),
            (sh, "mouthClose"),
            (d, "mouthSmile"),
            (d, "mouthFrown"),
            (d, "mouthDimple"),
            (d, "mouthUpperUp"),
            (d, "mouthLowerDown"),
            (d, "mouthPress"),
            (d, "mouthStretch"),
            (sh, "tongueOut"),
            (sh, "tongueUp"),
            (sh, "tongueDown"),
            (d, "tongue"),
            (sh, "tongueRoll"),
            (sh, "tongueBendDown"),
            (sh, "tongueCurlUp"),
            (sh, "tongueSquish"),
            (sh, "tongueFlat"),
            (d, "tongueTwist"),
        ]:
            for widget in kind(name):
                self.grid.add_widget(widget)
        self.general_settings_layout = self.grid

        page = ui.Panel(bg=bg_color_clear, padding=0)
        page.add_widget(
            ui.row(
                ui.label(f'{s("calibration.header")}:', bold=True),
                ui.label(f'{s("calibration.mode")}:', bg=bg_color_highlight),
                ui.spinner(
                    self.calibration_list,
                    self.config.calibration_mode,
                    on_change=self.on_calibration_mode_changed,
                    tooltip=f'{s("calibration.modeTooltip")}',
                ),
            )
        )
        # Column headings, aligned with the grid columns below.
        headings = GridLayout(cols=5, size_hint_y=None, height=ui.ROW_HEIGHT * 2, padding=(ui.PADDING, 0), spacing=(ui.SPACING, 0))
        for text, halign in [
            (s("calibration.left"), "left"),
            ("", "left"),
            (s("calibration.shape"), "center"),
            ("", "right"),
            (s("calibration.right"), "right"),
            (s("calibration.min"), "center"),
            (s("calibration.max"), "center"),
            ("", "center"),
            (s("calibration.max"), "center"),
            (s("calibration.min"), "center"),
        ]:
            headings.add_widget(self._heading(text, halign, center=(text == s("calibration.shape"))))
        page.add_widget(headings)

        scroll = ScrollView(do_scroll_x=False, bar_width=ui.dp(8), scroll_type=["bars", "content"])
        scroll.add_widget(self.grid)
        page.add_widget(scroll)
        page.add_widget(
            ui.row(
                ui.button(
                    s("calibration.resetMin"),
                    on_press=self.on_reset_min,
                    color="#FF0000",
                    tooltip=s("calibration.resetMinTooltip"),
                ),
                ui.button(
                    s("calibration.resetMax"),
                    on_press=self.on_reset_max,
                    color="#FF0000",
                    tooltip=s("calibration.resetMaxTooltip"),
                ),
            )
        )
        self.widget_layout = page

        self.cancellation_event = (
            Event()
        )  # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue(maxsize=2)

    def _heading(self, text, halign, center=False):
        if center:
            lbl = ui.wrapping_label(text, halign="center")
            lbl.size_hint = (1, 1)
            return lbl
        lbl = ui.wrapping_label(text, halign="center")
        lbl.size_hint = (None, 1)
        lbl.width = self._input_width()
        return lbl

    @staticmethod
    def _input_width():
        return ui.dp(14 + INPUT_CHARS * 8.5)

    def _make_input(self, row, index, tooltip):
        key = self.shape[row][index]
        ti = ui.text_input(
            self.array[row][index],
            on_change=lambda value, r=row, i=index: self.on_value_changed(r, i, value),
            chars=INPUT_CHARS,
            validator=is_valid_float_input,
            tooltip=lang._instance.get_string(tooltip),
        )
        self.inputs[key] = ti
        return ti

    def _shape_label(self, text):
        lbl = ui.Label(
            text=text,
            size_hint=(1, 1),
            color=ui.rgba(ui.TEXT_COLOR),
            font_size=ui.FONT_SIZE,
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        lbl.bind(size=lambda w, v: setattr(w, "text_size", v))
        return lbl

    def double_shape(self, shapename):
        indexl = self.shape_index.index(f"{shapename}Left")
        indexr = self.shape_index.index(f"{shapename}Right")
        return [
            self._make_input(0, indexl, "calibration.minLeftValue"),
            self._make_input(1, indexl, "calibration.maxLeftValue"),
            self._shape_label(f"{shapename}Left/Right"),
            self._make_input(1, indexr, "calibration.maxRightValue"),
            self._make_input(0, indexr, "calibration.minRightValue"),
        ]

    def single_shape(self, shapename):
        index = self.shape_index.index(f"{shapename}")
        return [
            self._make_input(0, index, "calibration.minLeftValue"),
            self._make_input(1, index, "calibration.maxLeftValue"),
            self._shape_label(f"{shapename}"),
            Widget(size_hint_x=None, width=self._input_width()),
            Widget(size_hint_x=None, width=self._input_width()),
        ]

    # --- Event handlers ---
    def on_calibration_mode_changed(self, value):
        if self.config.calibration_mode != str(value):
            self.config.calibration_mode = str(value)
            self.main_config.save()

    def on_value_changed(self, row, index, value):
        if self._suppress_events:
            return
        try:
            # A lone "." or "-" is valid partial input; treat "." as 0 like before.
            value = 0.0 if value == "." else float(value)
        except ValueError:
            return
        if float(self.array[row][index]) != value:
            self.array[row][index] = value
            self._save()

    def on_reset_min(self):
        self.array[0][:] = 0.0
        self._save()
        self.refreshed = False

    def on_reset_max(self):
        self.array[1][:] = 1.0
        self._save()
        self.refreshed = False

    def _save(self):
        self.config.calib_array = np.array2string(self.array, separator=",")
        self.main_config.save()

    # --- Lifecycle ---
    def started(self):
        return not self.cancellation_event.is_set()

    def start(self):
        # If we're already running, bail
        if not self.cancellation_event.is_set():
            return
        self.cancellation_event.clear()
        self.array = np.fromstring(
            self.config.calib_array.replace("[", "").replace("]", ""), sep=","
        ).reshape(
            2, 45
        )  # Reload the array from the config
        self.refreshed = False

    def stop(self):
        # If we're not running yet, bail
        if self.cancellation_event.is_set():
            return
        self.cancellation_event.set()

    def render(self):
        # Push the (possibly reloaded/reset) calibration values into the text boxes.
        if not self.refreshed:
            for count1, element1 in enumerate(self.shape):
                for count2, element2 in enumerate(element1):
                    ui.set_text_silently(self.inputs[element2], float(self.array[count1][count2]), self)
            self.refreshed = True
