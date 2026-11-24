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
import queue
import requests
import threading
import logging

import kivy_ui as ui  # Configures Kivy; must come before any other Kivy import
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton

from babble_model_loader import *
from camera_widget import CameraWidget
from config import BabbleConfig
from tab import Tab
from osc import VRChatOSCReceiver, VRChatOSC
from general_settings_widget import SettingsWidget
from algo_settings_widget import AlgoSettingsWidget
from calib_settings_widget import CalibSettingsWidget
from utils.misc_utils import ensurePath, os_type, is_android, bg_color_highlight, bg_color_clear
from lang_manager import LocaleStringManager as lang
from logger import setup_logging
from constants import AppConstants

winmm = None

if os_type == "Windows":
    try:
        from ctypes import windll, c_int
        winmm = windll.winmm
    except OSError:
        print(
            f'\033[91m[{lang._instance.get_string("log.error")}] {lang._instance.get_string("error.winmm")}.\033[0m'
        )

if os_type == "Windows":
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


class BabbleApp(App):
    """Kivy application hosting the camera, settings, algorithm and calibration pages."""

    def __init__(self, config: BabbleConfig, **kwargs):
        super().__init__(**kwargs)
        self.babble_config = config
        self.title = f"{AppConstants.VERSION}"
        self.icon = os.path.join("Images", "logo.ico")
        self.cancellation_event = threading.Event()
        self.thread_manager = ThreadManager(self.cancellation_event)
        self.focused = True
        self._render_event = None
        self._stopped = False

    # Kivy's App has its own "config" attribute, so ours is kept as babble_config.
    def build(self):
        config = self.babble_config
        Window.clearcolor = ui.rgba(bg_color_clear)

        osc_queue: queue.Queue[tuple[bool, int, int]] = queue.Queue(maxsize=10)
        osc = VRChatOSC(self.cancellation_event, osc_queue, config)
        osc_thread = threading.Thread(target=osc.run, name="OSCThread")
        self.thread_manager.add_thread(osc_thread, shutdown_obj=osc)

        self.cams = [
            CameraWidget(Tab.CAM, config, osc_queue),
        ]
        self.settings_pages = [
            SettingsWidget(Tab.SETTINGS, config, osc_queue),
            AlgoSettingsWidget(Tab.ALGOSETTINGS, config, osc_queue),
            CalibSettingsWidget(Tab.CALIBRATION, config, osc_queue),
        ]
        self.settings_pages[1].on_clear_calibration = self.cams[0].clear_calibration
        self.pages = {
            Tab.CAM: self.cams[0].widget_layout,
            Tab.SETTINGS: self.settings_pages[0].widget_layout,
            Tab.ALGOSETTINGS: self.settings_pages[1].widget_layout,
            Tab.CALIBRATION: self.settings_pages[2].widget_layout,
        }

        s = lang._instance.get_string
        root = BoxLayout(orientation="vertical", padding=ui.PADDING, spacing=ui.SPACING)

        # Tab selector (replaces the TABSELECTRADIO radio buttons)
        tab_bar = ui.row()
        self.tab_buttons = {}
        for tab, key in [
            (Tab.CAM, "babble.camPage"),
            (Tab.SETTINGS, "babble.settingsPage"),
            (Tab.ALGOSETTINGS, "babble.algoSettingsPage"),
            (Tab.CALIBRATION, "babble.calibrationPage"),
        ]:
            btn = ToggleButton(
                text=s(key),
                group="TABSELECTRADIO",
                allow_no_selection=False,
                state="down" if config.cam_display_id == tab else "normal",
                size_hint=(None, None),
                height=ui.ROW_HEIGHT,
                font_size=ui.FONT_SIZE,
                background_normal="",
                background_down="",
            )
            ui._fit_width(btn, extra=ui.dp(28))
            self._style_tab(btn)
            btn.bind(state=lambda inst, value, t=tab: self._on_tab_state(inst, value, t))
            self.tab_buttons[tab] = btn
            tab_bar.add_widget(btn)
        root.add_widget(tab_bar)

        self.page_container = BoxLayout()
        ui.paint_background(self.page_container, bg_color_highlight)
        root.add_widget(self.page_container)

        # Keep at bottom!
        self.focus_label = ui.wrapping_label(
            f'- - -  {s("general.windowFocus")}  - - -', halign="center"
        )

        if config.cam_display_id not in self.pages:
            config.cam_display_id = Tab.CAM
        self.page_container.add_widget(self.pages[config.cam_display_id])
        if config.cam_display_id in [Tab.CAM]:
            self.cams[0].start()
        if config.cam_display_id in [Tab.SETTINGS]:
            self.settings_pages[0].start()
        if config.cam_display_id in [Tab.ALGOSETTINGS]:
            self.settings_pages[1].start()
        if config.cam_display_id in [Tab.CALIBRATION]:
            self.settings_pages[2].start()

        # the cam needs to be running before it is passed to the OSC
        if config.settings.gui_ROSC:
            osc_receiver = VRChatOSCReceiver(self.cancellation_event, config, self.cams)
            osc_receiver_thread = threading.Thread(
                target=osc_receiver.run, name="OSCReceiverThread"
            )
            self.thread_manager.add_thread(osc_receiver_thread, shutdown_obj=osc_receiver)

        self.root_layout = root
        if not is_android:
            Window.bind(focus=self._on_window_focus)
        self._schedule_render(AppConstants.DEFAULT_WINDOW_FOCUS_REFRESH)
        return root

    # --- Tabs ---------------------------------------------------------------------------------
    @staticmethod
    def _style_tab(btn):
        btn.background_color = ui.rgba(bg_color_highlight if btn.state == "down" else "#333133")
        btn.bold = btn.state == "down"

    def _on_tab_state(self, btn, state, tab):
        self._style_tab(btn)
        if state == "down":
            self.select_tab(tab)

    def select_tab(self, tab):
        config = self.babble_config
        if config.cam_display_id == tab and self.pages[tab].parent is self.page_container:
            return
        cams, settings = self.cams, self.settings_pages
        if tab == Tab.CAM:
            cams[0].start()
            settings[0].stop()
            settings[1].stop()
            settings[2].stop()
        elif tab == Tab.SETTINGS:
            cams[0].stop()
            settings[1].stop()
            settings[2].stop()
            settings[0].start()
        elif tab == Tab.ALGOSETTINGS:
            cams[0].stop()
            settings[0].stop()
            settings[2].stop()
            settings[1].start()
        elif tab == Tab.CALIBRATION:
            cams[0].start()  # Allow tracking to continue in calibration tab
            settings[0].stop()
            settings[1].stop()
            settings[2].start()
        ui.tooltips.hide()
        self.page_container.clear_widgets()
        self.page_container.add_widget(self.pages[tab])
        config.cam_display_id = tab
        config.save()

    # --- Rendering ----------------------------------------------------------------------------
    def _schedule_render(self, interval_ms):
        if self._render_event is not None:
            self._render_event.cancel()
        self._render_event = Clock.schedule_interval(self.render, interval_ms / 1000.0)

    def _on_window_focus(self, window, focused):
        # If the window isn't in focus, refresh less often and pause the previews.
        if focused == self.focused:
            return
        self.focused = focused
        if focused:
            if self.focus_label.parent is not None:
                self.root_layout.remove_widget(self.focus_label)
            self._schedule_render(AppConstants.DEFAULT_WINDOW_FOCUS_REFRESH)
        else:
            ui.tooltips.hide()
            if self.focus_label.parent is None:
                self.root_layout.add_widget(self.focus_label)
            self._schedule_render(AppConstants.UNFOCUSED_WINDOW_REFRESH)

    def render(self, dt):
        if not self.focused:
            return
        for cam in self.cams:
            if cam.started():
                cam.render()
        for setting in self.settings_pages:
            if setting.started():
                setting.render()

    # --- Lifecycle ----------------------------------------------------------------------------
    def on_pause(self):
        # Android: keep tracking/OSC running while the app is in the background.
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        if self._stopped:
            return
        self._stopped = True
        if self._render_event is not None:
            self._render_event.cancel()
        # Exit code here
        for cam in getattr(self, "cams", []):
            cam.stop()
        self.thread_manager.shutdown_all()


def main():
    ensurePath()

    # Get Configuration
    config: BabbleConfig = BabbleConfig.load()
    
    # Init logging. TODO: Initiate before "BabbleConfig.load()"?
    if config.settings.gui_logging:
        setup_logging()

    # Init locale manager
    lang("Locale", config.settings.gui_language)

    config.save()

    # Uncomment for low-level Vive Facial Tracker logging
    # logging.basicConfig(filename='BabbleApp.log', filemode='w', encoding='utf-8', level=logging.INFO)

    timerResolution(True)
    ui.setup_fonts()
    app = BabbleApp(config)
    try:
        app.run()
    finally:
        # Also runs if the UI failed to start, so worker threads don't keep the process alive.
        app.on_stop()
        timerResolution(False)
    print(
        f'\033[94m[{lang._instance.get_string("log.info")}] {lang._instance.get_string("babble.exit")}\033[0m'
    )


if __name__ == "__main__":
    main()
