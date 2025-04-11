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
import FreeSimpleGUI as sg
import queue
import requests
import threading
import asyncio
import logging
from ctypes import c_int
from babble_model_loader import *
from camera_widget import CameraWidget
from config import BabbleConfig
from tab import Tab
from osc import VRChatOSCReceiver, VRChatOSC
from general_settings_widget import SettingsWidget
from algo_settings_widget import AlgoSettingsWidget
from calib_settings_widget import CalibSettingsWidget
from utils.misc_utils import ensurePath, os_type, bg_color_highlight, bg_color_clear
from lang_manager import LocaleStringManager as lang
from logger import setup_logging
from constants import UIConstants, AppConstants

winmm = None

if os_type == "Windows":
    try:
        from ctypes import windll

        winmm = windll.winmm
    except OSError:
        print(
            f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("error.winmm")}.\033[0m'
        )

os.system("color")  # init ANSI color

# Random environment variable to speed up webcam opening on the MSMF backend.
# https://github.com/opencv/opencv/issues/17687
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
page_url = "https://github.com/Project-Babble/ProjectBabble/releases/latest"
appversion = "Babble v2.0.7"


def timerResolution(toggle):
    if winmm != None:
        if toggle:
            rc = c_int(winmm.timeBeginPeriod(1))
            if rc.value != 0:
                # TIMEERR_NOCANDO = 97
                print(
                    f'\033[93m[{lang._instance.get_string("log.warn")}] {lang._instance.get_string("warn.timerRes")} {rc.value}\033[0m'
                )
        else:
            winmm.timeEndPeriod(1)


async def check_for_updates(config, notification_manager):
    if config.settings.gui_update_check:
        try:
            response = requests.get(
                "https://api.github.com/repos/Project-Babble/ProjectBabble/releases/latest",
                timeout=10,  # Add timeout
            )
            response.raise_for_status()  # Will raise exception for HTTP errors

            data = response.json()
            latestversion = data.get("name")

            if not latestversion:
                print(
                    f'[{lang._instance.get_string("log.warn")}] {lang._instance.get_string("babble.invalidVersionFormat")}'
                )
                return

            if appversion == latestversion:
                print(
                    f'\033[92m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.latestVersion")}! [{latestversion}]\033[0m'
                )
            else:
                print(
                    f'\033[93m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.needUpdateOne")} [{appversion}] {lang._instance.get_string("babble.needUpdateTwo")} [{latestversion}] {lang._instance.get_string("babble.needUpdateThree")}.\033[0m'
                )
                await notification_manager.show_notification(
                    appversion, latestversion, page_url
                )

        except requests.exceptions.Timeout:
            print(
                f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.updateTimeout")}'
            )
        except requests.exceptions.HTTPError as e:
            print(
                f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.updateHttpError")}: {e}'
            )
        except requests.exceptions.ConnectionError:
            print(
                f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.noInternet")}'
            )
        except Exception as e:
            print(
                f'[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.updateCheckFailed")}: {e}'
            )


class ThreadManager:
    def __init__(self, cancellation_event):
        """Initialize ThreadManager with a cancellation event for signaling threads."""
        self.threads = []  # List of (thread, shutdown_obj) tuples
        self.cancellation_event = cancellation_event
        self.logger = logging.getLogger("ThreadManager")

    def add_thread(self, thread, shutdown_obj=None):
        """Add a thread and its optional shutdown object to the manager."""
        self.threads.append((thread, shutdown_obj))
        thread.start()
        self.logger.debug(f"Started thread: {thread.name}")

    def shutdown_all(self, timeout=5.0):
        """Shutdown all managed threads with a configurable timeout."""
        self.logger.info("Initiiating shutdown of all threads")
        self.cancellation_event.set()  # Signal all threads to stop

        # Call shutdown methods on associated objects if available
        for thread, shutdown_obj in self.threads:
            if (
                shutdown_obj
                and hasattr(shutdown_obj, "shutdown")
                and callable(shutdown_obj.shutdown)
            ):
                try:
                    self.logger.debug(f"Calling shutdown on {shutdown_obj}")
                    shutdown_obj.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down {shutdown_obj}: {e}")

        # Join threads with the specified timeout
        for thread, _ in self.threads:
            if thread.is_alive():
                self.logger.debug(
                    f"Joining thread: {thread.name} with timeout {timeout}s"
                )
                thread.join(timeout=timeout)

        # Remove terminated threads from the list
        self.threads = [(t, s) for t, s in self.threads if t.is_alive()]

        if self.threads:
            self.logger.warning(
                f"{len(self.threads)} threads still alive: {[t.name for t, _ in self.threads]}"
            )
        else:
            self.logger.info("All threads terminated successfully")


