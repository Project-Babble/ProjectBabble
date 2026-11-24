import kivy_ui as ui  # Must be imported before any other Kivy module
from kivy.uix.scrollview import ScrollView

from lang_manager import LocaleStringManager as lang
from config import BabbleSettingsConfig
from osc import Tab
from queue import Queue
from threading import Event
from utils.misc_utils import bg_color_highlight, bg_color_clear, is_valid_int_input, is_valid_float_input


def _is_port(value):
    return value.isdigit() and len(value) <= 5


class SettingsWidget:
    def __init__(
        self, widget_id: Tab, main_config: BabbleSettingsConfig, osc_queue: Queue
    ):
        self.main_config = main_config
        self.config = main_config.settings
        self.osc_queue = osc_queue
        self.available_languages = (
            lang._instance.get_languages()
        )  # Add more languages as needed

        s = lang._instance.get_string
        c = self.config
        digits = lambda v: v == "" or v.isdigit()
        port_chars = lambda v: v == "" or _is_port(v)

        # Define the window's contents
        panel = ui.Panel(bg=bg_color_highlight, auto_height=True)
        panel.add_widget(
            ui.row(
                ui.checkbox(
                    s("general.checkForUpdates"),
                    c.gui_update_check,
                    on_change=self._setter("gui_update_check", bool),
                    tooltip=s("general.toolTip"),
                ),
                ui.checkbox(
                    s("general.logging"),
                    c.gui_logging,
                    on_change=self._setter("gui_logging", bool),
                    tooltip=s("general.loggingTooltip"),
                ),
            )
        )
        panel.add_widget(ui.section_header(f'{s("general.oscSettings")}:'))
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.locationPrefix")}:'),
                ui.text_input(
                    c.gui_osc_location,
                    on_change=self._setter("gui_osc_location", str),
                    chars=30,
                    tooltip=f'{s("general.locationTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.address")}:'),
                ui.text_input(
                    c.gui_osc_address,
                    on_change=self._setter("gui_osc_address", str),
                    chars=18,
                    tooltip=f'{s("general.addressTooltip")}.',
                ),
                ui.label(f'{s("general.port")}:'),
                ui.text_input(
                    c.gui_osc_port,
                    on_change=self._setter("gui_osc_port", int, _is_port),
                    chars=7,
                    validator=port_chars,
                    tooltip=f'{s("general.portTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.receiver")}'),
                ui.checkbox(
                    "",
                    c.gui_ROSC,
                    on_change=self._setter("gui_ROSC", bool),
                    tooltip=f'{s("general.receiverTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.receiver")}:'),
                ui.text_input(
                    c.gui_osc_receiver_port,
                    on_change=self._setter("gui_osc_receiver_port", int, _is_port),
                    chars=7,
                    validator=port_chars,
                    tooltip=f'{s("general.receiverPortTooltip")}:',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.recalibrate")}:'),
                ui.text_input(
                    c.gui_osc_recalibrate_address,
                    on_change=self._setter("gui_osc_recalibrate_address", str),
                    chars=36,
                    tooltip=f'{s("general.recalibrateTooltip")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.disableCameraPreview")}'),
                ui.checkbox(
                    "",
                    c.gui_disable_camera_preview,
                    on_change=self._setter("gui_disable_camera_preview", bool),
                    tooltip=f'{s("general.disableCameraPreview")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.oscDelayEnable")}'),
                ui.checkbox(
                    "",
                    c.gui_osc_delay_enable,
                    on_change=self._setter("gui_osc_delay_enable", bool),
                    tooltip=f'{s("general.oscDelayEnable")}.',
                ),
            )
        )
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.oscDelaySeconds")}:'),
                ui.text_input(
                    c.gui_osc_delay_seconds,
                    on_change=self._setter("gui_osc_delay_seconds", float, _is_float),
                    chars=8,
                    validator=is_valid_float_input,
                    tooltip=f'{s("general.oscDelaySeconds")}.',
                ),
            )
        )
        panel.add_widget(ui.section_header(f'{s("general.uvcCameraSettings")}:'))
        panel.add_widget(
            ui.row(
                ui.label(f'{s("general.useRedChannel")}:'),
                ui.checkbox(
                    "",
                    c.gui_use_red_channel,
                    on_change=self._setter("gui_use_red_channel", bool),
                    tooltip=f'{s("general.useRedChannelTooltip")}.',
                ),
                ui.label(f'{s("general.xResolution")}.'),
                ui.text_input(
                    c.gui_cam_resolution_x,
                    on_change=self._setter("gui_cam_resolution_x", int, str.isdigit),
                    chars=6,
                    validator=digits,
                    tooltip=f'{s("general.xResolutionTooltip")}',
                ),
                ui.label(f'{s("general.yResolution")}.'),
                ui.text_input(
                    c.gui_cam_resolution_y,
                    on_change=self._setter("gui_cam_resolution_y", int, str.isdigit),
                    chars=6,
                    validator=digits,
                    tooltip=f'{s("general.yResolutionTooltip")}',
                ),
                ui.label(f'{s("general.framerate")}:'),
                ui.text_input(
                    c.gui_cam_framerate,
                    on_change=self._setter("gui_cam_framerate", int, str.isdigit),
                    chars=6,
                    validator=digits,
                    tooltip=f'{s("general.framerateTooltip")}',
                ),
            )
        )
        panel.add_widget(ui.section_header(f'{s("general.language")}:'))
        panel.add_widget(ui.wrapping_label(f'{s("general.languageInstructions")}.'))
        panel.add_widget(
            ui.row(
                ui.spinner(
                    self.available_languages,
                    c.gui_language,
                    on_change=self._setter("gui_language", str),
                    tooltip=f'{s("general.languageTooltip")}.',
                )
            )
        )

        self.general_settings_layout = panel

        page = ui.Panel(bg=bg_color_clear, padding=0)
        page.add_widget(ui.section_header(f'{s("general.header")}:'))
        scroll = ScrollView(do_scroll_x=False, bar_width=ui.dp(8), scroll_type=["bars", "content"])
        scroll.add_widget(panel)
        page.add_widget(scroll)
        self.widget_layout = page

        self.cancellation_event = (
            Event()
        )  # Set the event until start is called, otherwise we can block if shutdown is called.
        self.cancellation_event.set()
        self.image_queue = Queue(maxsize=2)

    def _setter(self, attr, convert, is_complete=None):
        """Build a change handler that converts, stores and saves a setting.

        ``is_complete`` filters out partial input (e.g. an empty field or a lone "-") so it
        isn't written to the config, matching the previous behaviour.
        """

        def handler(value):
            if is_complete is not None and not is_complete(value):
                return
            try:
                new_value = convert(value)
            except (TypeError, ValueError):
                return
            if getattr(self.config, attr) != new_value:
                setattr(self.config, attr, new_value)
                self.main_config.save()

        return handler

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

    def render(self):
        # Settings are applied as soon as they are edited (see _setter); nothing to poll.
        pass


def _is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
