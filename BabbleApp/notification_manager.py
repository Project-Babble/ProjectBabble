import os
import webbrowser
import signal
import asyncio
from pathlib import Path
from desktop_notifier import DesktopNotifier, Urgency, Button, Icon, DEFAULT_SOUND
from lang_manager import LocaleStringManager as lang
from utils.misc_utils import os_type

class NotificationManager:
    def __init__(self):
        self.notifier = DesktopNotifier(app_name="Babble App")
        self.loop = None
        self.stop_event = None
        
    async def show_notification(self, appversion, latestversion, page_url):
        logo = Icon(
            path=Path(os.path.join(os.getcwd(), "Images", "logo.ico"))
        )
        
        notification_message = (
            f'{lang._instance.get_string("babble.needUpdateOne")} '
            f'{appversion} '
            f'{lang._instance.get_string("babble.needUpdateTwo")} '
            f'{latestversion} '
            f'{lang._instance.get_string("babble.needUpdateThree")}!'
        )
        
        await self.notifier.send(
            title=lang._instance.get_string("babble.updatePresent"),
            message=notification_message,
            urgency=Urgency.Normal,
            buttons=[
                Button(
                    title=lang._instance.get_string("babble.downloadPage"),
                    on_pressed=lambda: webbrowser.open(page_url)
                )
            ],
            icon=logo,
            sound=DEFAULT_SOUND,
            on_dismissed=lambda: self.stop_event.set()
        )

    async def initialize(self):
        self.stop_event = asyncio.Event()
        self.loop = asyncio.get_running_loop()
        
        # Add non nt signal handlers
        if not os_type == 'Windows':
            self.loop.add_signal_handler(signal.SIGINT, self.stop_event.set)
            self.loop.add_signal_handler(signal.SIGTERM, self.stop_event.set)