async def async_main():
    ensurePath()
    setup_logging()

    # Get Configuration
    config: BabbleConfig = BabbleConfig.load()

    # Init locale manager
    lang("Locale", config.settings.gui_language)

    config.save()

    # Uncomment for low-level Vive Facial Tracker logging
    # logging.basicConfig(filename='BabbleApp.log', filemode='w', encoding='utf-8', level=logging.INFO)

    cancellation_event = threading.Event()
    ROSC = False

    timerResolution(True)

    thread_manager = ThreadManager(cancellation_event)

    osc_queue: queue.Queue[tuple[bool, int, int]] = queue.Queue(maxsize=10)
    osc = VRChatOSC(cancellation_event, osc_queue, config)
    osc_thread = threading.Thread(target=osc.run, name="OSCThread")
    thread_manager.add_thread(osc_thread, shutdown_obj=osc)
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
                key=UIConstants.CAM_RADIO_NAME,
            ),
            sg.Radio(
                lang._instance.get_string("babble.settingsPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.SETTINGS),
                key=UIConstants.SETTINGS_RADIO_NAME,
            ),
            sg.Radio(
                lang._instance.get_string("babble.algoSettingsPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.ALGOSETTINGS),
                key=UIConstants.ALGO_SETTINGS_RADIO_NAME,
            ),
            sg.Radio(
                lang._instance.get_string("babble.calibrationPage"),
                "TABSELECTRADIO",
                background_color=bg_color_clear,
                default=(config.cam_display_id == Tab.CALIBRATION),
                key=UIConstants.CALIB_SETTINGS_RADIO_NAME,
            ),
        ],
        [
            sg.Column(
                cams[0].widget_layout,
                vertical_alignment="top",
                key=UIConstants.CAM_NAME,
                visible=(config.cam_display_id in [Tab.CAM]),
                background_color=bg_color_highlight,
            ),
            sg.Column(
                settings[0].widget_layout,
                vertical_alignment="top",
                key=UIConstants.SETTINGS_NAME,
                visible=(config.cam_display_id in [Tab.SETTINGS]),
                background_color=bg_color_highlight,
            ),
            sg.Column(
                settings[1].widget_layout,
                vertical_alignment="top",
                key=UIConstants.ALGO_SETTINGS_NAME,
                visible=(config.cam_display_id in [Tab.ALGOSETTINGS]),
                background_color=bg_color_highlight,
            ),
            sg.Column(
                settings[2].widget_layout,
                vertical_alignment="top",
                key=UIConstants.CALIB_SETTINGS_NAME,
                visible=(config.cam_display_id in [Tab.CALIBRATION]),
                background_color=bg_color_highlight,
            ),
        ],
        # Keep at bottom!
        [
            sg.Text(
                f'- - -  {lang._instance.get_string("general.windowFocus")}  - - -',
                key="-WINFOCUS-",
                background_color=bg_color_clear,
                text_color="#F0F0F0",
                justification="center",
                expand_x=True,
                visible=False,
            )
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
        osc_receiver_thread = threading.Thread(
            target=osc_receiver.run, name="OSCReceiverThread"
        )
        thread_manager.add_thread(osc_receiver_thread, shutdown_obj=osc_receiver)
        ROSC = True

    # Create the window
    window = sg.Window(
        f"{AppConstants.VERSION}",
        layout,
        icon=os.path.join("Images", "logo.ico"),
        background_color=bg_color_clear,
    )

    # Run the main loop
    await main_loop(window, config, cams, settings, thread_manager)

    # Cleanup after main loop exits
    timerResolution(False)
    print(
        f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.exit")}\033[0m'
    )


async def main_loop(window, config, cams, settings, thread_manager):
    tint = AppConstants.DEFAULT_WINDOW_FOCUS_REFRESH
    fs = False

    while True:
        event, values = window.read(timeout=tint)

        if event in ("Exit", sg.WIN_CLOSED):
            # Exit code here
            for cam in cams:
                cam.stop()
            thread_manager.shutdown_all()
            window.close()
            return

        try:
            # If window isn't in focus increase timeout and stop loop early
            if window.TKroot.focus_get():
                if fs:
                    fs = False
                    tint = AppConstants.DEFAULT_WINDOW_FOCUS_REFRESH
                    window[UIConstants.WINDOW_FOCUS_KEY].update(visible=False)
                    window[UIConstants.WINDOW_FOCUS_KEY].hide_row()
                    window.refresh()
            else:
                if not fs:
                    fs = True
                    tint = AppConstants.UNFOCUSED_WINDOW_REFRESH
                    window[UIConstants.WINDOW_FOCUS_KEY].update(visible=True)
                    window[UIConstants.WINDOW_FOCUS_KEY].unhide_row()
                continue
        except KeyError:
            pass

        if values[UIConstants.CAM_RADIO_NAME] and config.cam_display_id != Tab.CAM:
            cams[0].start()
            settings[0].stop()
            settings[1].stop()
            settings[2].stop()
            window[UIConstants.CAM_NAME].update(visible=True)
            window[UIConstants.SETTINGS_NAME].update(visible=False)
            window[UIConstants.ALGO_SETTINGS_NAME].update(visible=False)
            window[UIConstants.CALIB_SETTINGS_NAME].update(visible=False)
            config.cam_display_id = Tab.CAM
            config.save()

        elif (
            values[UIConstants.SETTINGS_RADIO_NAME]
            and config.cam_display_id != Tab.SETTINGS
        ):
            cams[0].stop()
            settings[1].stop()
            settings[2].stop()
            settings[0].start()
            window[UIConstants.CAM_NAME].update(visible=False)
            window[UIConstants.SETTINGS_NAME].update(visible=True)
            window[UIConstants.ALGO_SETTINGS_NAME].update(visible=False)
            window[UIConstants.CALIB_SETTINGS_NAME].update(visible=False)
            config.cam_display_id = Tab.SETTINGS
            config.save()

        elif (
            values[UIConstants.ALGO_SETTINGS_RADIO_NAME]
            and config.cam_display_id != Tab.ALGOSETTINGS
        ):
            cams[0].stop()
            settings[0].stop()
            settings[2].stop()
            settings[1].start()
            window[UIConstants.CAM_NAME].update(visible=False)
            window[UIConstants.SETTINGS_NAME].update(visible=False)
            window[UIConstants.ALGO_SETTINGS_NAME].update(visible=True)
            window[UIConstants.CALIB_SETTINGS_NAME].update(visible=False)
            config.cam_display_id = Tab.ALGOSETTINGS
            config.save()

        elif (
            values[UIConstants.CALIB_SETTINGS_RADIO_NAME]
            and config.cam_display_id != Tab.CALIBRATION
        ):
            cams[0].start()  # Allow tracking to continue in calibration tab
            settings[0].stop()
            settings[1].stop()
            settings[2].start()
            window[UIConstants.CAM_NAME].update(visible=False)
            window[UIConstants.SETTINGS_NAME].update(visible=False)
            window[UIConstants.ALGO_SETTINGS_NAME].update(visible=False)
            window[UIConstants.CALIB_SETTINGS_NAME].update(visible=True)
            config.cam_display_id = Tab.CALIBRATION
            config.save()

        # Otherwise, render all
        for cam in cams:
            if cam.started():
                cam.render(window, event, values)
        for setting in settings:
            if setting.started():
                setting.render(window, event, values)

        # Rather than await asyncio.sleep(0), yield control periodically
        await asyncio.sleep(0.001)  # Small sleep to allow other tasks to rundef main():
    asyncio.run(async_main())


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
