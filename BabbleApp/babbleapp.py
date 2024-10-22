"""
-------------------------------------------------------------------------------------------------------------
██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗    ██████╗  █████╗ ██████╗ ██████╗ ██╗     ███████╗
██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║     ██╔════╝
██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║       ██████╔╝███████║██████╔╝██████╔╝██║     █████╗
██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║       ██╔══██╗██╔══██║██╔══██╗██╔══██╗██║     ██╔══╝
██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║       ██████╔╝██║  ██║██████╔╝██████╔╝███████╗███████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝       ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚══════╝
--------------------------------------------------------------------------------------------------------------
GUI by: Prohurtz, qdot
Model by: Summer
App model implementation: Prohurtz, Summer

Additional contributors: RamesTheGeneric (dataset synthesizer), dfgHiatus (locale, some other stuff)

Copyright (c) 2023 Project Babble <3
"""

import os
import PySimpleGUI as sg
import queue
import requests
import threading
from ctypes import windll, c_int
from babble_model_loader import *
from camera_widget import CameraWidget
from config import BabbleConfig
from tab import CamInfo, Tab
from osc import VRChatOSCReceiver, VRChatOSC
from general_settings_widget import SettingsWidget
from algo_settings_widget import AlgoSettingsWidget
from calib_settings_widget import CalibSettingsWidget
from utils.misc_utils import EnsurePath, is_nt, bg_color_highlight, bg_color_clear
from lang_manager import LocaleStringManager as lang

winmm = None

