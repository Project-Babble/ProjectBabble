import PySimpleGUI as sg

from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event

class AlgoSettingsWidget:
    def __init__(self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue):


        self.gui_general_settings_layout = f"-GENERALSETTINGSLAYOUT{widget_id}-"
        self.gui_multiply = f"-MULTIPLY{widget_id}-"
        self.gui_model_file = f"-MODLEFILE{widget_id}-"
        self.gui_use_gpu = f"USEGPU{widget_id}"
        self.main_config = main_config
        self.config = main_config.settings
        self.osc_queue = osc_queue

        # Define the window's contents
        self.general_settings_layout = [

            [sg.Text("Model output multiplier:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_multiply,
                    key=self.gui_multiply,
                    size=(0,8),
                    tooltip = "Model output modifier.",
                ),
             ],
            [sg.Text("Model file:", background_color='#424042'),
             sg.InputText(
                 self.config.gui_model_file,
                 key=self.gui_model_file,
                 size=(0, 8),
                 tooltip="Name of the model file.",
             ),
             ],
            [sg.Checkbox(
                "Use GPU (DirectML)",
                default=self.config.gui_use_gpu,
                key=self.gui_use_gpu,
                background_color='#424042',
                tooltip="Toggle GPU execution.",
            ),
            ],

        ]

        
        self.widget_layout = [
            [   
                sg.Text("Tracking Algorithm Settings:", background_color='#242224'),
            ],
            [
                sg.Column(self.general_settings_layout, key=self.gui_general_settings_layout, background_color='#424042' ),
            ],
        ]

        self.cancellation_event = Event() # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue()


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

    def render(self, window, event, values):
        # If anything has changed in our configuration settings, change/update those.
        changed = False

        if self.config.gui_multiply != int(values[self.gui_multiply]):
            self.config.gui_multiply = int(values[self.gui_multiply])
            changed = True

        if self.config.gui_model_file != values[self.gui_model_file]:
            self.config.gui_model_file = values[self.gui_model_file]
            changed = True

        if self.config.gui_use_gpu != values[self.gui_use_gpu]:
            self.config.gui_use_gpu = values[self.gui_use_gpu]
            changed = True

        if changed:
            self.main_config.save()
            #print(self.main_config)
        self.osc_queue.put(Tab.ALGOSETTINGS)
