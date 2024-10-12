import PySimpleGUI as sg

from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
from utils import misc_utils


class AlgoSettingsWidget:
    def __init__(self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue):

        self.gui_general_settings_layout = f"-GENERALSETTINGSLAYOUT{widget_id}-"
        self.gui_multiply = f"-MULTIPLY{widget_id}-"
        self.gui_model_file = f"-MODLEFILE{widget_id}-"
        self.gui_use_gpu = f"USEGPU{widget_id}"
        self.gui_speed_coefficient = f"-SPEEDCOEFFICIENT{widget_id}-"
        self.gui_min_cutoff = f"-MINCUTOFF{widget_id}-"
        self.gui_inference_threads = f"-THREADS{widget_id}-"
        self.gui_runtime = f"-RUNTIME{widget_id}"
        self.gui_gpu_index = f"GPUINDEX{widget_id}"
        self.calib_deadzone = f"CALIBDEADZONE{widget_id}"
        self.main_config = main_config
        self.config = main_config.settings
        self.osc_queue = osc_queue
        self.runtime_list = ("Default (ONNX)", "ONNX")

        # Define the window's contents
        self.general_settings_layout = [

            [sg.Text("Model file:", background_color='#424042'),
             sg.InputText(
                 self.config.gui_model_file,
                 key=self.gui_model_file,
                 size=(32),
                 tooltip="Name of the model file.",
             ),
             sg.Text("Inference Threads:", background_color='#424042'),
             sg.InputText(
                 self.config.gui_inference_threads,
                 key=self.gui_inference_threads,
                 size=(4),
                 tooltip="How many threads to use for processing the model.",
                 enable_events=True,
             ),
             ],
            [sg.Text("Runtime:", background_color='#424042'),
             sg.OptionMenu(
                 self.runtime_list,
                 self.config.gui_runtime,
                 key=self.gui_runtime,
             ),
             sg.Text("GPU Index:", background_color='#424042'),
             sg.InputText(
                 self.config.gui_gpu_index,
                 key=self.gui_gpu_index,
                 size=(4),
                 tooltip="Select which device to run inference.",
                 enable_events=True,
             ),
             sg.Checkbox(
                 "Use GPU",
                 default=self.config.gui_use_gpu,
                 key=self.gui_use_gpu,
                 background_color='#424042',
                 tooltip="Toggle GPU execution.",
             ),
             ],
            [sg.Text("Model output multiplier:", background_color='#424042'),
             sg.InputText(
                 self.config.gui_multiply,
                 key=self.gui_multiply,
                 size=(4),
                 tooltip="Model output modifier.",
                 enable_events=True,
             ),
             ],
            [sg.Text("Calibration Deadzone:", background_color='#424042'),
             sg.InputText(
                 self.config.calib_deadzone,
                 key=self.calib_deadzone,
                 size=(4),
                 tooltip="Offset the minimum calibrated values.",
                 enable_events=True,
             ),
             ],
            [
                sg.Text("One Euro Filter Parameters:", background_color='#242224'),
            ],
            [

                sg.Text("Min Frequency Cutoff", background_color='#424042'),
                sg.InputText(
                    self.config.gui_min_cutoff,
                    key=self.gui_min_cutoff,
                    size=(7),
                    enable_events=True,
                ),
                sg.Text("Speed Coefficient", background_color='#424042'),
                sg.InputText(
                    self.config.gui_speed_coefficient,
                    key=self.gui_speed_coefficient,
                    size=(5),
                    enable_events=True,
                ),
            ],

        ]

        self.widget_layout = [
            [
                sg.Text("Model Settings:", background_color='#242224'),
            ],
            [
                sg.Column(self.general_settings_layout, key=self.gui_general_settings_layout, background_color='#424042'),
            ],
        ]

        self.cancellation_event = Event()  # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue(maxsize=2)

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
        # Input validation for the fields
        if event == self.gui_multiply:
            value = values[self.gui_multiply]
            if not misc_utils.is_valid_float_input(value):
                # Invalid input, remove last character
                value = value[:-1]
                window[self.gui_multiply].update(value)
                values[self.gui_multiply] = value

        elif event == self.calib_deadzone:
            value = values[self.calib_deadzone]
            if not misc_utils.is_valid_float_input(value):
                value = value[:-1]
                window[self.calib_deadzone].update(value)
                values[self.calib_deadzone] = value

        elif event == self.gui_inference_threads:
            value = values[self.gui_inference_threads]
            if not misc_utils.is_valid_int_input(value):
                value = value[:-1]
                window[self.gui_inference_threads].update(value)
                values[self.gui_inference_threads] = value

        elif event == self.gui_gpu_index:
            value = values[self.gui_gpu_index]
            if not misc_utils.is_valid_int_input(value):
                value = value[:-1]
                window[self.gui_gpu_index].update(value)
                values[self.gui_gpu_index] = value

        elif event == self.gui_min_cutoff:
            value = values[self.gui_min_cutoff]
            if not misc_utils.is_valid_float_input(value):
                value = value[:-1]
                window[self.gui_min_cutoff].update(value)
                values[self.gui_min_cutoff] = value

        elif event == self.gui_speed_coefficient:
            value = values[self.gui_speed_coefficient]
            if not misc_utils.is_valid_float_input(value):
                value = value[:-1]
                window[self.gui_speed_coefficient].update(value)
                values[self.gui_speed_coefficient] = value

        changed = False

        try:
            if values[self.gui_multiply] != '':
                if self.config.gui_multiply != float(values[self.gui_multiply]):
                    self.config.gui_multiply = float(values[self.gui_multiply])
                    changed = True
        except ValueError:
            pass  # Ignore invalid float conversion


        if self.config.gui_model_file != values[self.gui_model_file]:
            self.config.gui_model_file = values[self.gui_model_file]
            changed = True

        try:
            if values[self.calib_deadzone] != '':
                if self.config.calib_deadzone != float(values[self.calib_deadzone]):
                    self.config.calib_deadzone = float(values[self.calib_deadzone])
                    changed = True
        except ValueError:
            pass  # Ignore invalid float conversion


        if self.config.gui_use_gpu != values[self.gui_use_gpu]:
            self.config.gui_use_gpu = values[self.gui_use_gpu]
            changed = True

        try:
            if values[self.gui_gpu_index] != '':
                if self.config.gui_gpu_index != int(values[self.gui_gpu_index]):
                    self.config.gui_gpu_index = int(values[self.gui_gpu_index])
                    changed = True
        except ValueError:
            pass  # Ignore invalid int conversion


        if self.config.gui_runtime != str(values[self.gui_runtime]):
            self.config.gui_runtime = str(values[self.gui_runtime])
            changed = True

        try:
            if values[self.gui_inference_threads] != '':
                if self.config.gui_inference_threads != int(values[self.gui_inference_threads]):
                    self.config.gui_inference_threads = int(values[self.gui_inference_threads])
                    changed = True
        except ValueError:
            pass  # Ignore invalid int conversion

        if values[self.gui_min_cutoff] != '':
            if self.config.gui_min_cutoff != values[self.gui_min_cutoff]:
                self.config.gui_min_cutoff = values[self.gui_min_cutoff]
                changed = True

        if values[self.gui_speed_coefficient] != '':
            if self.config.gui_speed_coefficient != values[self.gui_speed_coefficient]:
                self.config.gui_speed_coefficient = values[self.gui_speed_coefficient]
                changed = True

        if changed:
            self.main_config.save()
        self.osc_queue.put(Tab.ALGOSETTINGS)
