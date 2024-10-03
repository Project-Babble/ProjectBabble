import PySimpleGUI as sg
from lang_manager import LocaleStringManager as lang
from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
from utils.misc_utils import bg_color_highlight, bg_color_clear


class SettingsWidget:
    def __init__(
        self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue
    ):
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
        self.gui_language = f"-LANGUAGE{widget_id}-"  # Add this line
        self.main_config = main_config
        self.config = main_config.settings
        self.osc_queue = osc_queue
        self.available_languages = (
            lang._instance.get_languages()
        )  # Add more languages as needed

        # Define the window's contents
        self.general_settings_layout = [
            [
                sg.Checkbox(
                    lang._instance.get_string("general.checkForUpdates"),
                    default=self.config.gui_update_check,
                    key=self.gui_update_check,
                    background_color=bg_color_highlight,
                    tooltip=lang._instance.get_string("general.toolTip"),
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.oscSettings")}:',
                    background_color=bg_color_clear,
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.locationPrefix")}:',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_osc_location,
                    key=self.gui_osc_location,
                    size=(30),
                    tooltip=f'{lang._instance.get_string("general.locationTooltip")}.',
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.address")}:',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_osc_address,
                    key=self.gui_osc_address,
                    size=(0, 20),
                    tooltip=f'{lang._instance.get_string("general.addressTooltip")}.',
                ),
                #  ],
                #  [
                sg.Text(
                    f'{lang._instance.get_string("general.port")}:',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_osc_port,
                    key=self.gui_osc_port,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.portTooltip")}.',
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.receiver")}',
                    background_color=bg_color_highlight,
                ),
                sg.Checkbox(
                    "",
                    default=self.config.gui_ROSC,
                    key=self.gui_ROSC,
                    background_color=bg_color_highlight,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.receiverTooltip")}.',
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.receiver")}:',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_osc_receiver_port,
                    key=self.gui_osc_receiver_port,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.receiverPortTooltip")}:',
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.recalibrate")}:',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_osc_recalibrate_address,
                    key=self.gui_osc_recalibrate_address,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.recalibrateTooltip")}.',
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.uvcCameraSettings")}:',
                    background_color=bg_color_clear,
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.useRedChannel")}:',
                    background_color=bg_color_highlight,
                ),
                sg.Checkbox(
                    "",
                    default=self.config.gui_use_red_channel,
                    key=self.gui_use_red_channel,
                    background_color=bg_color_highlight,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.useRedChannelTooltip")}.',
                ),
                sg.Text(
                    f'{lang._instance.get_string("general.xResolution")}.',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_cam_resolution_x,
                    key=self.gui_cam_resolution_x,
                    size=(0, 20),
                    tooltip=f'{lang._instance.get_string("general.xResolutionTooltip")}',
                ),
                #  ],
                #  [
                sg.Text(
                    f'{lang._instance.get_string("general.yResolution")}.',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_cam_resolution_y,
                    key=self.gui_cam_resolution_y,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.yResolutionTooltip")}',
                ),
                #  ],
                #  [
                sg.Text(
                    f'{lang._instance.get_string("general.framerate")}:',
                    background_color=bg_color_highlight,
                ),
                sg.InputText(
                    self.config.gui_cam_framerate,
                    key=self.gui_cam_framerate,
                    size=(0, 10),
                    tooltip=f'{lang._instance.get_string("general.framerateTooltip")}',
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.language")}:',
                    background_color=bg_color_clear,
                ),
            ],
            [
                sg.Text(
                    f'{lang._instance.get_string("general.languageInstructions")}.',
                    background_color=bg_color_highlight,
                ),
            ],
            [
                sg.OptionMenu(
                    self.available_languages,
                    default_value=self.config.gui_language,
                    key=self.gui_language,
                    tooltip=f'{lang._instance.get_string("general.languageTooltip")}.',
                ),
            ],
        ]

        self.widget_layout = [
            [
                sg.Text(
                    f'{lang._instance.get_string("general.header")}:',
                    background_color=bg_color_clear,
                ),
            ],
            [
                sg.Column(
                    self.general_settings_layout,
                    key=self.gui_general_settings_layout,
                    background_color=bg_color_highlight,
                ),
            ],
        ]

        self.cancellation_event = (
            Event()
        )  # Set the event until start is called, otherwise we can block if shutdown is called.
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
                        print(
                            f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("general.oscPort")}\033[0m'
                        )
                except:
                    print(
                        f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("general.oscPort")}\033[0m'
                    )
        except:
            print(
                f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("general.oscValue")}\033[0m'
            )

        try:
            if self.config.gui_osc_receiver_port != int(
                values[self.gui_osc_receiver_port]
            ):
                try:
                    int(values[self.gui_osc_receiver_port])
                    if len(values[self.gui_osc_receiver_port]) <= 5:
                        self.config.gui_osc_receiver_port = int(
                            values[self.gui_osc_receiver_port]
                        )
                        changed = True
                    else:
                        print(
                            f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("general.oscPort")}\033[0m'
                        )
                except:
                    print(
                        f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("general.oscPort")}\033[0m'
                    )
        except:
            print(
                f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("general.oscValue")}\033[0m'
            )

        if self.config.gui_osc_address != values[self.gui_osc_address]:
            self.config.gui_osc_address = values[self.gui_osc_address]
            changed = True

        if (
            self.config.gui_osc_recalibrate_address
            != values[self.gui_osc_recalibrate_address]
        ):
            self.config.gui_osc_recalibrate_address = values[
                self.gui_osc_recalibrate_address
            ]
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

        if values[self.gui_cam_resolution_x] != "":
            if (
                str(self.config.gui_cam_resolution_x)
                != values[self.gui_cam_resolution_x]
            ):
                try:
                    self.config.gui_cam_resolution_x = int(
                        values[self.gui_cam_resolution_x]
                    )
                    changed = True
                except:
                    print(lang._instance.get_string("general.notAnInt"))
        if values[self.gui_cam_resolution_y] != "":
            if (
                str(self.config.gui_cam_resolution_y)
                != values[self.gui_cam_resolution_y]
            ):
                try:
                    self.config.gui_cam_resolution_y = int(
                        values[self.gui_cam_resolution_y]
                    )
                    changed = True
                except:
                    print(lang._instance.get_string("general.notAnInt"))
        if values[self.gui_cam_framerate] != "":
            if str(self.config.gui_cam_framerate) != values[self.gui_cam_framerate]:
                try:
                    self.config.gui_cam_framerate = int(values[self.gui_cam_framerate])
                    changed = True
                except:
                    print(lang._instance.get_string("general.notAnInt"))

        if self.config.gui_use_red_channel != bool(values[self.gui_use_red_channel]):
            self.config.gui_use_red_channel = bool(values[self.gui_use_red_channel])
            changed = True

        if self.config.gui_language != values[self.gui_language]:
            self.config.gui_language = values[self.gui_language]
            changed = True

        if changed:
            self.main_config.save()
        self.osc_queue.put((Tab.SETTINGS))
