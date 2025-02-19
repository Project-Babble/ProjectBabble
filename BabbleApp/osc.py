from pythonosc import udp_client, osc_server, dispatcher
from utils.misc_utils import playSound
import queue
import threading
from enum import IntEnum
import time
from config import BabbleConfig
import traceback
import math
import os
from lang_manager import LocaleStringManager as lang

class Tab(IntEnum):
    CAM = 0
    SETTINGS = 1
    ALGOSETTINGS = 2
    CALIBRATION = 3

import numpy as np

def delay_output_osc(array, delay_seconds, self):
    time.sleep(delay_seconds)
    output_osc(array, self)

def output_osc(array, self):
    location = self.config.gui_osc_location
    multi = self.config.gui_multiply

    max_clip_value = 10 ** math.floor(math.log10(multi))
    # Apply the multiplier and then clip the values between 0 and 1
    clipped_array = np.clip(array * multi, 0, max_clip_value)
    self.client.send_message(location + "/cheekPuffLeft", clipped_array[0])
    self.client.send_message(location + "/cheekPuffRight", clipped_array[1])
    self.client.send_message(location + "/cheekSuckLeft", clipped_array[2])
    self.client.send_message(location + "/cheekSuckRight", clipped_array[3])
    self.client.send_message(location + "/jawOpen", clipped_array[4])
    self.client.send_message(location + "/jawForward", clipped_array[5])
    self.client.send_message(location + "/jawLeft", clipped_array[6])
    self.client.send_message(location + "/jawRight", clipped_array[7])
    self.client.send_message(location + "/noseSneerLeft", clipped_array[8])
    self.client.send_message(location + "/noseSneerRight", clipped_array[9])
    self.client.send_message(location + "/mouthFunnel", clipped_array[10])
    self.client.send_message(location + "/mouthPucker", clipped_array[11])
    self.client.send_message(location + "/mouthLeft", clipped_array[12])
    self.client.send_message(location + "/mouthRight", clipped_array[13])
    self.client.send_message(location + "/mouthRollUpper", clipped_array[14])
    self.client.send_message(location + "/mouthRollLower", clipped_array[15])
    self.client.send_message(location + "/mouthShrugUpper", clipped_array[16])
    self.client.send_message(location + "/mouthShrugLower", clipped_array[17])
    self.client.send_message(location + "/mouthClose", clipped_array[18])
    self.client.send_message(location + "/mouthSmileLeft", clipped_array[19])
    self.client.send_message(location + "/mouthSmileRight", clipped_array[20])
    self.client.send_message(location + "/mouthFrownLeft", clipped_array[21])
    self.client.send_message(location + "/mouthFrownRight", clipped_array[22])
    self.client.send_message(location + "/mouthDimpleLeft", clipped_array[23])
    self.client.send_message(location + "/mouthDimpleRight", clipped_array[24])
    self.client.send_message(location + "/mouthUpperUpLeft", clipped_array[25])
    self.client.send_message(location + "/mouthUpperUpRight", clipped_array[26])
    self.client.send_message(location + "/mouthLowerDownLeft", clipped_array[27])
    self.client.send_message(location + "/mouthLowerDownRight", clipped_array[28])
    self.client.send_message(location + "/mouthPressLeft", clipped_array[29])
    self.client.send_message(location + "/mouthPressRight", clipped_array[30])
    self.client.send_message(location + "/mouthStretchLeft", clipped_array[31])
    self.client.send_message(location + "/mouthStretchRight", clipped_array[32])
    self.client.send_message(location + "/tongueOut", clipped_array[33])
    self.client.send_message(location + "/tongueUp", clipped_array[34])
    self.client.send_message(location + "/tongueDown", clipped_array[35])
    self.client.send_message(location + "/tongueLeft", clipped_array[36])
    self.client.send_message(location + "/tongueRight", clipped_array[37])
    self.client.send_message(location + "/tongueRoll", clipped_array[38])
    self.client.send_message(location + "/tongueBendDown", clipped_array[39])
    self.client.send_message(location + "/tongueCurlUp", clipped_array[40])
    self.client.send_message(location + "/tongueSquish", clipped_array[41])
    self.client.send_message(location + "/tongueFlat", clipped_array[42])
    self.client.send_message(location + "/tongueTwistLeft", clipped_array[43])
    self.client.send_message(location + "/tongueTwistRight", clipped_array[44])


class VRChatOSC:
    # Use a tuple of blink (true, blinking, false, not), x, y for now.
    def __init__(
        self,
        cancellation_event: threading.Event,
        msg_queue: queue.Queue[tuple[bool, int, int]],
        main_config: BabbleConfig,
    ):
        self.main_config = main_config
        self.config = main_config.settings
        self.client = udp_client.SimpleUDPClient(
            self.config.gui_osc_address, int(self.config.gui_osc_port)
        )  # use OSC port and address that was set in the config
        self.cancellation_event = cancellation_event
        self.msg_queue = msg_queue
        self.cam = Tab.CAM

    def run(self):
        while True:
            if self.cancellation_event.is_set():
                print(
                    f'\033[94m[{lang._instance.get_string("log.info")}] Exiting OSC Queue\033[0m'
                )
                return
            try:
                (self.cam_id, cam_info) = self.msg_queue.get(block=True, timeout=0.1)
            except TypeError:
                continue
            except queue.Empty:
                continue

            # If the delay setting is enabled, make a new thread and delay the outputs.
            delay_enable = self.config.gui_osc_delay_enable
            delay_seconds = self.config.gui_osc_delay_seconds
            if delay_enable:
                threading.Thread(target=delay_output_osc, args=(cam_info.output, delay_seconds, self)).start() 
            else:
                output_osc(cam_info.output, self)


class VRChatOSCReceiver:
    def __init__(
        self, cancellation_event: threading.Event, main_config: BabbleConfig, cams: []
    ):
        self.config = main_config.settings
        self.cancellation_event = cancellation_event
        self.dispatcher = dispatcher.Dispatcher()
        self.cams = cams  # we cant import CameraWidget so any type it is
        print("OSC_INIT")
        try:
            self.server = osc_server.OSCUDPServer(
                (self.config.gui_osc_address, int(self.config.gui_osc_receiver_port)),
                self.dispatcher,
            )
        except:
            print(
                f'\033[91m[{lang._instance.get_string("log.error")}] OSC Receive port: {self.config.gui_osc_receiver_port} occupied.\033[0m'
            )

    def shutdown(self):
        print(
            f'\033[94m[{lang._instance.get_string("log.info")}] Exiting OSC Receiver\033[0m'
        )
        try:
            self.server.shutdown()
        except:
            pass

    def recalibrate_mouth(self, address, osc_value):
        if not isinstance(osc_value, bool):
            return  # just incase we get anything other than bool
        if osc_value:
            for cam in self.cams:
                cam.babble_cnn.calibration_frame_counter = 300
                playSound(os.path.join("Audio", "start.wav"))

    def run(self):

        # bind what function to run when specified OSC message is received
        try:
            self.dispatcher.map(
                self.config.gui_osc_recalibrate_address, self.recalibrate_mouth
            )
            # start the server
            print(
                f'\033[92m[{lang._instance.get_string("log.info")}] VRChatOSCReceiver serving on {self.server.server_address}\033[0m'
            )
            self.server.serve_forever()

        except:
            traceback.print_exc()
            print(
                f'\033[91m[{lang._instance.get_string("log.error")}] OSC Receive port: {self.config.gui_osc_receiver_port} occupied.\033[0m'
            )
