import PySimpleGUI as sg

from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
import numpy as np
from calib_settings_values import set_shapes
from utils import misc_utils


class CalibSettingsWidget:
    def __init__(self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue):


        self.gui_general_settings_layout = f"-GENERALSETTINGSLAYOUT{widget_id}-"
        self.gui_reset_min = f"-RESETMIN{widget_id}-"
        self.gui_reset_max = f"-RESETMAX{widget_id}-"
        self.gui_multiply = f"-MULTIPLY{widget_id}-"
        self.gui_calibration_mode = f"-CALIBRATIONMODE{widget_id}-"
        self.main_config = main_config
        self.config = main_config.settings
        self.array = np.fromstring(self.config.calib_array.replace('[', '').replace(']', ''), sep=',').reshape(2, 45)
        self.calibration_list = ['Neutral', 'Full']
        self.osc_queue = osc_queue
        self.shape_index, self.shape = set_shapes(widget_id)
        self.refreshed = False

        

        # Define the window's contents
        s = self.single_shape
        d = self.double_shape
        self.general_settings_layout = [

            d('cheekPuff'),
            d('cheekSuck'),
            s('jawOpen'),
            s('jawForward'),
            d('jaw'),
            d('noseSneer'),
            s('mouthFunnel'),
            s('mouthPucker'),
            d('mouth'),
            s('mouthRollUpper'),
            s('mouthRollLower'),
            s('mouthShrugUpper'),
            s('mouthShrugLower'),
            s('mouthClose'),
            d('mouthSmile'),
            d('mouthFrown'),
            d('mouthDimple'),
            d('mouthUpperUp'),
            d('mouthLowerDown'),
            d('mouthPress'),
            d('mouthStretch'),
            s('tongueOut'),
            s('tongueUp'),
            s('tongueDown'),
            d('tongue'),
            s('tongueRoll'),
            s('tongueBendDown'),
            s('tongueCurlUp'),
            s('tongueSquish'),
            s('tongueFlat'),
            d('tongueTwist'),

            
        ]

        self.widget_layout = [
            [   
                sg.Text("Calibration Settings:", background_color='#242224'),
                sg.Text("Calibration Mode:", background_color='#424042'), 
                sg.OptionMenu(
                    self.calibration_list,
                    self.config.calibration_mode,
                    key=self.gui_calibration_mode,
                    tooltip='Neutral = Only Min values are set when starting and stopping calibration. Full = Min and Max values are set based on recorded values when starting calibration.',
                ),
            ],
            [
                sg.Text("Left  ", expand_x=True, justification='left'),
                sg.Text("Shape", expand_x=True, justification='center'),
                sg.Text("Right", expand_x=True, justification='right')
            ],
            [
                sg.Text("Min", expand_x=True, justification='center'),
                sg.Text("Max", expand_x=True, justification='center'),
                sg.HSeparator(pad=(50,0)),
                sg.Text("Max", expand_x=True, justification='center'),
                sg.Text("Min", expand_x=True, justification='center'),
            ],
            [
                sg.Column(
                    self.general_settings_layout, 
                    key=self.gui_general_settings_layout, 
                    scrollable=True, 
                    vertical_scroll_only=True,
                    element_justification='center',
                    background_color='#424042' ),
            ],
            [
                sg.Button("Reset Min", key=self.gui_reset_min, button_color='#FF0000', tooltip = "Reset minimum values",),
                sg.Button("Reset Max", key=self.gui_reset_max, button_color='#FF0000', tooltip = "Reset maximum values",),
            ],
        ]

        self.cancellation_event = Event() # Set the event until start is called, otherwise we can block if shutdown is called.
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
                tooltip="Min Left Value",
            ),
            sg.InputText(
                default_text=self.array[1][indexl],
                key=self.shape[1][indexl],
                size=(8),
                tooltip="Max Left Value",
            ),
            sg.Text(f"{shapename}Left/Right", background_color='#424042', expand_x=True),
            sg.InputText(
                default_text=self.array[1][indexr],
                key=self.shape[1][indexr],
                size=(8),
                tooltip="Max Right Value",
                ),
            sg.InputText(
                default_text=self.array[0][indexr],
                key=self.shape[0][indexr],
                size=(8),
                tooltip="Min Right Value",
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
                tooltip="Min Left Value",
            ),
            sg.InputText(
                default_text=self.array[1][index],
                key=self.shape[1][index],
                size=(8),
                tooltip="Max Left Value",
            ),
            sg.Text(f"{shapename}", background_color='#424042', expand_x=True),
        ]
        return single_shape

    def started(self):
        return not self.cancellation_event.is_set()

    def start(self):
        # If we're already running, bail
        if not self.cancellation_event.is_set():
            return
        self.cancellation_event.clear()
        self.array = np.fromstring(self.config.calib_array.replace('[', '').replace(']', ''), sep=',').reshape(2, 45)   # Reload the array from the config
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
                    #values[element2] = float(self.array[count1][count2])
                    self.refreshed = True
            print('DEBUG: Refreshed')

        if self.config.calibration_mode != str(values[self.gui_calibration_mode]):
            self.config.calibration_mode = str(values[self.gui_calibration_mode])
            changed = True
        
        for count1, element1 in enumerate(self.shape):
            for count2, element2 in enumerate(element1):
                value = values[element2]
                if not misc_utils.is_valid_float_input(value):
                    value = value[:-1]
                    window[element2].update(value)
                    values[element2] = value
                    
                if values[element2] != '':
                    if float(self.array[count1][count2]) != float(value):
                        self.array[count1][count2] = float(value)
                        changed = True
        
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
            self.config.calib_array = np.array2string(self.array, separator=',')
            self.main_config.save()
            #print(self.main_config)
        self.osc_queue.put(Tab.CALIBRATION)