if is_nt:
    from winotify import Notification
    try:
        winmm = windll.winmm
    except OSError:
        print(f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("error.winmm")}.\033[0m')
os.system("color")  # init ANSI color

# Random environment variable to speed up webcam opening on the MSMF backend.
# https://github.com/opencv/opencv/issues/17687
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

WINDOW_NAME = "Babble App"
CAM_NAME = "-CAMWIDGET-"
SETTINGS_NAME = "-SETTINGSWIDGET-"
ALGO_SETTINGS_NAME = "-ALGOSETTINGSWIDGET-"
CALIB_SETTINGS_NAME = "-CALIBSETTINGSWIDGET-"
CAM_RADIO_NAME = "-CAMRADIO-"
SETTINGS_RADIO_NAME = "-SETTINGSRADIO-"
ALGO_SETTINGS_RADIO_NAME = "-ALGOSETTINGSRADIO-"
CALIB_SETTINGS_RADIO_NAME = "-CALIBSETTINGSRADIO-"

page_url = "https://github.com/SummerSigh/ProjectBabble/releases/latest"
appversion = "Babble v2.0.6 Alpha"

def timerResolution(toggle):
    if winmm != None:
        if toggle:
            rc = c_int(winmm.timeBeginPeriod(1))
            if rc.value != 0:
                # TIMEERR_NOCANDO = 97
                print(f'\033[93m[{lang._instance.get_string("log.warn")}] {lang._instance.get_string("warn.timerRes")} {rc.value}\033[0m')
        else:
            winmm.timeEndPeriod(1)

def main():
    EnsurePath()

    # Get Configuration
    config: BabbleConfig = BabbleConfig.load()

    # Init locale manager
    lang("Locale", config.settings.gui_language)

    config.save()

    cancellation_event = threading.Event()
    ROSC = False
    # Check to see if we can connect to our video source first. If not, bring up camera finding
    # dialog.

    if config.settings.gui_update_check:
        try:
            response = requests.get(
                "https://api.github.com/repos/SummerSigh/ProjectBabble/releases/latest"
            )
            latestversion = response.json()["name"]
            if (
                appversion == latestversion
            ):  # If what we scraped and hardcoded versions are same, assume we are up to date.
                print(
                    f'\033[92m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.latestVersion")}! [{latestversion}]\033[0m'
                )
            else:
                print(
                    f'\033[93m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.needUpdateOne")} [{appversion}] {lang._instance.get_string("babble.needUpdateTwo")} [{latestversion}] {lang._instance.get_string("babble.needUpdateThree")}.\033[0m'
                )
                try:
                    if is_nt:
                        cwd = os.getcwd()
                        icon = cwd + "\Images\logo.ico"
                        toast = Notification(
                            app_id=lang._instance.get_string("babble.name"),
                            title=lang._instance.get_string("babble.updatePresent"),
                            msg=f'{lang._instance.get_string("babble.updateTo")} {latestversion}',
                            icon=r"{}".format(icon),
                        )
                        toast.add_actions(
                            label=lang._instance.get_string("babble.downloadPage"),
                            launch="https://github.com/SummerSigh/ProjectBabble/releases/latest",
                        )
                        toast.show()
                except Exception as e:
                    print(
                        f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.noToast")}'
                    )
        except:
            print(
                f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.noInternet")}.'
            )
    timerResolution(True)
    # Check to see if we have an ROI. If not, bring up ROI finder GUI.

    # Spawn worker threads
    osc_queue: queue.Queue[tuple[bool, int, int]] = queue.Queue(maxsize=2)
    osc = VRChatOSC(cancellation_event, osc_queue, config)
    osc_thread = threading.Thread(target=osc.run)
    # start worker threads
    osc_thread.start()

    cams = [
        CameraWidget(Tab.CAM, config, osc_queue),
    ]

    settings = [
        SettingsWidget(Tab.SETTINGS, config, osc_queue),
        AlgoSettingsWidget(Tab.ALGOSETTINGS, config, osc_queue),
        CalibSettingsWidget(Tab.CALIBRATION, config, osc_queue),
    ]

    layout = [
        [
            sg.Radio(
                lang._instance.get_string("babble.camPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.CAM),
                key=CAM_RADIO_NAME,
            ),
            sg.Radio(
                lang._instance.get_string("babble.settingsPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.SETTINGS),
                key=SETTINGS_RADIO_NAME,
            ),
            sg.Radio(
                lang._instance.get_string("babble.algoSettingsPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.ALGOSETTINGS),
                key=ALGO_SETTINGS_RADIO_NAME,
            ),
            sg.Radio(
                lang._instance.get_string("babble.calibrationPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.CALIBRATION),
                key=CALIB_SETTINGS_RADIO_NAME,
            ),
        ],
        [
            sg.Column(
                cams[0].widget_layout,
                vertical_alignment="top",
                key=CAM_NAME,
                visible=(config.cam_display_id in [Tab.CAM]),
                background_color=bg_color_highlight,
            ),
            sg.Column(
                settings[0].widget_layout,
                vertical_alignment="top",
                key=SETTINGS_NAME,
                visible=(config.cam_display_id in [Tab.SETTINGS]),
                background_color=bg_color_highlight,
            ),
            sg.Column(
                settings[1].widget_layout,
                vertical_alignment="top",
                key=ALGO_SETTINGS_NAME,
                visible=(config.cam_display_id in [Tab.ALGOSETTINGS]),
                background_color=bg_color_highlight,
            ),
            sg.Column(
                settings[2].widget_layout,
                vertical_alignment="top",
                key=CALIB_SETTINGS_NAME,
                visible=(config.cam_display_id in [Tab.CALIBRATION]),
                background_color=bg_color_highlight,
            ),
        ],
    ]

    if config.cam_display_id in [Tab.CAM]:
        cams[0].start()
    if config.cam_display_id in [Tab.SETTINGS]:
        settings[0].start()
    if config.cam_display_id in [Tab.ALGOSETTINGS]:
        settings[1].start()
    if config.cam_display_id in [Tab.CALIBRATION]:
        settings[2].start()

    # the cam needs to be running before it is passed to the OSC
    if config.settings.gui_ROSC:
        osc_receiver = VRChatOSCReceiver(cancellation_event, config, cams)
        osc_receiver_thread = threading.Thread(target=osc_receiver.run)
        osc_receiver_thread.start()
        ROSC = True

    # Create the window
    window = sg.Window(
        f"{appversion}", layout, icon="Images/logo.ico", background_color=bg_color_clear
    )

    # GUI Render loop
    while True:
        # First off, check for any events from the GUI
        event, values = window.read(timeout=2)

        # If we're in either mode and someone hits q, quit immediately
        if event == "Exit" or event == sg.WIN_CLOSED:
            for (
                cam
            ) in (
                cams
            ):  # yes we only have one cam page but im just gonna leave this incase
                cam.stop()
            cancellation_event.set()
            # shut down worker threads
            osc_thread.join()
            # TODO: find a way to have this function run on join maybe??
            # threading.Event() wont work because pythonosc spawns its own thread.
            # only way i can see to get around this is an ugly while loop that only checks if a threading event is triggered
            # and then call the pythonosc shutdown function
            if ROSC:
                osc_receiver.shutdown()
                osc_receiver_thread.join()
            timerResolution(False)
            print(
                f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.exit")}\033[0m'
            )
            return

        if values[CAM_RADIO_NAME] and config.cam_display_id != Tab.CAM:
            cams[0].start()
            settings[0].stop()
            settings[1].stop()
            settings[2].stop()
            window[CAM_NAME].update(visible=True)
            window[SETTINGS_NAME].update(visible=False)
            window[ALGO_SETTINGS_NAME].update(visible=False)
            window[CALIB_SETTINGS_NAME].update(visible=False)
            config.cam_display_id = Tab.CAM
            config.save()

        elif values[SETTINGS_RADIO_NAME] and config.cam_display_id != Tab.SETTINGS:
            cams[0].stop()
            settings[1].stop()
            settings[2].stop()
            settings[0].start()
            window[CAM_NAME].update(visible=False)
            window[SETTINGS_NAME].update(visible=True)
            window[ALGO_SETTINGS_NAME].update(visible=False)
            window[CALIB_SETTINGS_NAME].update(visible=False)
            config.cam_display_id = Tab.SETTINGS
            config.save()

        elif (
            values[ALGO_SETTINGS_RADIO_NAME]
            and config.cam_display_id != Tab.ALGOSETTINGS
        ):
            cams[0].stop()
            settings[0].stop()
            settings[2].stop()
            settings[1].start()
            window[CAM_NAME].update(visible=False)
            window[SETTINGS_NAME].update(visible=False)
            window[ALGO_SETTINGS_NAME].update(visible=True)
            window[CALIB_SETTINGS_NAME].update(visible=False)
            config.cam_display_id = Tab.ALGOSETTINGS
            config.save()

        elif (
            values[CALIB_SETTINGS_RADIO_NAME]
            and config.cam_display_id != Tab.CALIBRATION
        ):
            cams[0].start()  # Allow tracking to continue in calibration tab
            settings[0].stop()
            settings[1].stop()
            settings[2].start()
            window[CAM_NAME].update(visible=False)
            window[SETTINGS_NAME].update(visible=False)
            window[ALGO_SETTINGS_NAME].update(visible=False)
            window[CALIB_SETTINGS_NAME].update(visible=True)
            config.cam_display_id = Tab.CALIBRATION
            config.save()

        # Otherwise, render all
        for cam in cams:
            if cam.started():
                cam.render(window, event, values)
        for setting in settings:
            if setting.started():
                setting.render(window, event, values)


if __name__ == "__main__":
    main()
