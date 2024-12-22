import PySimpleGUI as sg

from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
import numpy as np
from calib_settings_values import set_shapes
from utils.misc_utils import bg_color_highlight, bg_color_clear, is_valid_float_input
from lang_manager import LocaleStringManager as lang


class CalibSettingsWidget:
    def __init__(
        self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue
    ):
        self.gui_general_settings_layout = f"-GENERALSETTINGSLAYOUT{widget_id}-"
        self.gui_reset_min = f"-RESETMIN{widget_id}-"
        self.gui_reset_max = f"-RESETMAX{widget_id}-"
        self.gui_multiply = f"-MULTIPLY{widget_id}-"
        self.gui_calibration_mode = f"-CALIBRATIONMODE{widget_id}-"
        self.main_config = main_config
        self.config = main_config.settings
        self.array = np.fromstring(
            self.config.calib_array.replace("[", "").replace("]", ""), sep=","
        ).reshape(2, 45)
        self.calibration_list = ["Neutral", "Full"]
        self.osc_queue = osc_queue
        self.shape_index, self.shape = set_shapes(widget_id)
        self.refreshed = False

        # Define the window's contents
        s = self.single_shape
        d = self.double_shape
        self.general_settings_layout = [
            d("cheekPuff"),
            d("cheekSuck"),
            s("jawOpen"),
            s("jawForward"),
            d("jaw"),
            d("noseSneer"),
            s("mouthFunnel"),
            s("mouthPucker"),
            d("mouth"),
            s("mouthRollUpper"),
            s("mouthRollLower"),
            s("mouthShrugUpper"),
            s("mouthShrugLower"),
            s("mouthClose"),
            d("mouthSmile"),
            d("mouthFrown"),
            d("mouthDimple"),
            d("mouthUpperUp"),
            d("mouthLowerDown"),
            d("mouthPress"),
            d("mouthStretch"),
            s("tongueOut"),
            s("tongueUp"),
            s("tongueDown"),
            d("tongue"),
            s("tongueRoll"),
            s("tongueBendDown"),
            s("tongueCurlUp"),
            s("tongueSquish"),
            s("tongueFlat"),
            d("tongueTwist"),
        ]

        self.widget_layout = [
            [
                sg.Text(
                    f'{lang._instance.get_string("calibration.header")}:',
                    background_color=bg_color_clear,
                ),
                sg.Text(
                    f'{lang._instance.get_string("calibration.mode")}:',
                    background_color=bg_color_highlight,
                ),
                sg.OptionMenu(
                    self.calibration_list,
                    self.config.calibration_mode,
                    key=self.gui_calibration_mode,
                    tooltip=f'{lang._instance.get_string("calibration.modeTooltip")}',
                ),
            ],
            [
                sg.Text(
                    lang._instance.get_string("calibration.left"),
                    expand_x=True,
                    justification="left",
                ),
                sg.Text(
                    lang._instance.get_string("calibration.shape"),
                    expand_x=True,
                    justification="center",
                ),
                sg.Text(
                    lang._instance.get_string("calibration.right"),
                    expand_x=True,
                    justification="right",
                ),
            ],
            [
                sg.Text(
                    lang._instance.get_string("calibration.min"),
                    expand_x=True,
                    justification="center",
                ),
                sg.Text(
                    lang._instance.get_string("calibration.max"),
                    expand_x=True,
                    justification="center",
                ),
                sg.HSeparator(pad=(50, 0)),
                sg.Text(
                    lang._instance.get_string("calibration.max"),
                    expand_x=True,
                    justification="center",
                ),
                sg.Text(
                    lang._instance.get_string("calibration.min"),
                    expand_x=True,
                    justification="center",
                ),
            ],
            [
                sg.Column(
                    self.general_settings_layout,
                    key=self.gui_general_settings_layout,
                    scrollable=True,
                    vertical_scroll_only=True,
                    element_justification="center",
                    background_color=bg_color_highlight,
                ),
            ],
            [
                sg.Button(
                    lang._instance.get_string("calibration.resetMin"),
                    key=self.gui_reset_min,
                    button_color="#FF0000",
                    tooltip=lang._instance.get_string("calibration.resetMinTooltip"),
                ),
                sg.Button(
                    lang._instance.get_string("calibration.resetMax"),
                    key=self.gui_reset_max,
                    button_color="#FF0000",
                    tooltip=lang._instance.get_string("calibration.resetMaxTooltip"),
                ),
            ],
        ]

        self.cancellation_event = (
            Event()
        )  # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue(maxsize=2)

    def double_shape(self, shapename):
        indexl = self.shape_index.index(f"{shapename}Left")
        indexr = self.shape_index.index(f"{shapename}Right")
        double_shape = [
            sg.InputText(
                default_text=self.array[0][indexl],
                key=self.shape[0][indexl],
                size=(8),
                tooltip=lang._instance.get_string("calibration.minLeftValue"),
                enable_events=True,
            ),
            sg.InputText(
                default_text=self.array[1][indexl],
                key=self.shape[1][indexl],
                size=(8),
                tooltip=lang._instance.get_string("calibration.maxLeftValue"),
                enable_events=True,
            ),
            sg.Text(
                f"{shapename}Left/Right",
                background_color=bg_color_highlight,
                expand_x=True,
            ),
            sg.InputText(
                default_text=self.array[1][indexr],
                key=self.shape[1][indexr],
                size=(8),
                tooltip=lang._instance.get_string("calibration.maxRightValue"),
                enable_events=True,
            ),
            sg.InputText(
                default_text=self.array[0][indexr],
                key=self.shape[0][indexr],
                size=(8),
                tooltip=lang._instance.get_string("calibration.minRightValue"),
                enable_events=True,
            ),
        ]
        return double_shape

    def single_shape(self, shapename):
        index = self.shape_index.index(f"{shapename}")
        single_shape = [
            sg.InputText(
                default_text=self.array[0][index],
                key=self.shape[0][index],
                size=(8),
                tooltip=lang._instance.get_string("calibration.minLeftValue"),
                enable_events=True,
            ),
            sg.InputText(
                default_text=self.array[1][index],
                key=self.shape[1][index],
                size=(8),
                tooltip=lang._instance.get_string("calibration.maxLeftValue"),
                enable_events=True,
            ),
            sg.Text(f"{shapename}", background_color=bg_color_highlight, expand_x=True),
        ]
        return single_shape

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

    def render(self, window, event, values):
        # If anything has changed in our configuration settings, change/update those.
        changed = False
        if not self.refreshed:
            for count1, element1 in enumerate(self.shape):
                for count2, element2 in enumerate(element1):
                    window[element2].update(float(self.array[count1][count2]))
                    # values[element2] = float(self.array[count1][count2])
                    self.refreshed = True

        if self.config.calibration_mode != str(values[self.gui_calibration_mode]):
            self.config.calibration_mode = str(values[self.gui_calibration_mode])
            changed = True

        for count1, element1 in enumerate(self.shape):
            for count2, element2 in enumerate(element1):
                if values[element2] != "":   
                    value = values[element2]
                    if is_valid_float_input(value): # Returns true if a single decimal point. Therefore we need to make sure value can be converted to a float by assuming a dot implies a leading 0.
                        if value == ".":
                            valid_float = 0.
                            values[element2] = valid_float
                            window[element2].update(valid_float)
                        value = float(values[element2])
                        if float(self.array[count1][count2]) != value:
                            self.array[count1][count2] = value
                            changed = True
                    else:
                        trimmed_value = value[:-1]
                        if trimmed_value == '':     # If we get an empty string, don't try to convert to float. 
                            window[element2].update(trimmed_value)
                            values[element2] = trimmed_value
                        else: 
                            value = float(trimmed_value)
                            window[element2].update(value)
                            values[element2] = value

        if event == self.gui_reset_min:
            for count1, element1 in enumerate(self.shape):
                for count2, element2 in enumerate(element1):
                    self.array[0][count2] = float(0)
                    changed = True
                    self.refreshed = False
                    
        elif event == self.gui_reset_max:
            for count1, element1 in enumerate(self.shape):
                for count2, element2 in enumerate(element1):
                    self.array[1][count2] = float(1)
                    changed = True
                    self.refreshed = False

        if changed:
            self.config.calib_array = np.array2string(self.array, separator=",")
            self.main_config.save()
            # print(self.main_config)
        self.osc_queue.put(Tab.CALIBRATION)
