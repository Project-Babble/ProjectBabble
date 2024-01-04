import PySimpleGUI as sg
from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event

class SettingsWidget:
    def __init__(self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue):
        self.gui_general_settings_layout = f"-GENERALSETTINGSLAYOUT{widget_id}-"
        self.gui_osc_address = f"-OSCADDRESS{widget_id}-"
        self.gui_osc_port = f"-OSCPORT{widget_id}-"
        self.gui_osc_receiver_port = f"OSCRECEIVERPORT{widget_id}-"
        self.gui_osc_recalibrate_address = f"OSCRECALIBRATEADDRESS{widget_id}-"
        self.gui_speed_coefficient = f"-SPEEDCOEFFICIENT{widget_id}-"
        self.gui_min_cutoff = f"-MINCUTOFF{widget_id}-"
        self.gui_ROSC = f"-ROSC{widget_id}-"
        self.gui_update_check = f"-UPDATECHECK{widget_id}-"
        self.gui_osc_location = f"-OSCLOCATION{widget_id}-"
        self.gui_cam_resolution_x = f"-CAMRESX{widget_id}-"
        self.gui_cam_resolution_y = f"-CAMRESY{widget_id}-"
        self.gui_cam_framerate = f"-CAMFRAMERATE{widget_id}-"
        self.gui_use_red_channel = f"-REDCHANNEL{widget_id}-"
        self.main_config = main_config
        self.config = main_config.settings
        self.osc_queue = osc_queue

        # Define the window's contents
        self.general_settings_layout = [
           


            [sg.Checkbox(
                    "Check For Updates",
                    default=self.config.gui_update_check,
                    key=self.gui_update_check,
                    background_color='#424042',
                    tooltip = "Toggle update check on launch.",
                ),
            ],

             [
                sg.Text("OSC Settings:", background_color='#242224'),
            ],
            [
                sg.Text("Location Prefix:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_osc_location,
                    key=self.gui_osc_location,
                    size=(30),
                    tooltip="Prefix for OSC address.",
                ),
            ],
            [
                sg.Text("Address:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_osc_address, 
                    key=self.gui_osc_address,
                    size=(0,20),
                    tooltip = "IP address we send OSC data to.",
                ),
                
          #  ],
          #  [
                sg.Text("Port:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_osc_port, 
                    key=self.gui_osc_port,
                    size=(0,10),
                    tooltip = "OSC port we send data to.",
                ),
            ],
            [
                sg.Text("Receive functions", background_color='#424042'),
                sg.Checkbox(
                    "",
                    default=self.config.gui_ROSC,
                    key=self.gui_ROSC,
                    background_color='#424042',
                    size=(0,10),
                    tooltip = "Toggle OSC receive functions.",
                ),
            ],
            [
                sg.Text("Receiver Port:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_osc_receiver_port, 
                    key=self.gui_osc_receiver_port,
                    size=(0,10),
                    tooltip = "Port we receive OSC data from (used to recalibrate from within VRChat.",
                ),
            ],
            [
                sg.Text("Recalibrate Address:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_osc_recalibrate_address, 
                    key=self.gui_osc_recalibrate_address,
                    size=(0,10),
                    tooltip = "OSC address we use for recalibrating.",
                    ),
            ],
            [
                sg.Text("UVC Camera Settings:", background_color='#242224'),
            ],
            [
                sg.Text("Use Red Channel", background_color='#424042'),
                sg.Checkbox(
                    "",
                    default=self.config.gui_use_red_channel,
                    key=self.gui_use_red_channel,
                    background_color='#424042',
                    size=(0,10),
                    tooltip = "Uses only the red channel for Omnicept capture.",
                ),
                
                sg.Text("X Resolution:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_cam_resolution_x, 
                    key=self.gui_cam_resolution_x,
                    size=(0,20),
                    tooltip = "X capture resolution. Default = 0",
                ),
                
          #  ],
          #  [
                sg.Text("Y Resolution:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_cam_resolution_y, 
                    key=self.gui_cam_resolution_y,
                    size=(0,10),
                    tooltip = "Y capture resolution. Default = 0",
                ),
                          
          #  ],
          #  [
                sg.Text("Framerate:", background_color='#424042'),
                sg.InputText(
                    self.config.gui_cam_framerate, 
                    key=self.gui_cam_framerate,
                    size=(0,10),
                    tooltip = "Capture framerate. Default = 0",
                ),
            ],

        ]

        
        self.widget_layout = [
            [   
                sg.Text("General Settings:", background_color='#242224'),
            ],
            [
                sg.Column(self.general_settings_layout, key=self.gui_general_settings_layout, background_color='#424042' ),
            ],
        ]

        self.cancellation_event = Event() # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue(maxsize=1)


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

        try:
            if self.config.gui_osc_port != int(values[self.gui_osc_port]):
                try:
                    int(values[self.gui_osc_port])
                    if len(values[self.gui_osc_port]) <= 5:
                        self.config.gui_osc_port = int(values[self.gui_osc_port])
                        changed = True
                    else:
                        print("\033[91m[ERROR] OSC port value must be an integer 0-65535\033[0m")
                except:
                    print("\033[91m[ERROR] OSC port value must be an integer 0-65535\033[0m")
        except:
            print("\033[91m[ERROR] OSC port value cannot be empty and must be an integer 0-65535\033[0m")

        try:
            if self.config.gui_osc_receiver_port != int(values[self.gui_osc_receiver_port]):
                try:
                    int(values[self.gui_osc_receiver_port])
                    if len(values[self.gui_osc_receiver_port]) <= 5:
                        self.config.gui_osc_receiver_port = int(values[self.gui_osc_receiver_port])
                        changed = True
                    else:
                        print("\033[91m[ERROR] OSC receive port value must be an integer 0-65535\033[0m")
                except:
                    print("\033[91m[ERROR] OSC receive port value must be an integer 0-65535\033[0m")
        except:
            print("\033[91m[ERROR] OSC receive port value cannot be empty and must be an integer 0-65535\033[0m")

        if self.config.gui_osc_address != values[self.gui_osc_address]:
            self.config.gui_osc_address = values[self.gui_osc_address]
            changed = True

        if self.config.gui_osc_recalibrate_address != values[self.gui_osc_recalibrate_address]:
            self.config.gui_osc_recalibrate_address = values[self.gui_osc_recalibrate_address]
            changed = True
        
        if self.config.gui_update_check != values[self.gui_update_check]:
            self.config.gui_update_check = values[self.gui_update_check]
            changed = True

        if self.config.gui_ROSC != values[self.gui_ROSC]:
            self.config.gui_ROSC = values[self.gui_ROSC]
            changed = True

        if self.config.gui_osc_location != values[self.gui_osc_location]:
            self.config.gui_osc_location = values[self.gui_osc_location]
            changed = True
        if values[self.gui_cam_resolution_x] != '':
            if self.config.gui_cam_resolution_x != int(values[self.gui_cam_resolution_x]):
                self.config.gui_cam_resolution_x = int(values[self.gui_cam_resolution_x])
                changed = True
        if values[self.gui_cam_resolution_y] != '':
            if self.config.gui_cam_resolution_y != int(values[self.gui_cam_resolution_y]):
                self.config.gui_cam_resolution_y = int(values[self.gui_cam_resolution_y])
                changed = True
        if values[self.gui_cam_framerate] != '':
            if self.config.gui_cam_framerate != int(values[self.gui_cam_framerate]):
                self.config.gui_cam_framerate = int(values[self.gui_cam_framerate])
                changed = True

        if self.config.gui_use_red_channel != bool(values[self.gui_use_red_channel]):
            self.config.gui_use_red_channel = bool(values[self.gui_use_red_channel])
            changed = True

        if changed:
            self.main_config.save()
        self.osc_queue.put((Tab.SETTINGS))
