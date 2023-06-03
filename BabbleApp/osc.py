
from pythonosc import udp_client
from pythonosc import osc_server
from pythonosc import dispatcher
from utils.misc_utils import PlaySound,SND_FILENAME,SND_ASYNC
import queue
import threading
from enum import IntEnum
import time
from config import BabbleConfig

class Tab(IntEnum):
    CAM = 0
    SETTINGS = 1
    ALGOSETTINGS = 2


def output_osc(array, self):
    location = self.config.gui_osc_location
    multi = self.config.gui_multiply
    self.client.send_message(location + "/cheekPuffLeft", array[0] * multi)
    self.client.send_message(location + "/cheekPuffRight", array[1] * multi)
    self.client.send_message(location + "/cheekSuckLeft", array[2] * multi)
    self.client.send_message(location + "/cheekSuckRight", array[3] * multi)
    self.client.send_message(location + "/jawOpen", array[4] * multi)
    self.client.send_message(location + "/jawForward", array[5] * multi)
    self.client.send_message(location + "/jawLeft", array[6] * multi)
    self.client.send_message(location + "/jawRight", array[7] * multi)
    self.client.send_message(location + "/noseSneerLeft", array[8] * multi)
    self.client.send_message(location + "/noseSneerRight", array[9] * multi)
    self.client.send_message(location + "/mouthFunnel", array[10] * multi)
    self.client.send_message(location + "/mouthPucker", array[11] * multi)
    self.client.send_message(location + "/mouthLeft", array[12] * multi)
    self.client.send_message(location + "/mouthRight", array[13] * multi)
    self.client.send_message(location + "/mouthRollUpper", array[14] * multi)
    self.client.send_message(location + "/mouthRollLower", array[15] * multi)
    self.client.send_message(location + "/mouthShrugUpper", array[16] * multi)
    self.client.send_message(location + "/mouthShrugLower", array[17] * multi)
    self.client.send_message(location + "/mouthClose", array[18] * multi)
    self.client.send_message(location + "/mouthSmileLeft", array[19] * multi)
    self.client.send_message(location + "/mouthSmileRight", array[20] * multi)
    self.client.send_message(location + "/mouthFrownLeft", array[21] * multi)
    self.client.send_message(location + "/mouthFrownRight", array[22] * multi)
    self.client.send_message(location + "/mouthDimpleLeft", array[23] * multi)
    self.client.send_message(location + "/mouthDimpleRight", array[24] * multi)
    self.client.send_message(location + "/mouthUpperUpLeft", array[25] * multi)
    self.client.send_message(location + "/mouthUpperUpRight", array[26] * multi)
    self.client.send_message(location + "/mouthLowerDownLeft", array[27] * multi)
    self.client.send_message(location + "/mouthLowerDownRight", array[28] * multi)
    self.client.send_message(location + "/mouthPressLeft", array[29] * multi)
    self.client.send_message(location + "/mouthPressRight", array[30] * multi)
    self.client.send_message(location + "/mouthStretchLeft", array[31] * multi)
    self.client.send_message(location + "/mouthStretchRight", array[32] * multi)
    self.client.send_message(location + "/tongueOut", array[33] * multi)
    self.client.send_message(location + "/tongueUp", array[34] * multi)
    self.client.send_message(location + "/tongueDown", array[35] * multi)
    self.client.send_message(location + "/tongueLeft", array[36] * multi)
    self.client.send_message(location + "/tongueRight", array[37] * multi)
    self.client.send_message(location + "/tongueRoll", array[38] * multi)
    self.client.send_message(location + "/tongueBendDown", array[39] * multi)
    self.client.send_message(location + "/tongueCurlUp", array[40] * multi)
    self.client.send_message(location + "/tongueSquish", array[41] * multi)
    self.client.send_message(location + "/tongueFlat", array[42] * multi)
    self.client.send_message(location + "/tongueTwistLeft", array[43] * multi)
    self.client.send_message(location + "/tongueTwistRight", array[44] * multi)

class VRChatOSC:
    # Use a tuple of blink (true, blinking, false, not), x, y for now. 
    def __init__(self, cancellation_event: threading.Event, msg_queue: queue.Queue[tuple[bool, int, int]], main_config: BabbleConfig,):
        self.main_config = main_config
        self.config = main_config.settings
        self.client = udp_client.SimpleUDPClient(self.config.gui_osc_address, int(self.config.gui_osc_port)) # use OSC port and address that was set in the config
        self.cancellation_event = cancellation_event
        self.msg_queue = msg_queue
        self.eye_id = Tab.CAM
        self.left_y = 621
        self.right_y = 621
        self.r_eye_x = 0
        self.l_eye_x = 0
        self.r_eye_blink = 0.7
        self.l_eye_blink = 0.7


    def run(self):
        start = time.time()
        last_blink = time.time()
        while True:
            if self.cancellation_event.is_set():
                print("\033[94m[INFO] Exiting OSC Queue\033[0m")
                return
            try:
                (self.eye_id, eye_info) = self.msg_queue.get(block=True, timeout=0.1)
            except:
                continue

            output_osc(eye_info.output, self)


class VRChatOSCReceiver:
    def __init__(self, cancellation_event: threading.Event, main_config: BabbleConfig, eyes: []):
        self.config = main_config.settings
        self.cancellation_event = cancellation_event
        self.dispatcher = dispatcher.Dispatcher()
        self.eyes = eyes  # we cant import CameraWidget so any type it is
        try:
            self.server = osc_server.OSCUDPServer((self.config.gui_osc_address, int(self.config.gui_osc_receiver_port)), self.dispatcher)
        except:
            print(f"\033[91m[ERROR] OSC Receive port: {self.config.gui_osc_receiver_port} occupied.\033[0m")

    def shutdown(self):
        print("\033[94m[INFO] Exiting OSC Receiver\033[0m")
        try:
            self.server.shutdown()
        except:
            pass

    def recenter_eyes(self, address, osc_value):
        if type(osc_value) != bool: return  # just incase we get anything other than bool
        if osc_value:
            for eye in self.eyes:
                eye.settings.gui_recenter_eyes = True

    def recalibrate_eyes(self, address, osc_value):
        if type(osc_value) != bool: return  # just incase we get anything other than bool
        if osc_value:
            for eye in self.eyes:
                eye.ransac.calibration_frame_counter = 300
                PlaySound('Audio/start.wav', SND_FILENAME | SND_ASYNC)

    def run(self):
        
        # bind what function to run when specified OSC message is received
        try:
            self.dispatcher.map(self.config.gui_osc_recalibrate_address, self.recalibrate_eyes)
            self.dispatcher.map(self.config.gui_osc_recenter_address, self.recenter_eyes)
            # start the server
            print("\033[92m[INFO] VRChatOSCReceiver serving on {}\033[0m".format(self.server.server_address))
            self.server.serve_forever()
            
        except:
            print(f"\033[91m[ERROR] OSC Receive port: {self.config.gui_osc_receiver_port} occupied.\033[0m")