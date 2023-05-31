import os
import json
os.environ["OMP_NUM_THREADS"] = "1"
import onnxruntime as ort
import time
import PySimpleGUI as sg
import cv2
from pythonosc import udp_client
from torchvision.transforms.functional import to_grayscale
import PIL.Image as Image
from torchvision import transforms
from threading import Thread


class WebcamVideoStream:
	def __init__(self, src=0):
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		(self.grabbed, self.frame) = self.stream.read()
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self
	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return
			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()
	def read(self):
		# return the frame most recently read
		return self.frame
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
                
class Calibration(object):  
    def __init__(self, filename):
         self.CALIBRATION_FILE = filename
         self._load_calibration(self.CALIBRATION_FILE)    

    def update_calib(self, filename):
        if self._last_update != os.stat(self.CALIBRATION_FILE).st_mtime:
             print("Change detected, reloading calibration file")
             self._load_calibration(filename)
             return True
        return False

    def _load_calibration(self, filename):   
        with open(filename) as user_file:       # Open and load the file into a dict 
            self.calib = json.load(user_file)
            self._last_update = os.fstat(user_file.fileno()).st_mtime
        self.jsonminmax = [
                [self.calib["cheekPuffLeft"]["min"],self.calib["cheekPuffLeft"]["max"]],                     # CheekPuff
                [self.calib["cheekPuffRight"]["min"],self.calib["cheekPuffRight"]["max"]],                     # CheekPuff
                [self.calib["cheekSuckLeft"]["min"],self.calib["cheekSuckLeft"]["max"]],                     # CheekPuff
                [self.calib["cheekSuckRight"]["min"],self.calib["cheekSuckRight"]["max"]],                     # CheekPuff
                [self.calib["jawOpen"]["min"],self.calib["jawOpen"]["max"]],                         # jawOpen
                [self.calib["jawForward"]["min"],self.calib["jawForward"]["max"]],                   # jawForward
                [self.calib["jawLeft"]["min"],self.calib["jawLeft"]["max"]],                         # jawLeft 
                [self.calib["jawRight"]["min"],self.calib["jawRight"]["max"]],                       # jawRight
                [self.calib["noseSneerLeft"]["min"],self.calib["noseSneerLeft"]["max"]],             # noseSneerLeft
                [self.calib["noseSneerRight"]["min"],self.calib["noseSneerRight"]["max"]],           # noseSneerRight
                [self.calib["mouthFunnel"]["min"],self.calib["mouthFunnel"]["max"]],                 # mouthFunnel      
                [self.calib["mouthPucker"]["min"],self.calib["mouthPucker"]["max"]],                 # mouthPucker
                [self.calib["mouthLeft"]["min"],self.calib["mouthLeft"]["max"]],                     # mouthLeft
                [self.calib["mouthRight"]["min"],self.calib["mouthRight"]["max"]],                   # mouthRight
                [self.calib["mouthRollUpper"]["min"],self.calib["mouthRollUpper"]["max"]],           # mouthRollUpper
                [self.calib["mouthRollLower"]["min"],self.calib["mouthRollLower"]["max"]],           # mouthRollLower
                [self.calib["mouthShrugUpper"]["min"],self.calib["mouthShrugUpper"]["max"]],         # mouthShrugUpper
                [self.calib["mouthShrugLower"]["min"],self.calib["mouthShrugLower"]["max"]],         # mouthShrugLower
                [self.calib["mouthClose"]["min"],self.calib["mouthClose"]["max"]],                   # mouthClose
                [self.calib["mouthSmileLeft"]["min"],self.calib["mouthSmileLeft"]["max"]],           # mouthSmileLeft
                [self.calib["mouthSmileRight"]["min"],self.calib["mouthSmileRight"]["max"]],         # mouthSmileRight
                [self.calib["mouthFrownLeft"]["min"],self.calib["mouthFrownLeft"]["max"]],           # mouthFrownLeft
                [self.calib["mouthSmileRight"]["min"],self.calib["mouthSmileRight"]["max"]],         # mouthFrownRight
                [self.calib["mouthDimpleLeft"]["min"],self.calib["mouthDimpleLeft"]["max"]],         # mouthDimpleLeft
                [self.calib["mouthDimpleRight"]["min"],self.calib["mouthDimpleRight"]["max"]],       # mouthDimpleRight
                [self.calib["mouthUpperUpLeft"]["min"],self.calib["mouthUpperUpLeft"]["max"]],       # mouthUpperUpLeft  
                [self.calib["mouthUpperUpRight"]["min"],self.calib["mouthUpperUpRight"]["max"]],     # mouthUpperUpRight
                [self.calib["mouthLowerDownLeft"]["min"],self.calib["mouthLowerDownLeft"]["max"]],   # mouthLowerDownLeft
                [self.calib["mouthLowerDownRight"]["min"],self.calib["mouthLowerDownRight"]["max"]], # mouthLowerDownRight
                [self.calib["mouthPressLeft"]["min"],self.calib["mouthPressLeft"]["max"]],           # mouthPressLeft
                [self.calib["mouthPressRight"]["min"],self.calib["mouthPressRight"]["max"]],         # mouthPressRight
                [self.calib["mouthStretchLeft"]["min"],self.calib["mouthStretchLeft"]["max"]],       # mouthStretchLeft
                [self.calib["mouthStretchRight"]["min"],self.calib["mouthStretchRight"]["max"]],     # mouthStretchRight
                [self.calib["tongueOut"]["min"],self.calib["tongueOut"]["max"]],                     # tongueOut
                [self.calib["tongueUp"]["min"],self.calib["tongueUp"]["max"]],                     # tongueOut
                [self.calib["tongueDown"]["min"],self.calib["tongueDown"]["max"]],                     # tongueOut
                [self.calib["tongueLeft"]["min"],self.calib["tongueLeft"]["max"]],                     # tongueOut
                [self.calib["tongueRight"]["min"],self.calib["tongueRight"]["max"]],                     # tongueOut
                [self.calib["tongueRoll"]["min"],self.calib["tongueRoll"]["max"]],                     # tongueOut
                [self.calib["tongueBendDown"]["min"],self.calib["tongueBendDown"]["max"]],                     # tongueOut
                [self.calib["tongueCurlUp"]["min"],self.calib["tongueCurlUp"]["max"]],                     # tongueOut
                [self.calib["tongueSquish"]["min"],self.calib["tongueSquish"]["max"]],                     # tongueOut
                [self.calib["tongueFlat"]["min"],self.calib["tongueFlat"]["max"]],                     # tongueOut
                [self.calib["tongueTwistLeft"]["min"],self.calib["tongueTwistLeft"]["max"]],                     # tongueOut
                [self.calib["tongueTwistRight"]["min"],self.calib["tongueTwistRight"]["max"]],                     # tongueOut
            ]
        return self.jsonminmax


def makeminmaxarray(amount):
    stored_values = []
    for i in range(amount):
        stored_values.append([0,0])
    return stored_values


def minmax(stored_values, value, passthrough = False):        # Set passthrough to true if you don't want to set the stored values wtih the function
    if passthrough == False:                                # Sets and updates the min and max value
        if stored_values[0] == 0 and stored_values[1] == 0:
            stored_values[0] = value
            stored_values[1] = value
            array = (0, max(min(value, 1), 0), 1)
        else:                                   # if value is greater than the max or less than the min, set it.
            if value < stored_values[0]: stored_values[0] = value
            if value > stored_values[1]: stored_values[1] = value
            array = (stored_values[0], max(min(value, 1), 0), stored_values[1])
    else: 
        array = stored_values                               # Formats the min max value without changing the values
        array = (stored_values[0], max(min(value, 1), 0), stored_values[1])
    return array

def normalize_value(array):
    normalized_value = ((array[1] - array[0]) / (array[2] - array[0]))
    return normalized_value

"""
Demo program that allows a user to type in a webcam url or number and displays it using OpenCV
"""

# ----------------  Create Form  ----------------
sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
layout = [
    [sg.Image(key = '-IMAGE-')],
    [sg.Text('Enter Webcam URL or Number (Defualts to 0)'), sg.Input(key = '-URL-', size = (30, 1))],
    [sg.Text('Enter Onnx model name (Defualts to EFV2300K45E57.onnx)'), sg.Input(key = '-MODEL-', size = (30, 1))],
    [sg.Text('OSC Location Address'), sg.Input(key = '-LOC-', size = (30, 1))],
    [sg.Text('Output Mutiplier (defualts to 1. Please use 100 if you are using the unity demo.)'), sg.Input(key = '-MULT-', size = (30, 1))],
    [sg.Text('Enter OSC IP (Defualts to 127.0.0.1)'), sg.Input(key = '-OSC-', size = (30, 1))],
    [sg.Text('Enter OSC Port (Defualts to 8888)'), sg.Input(key = '-PORT-', size = (30, 1))],
    [sg.Text('Enter Calibration file name (Defaults to calib.json)'), sg.Input(key = '-JSON_FILE-', size = (30, 1))],
    [sg.Text('Press Ok to start the webcam')],  
    [sg.Checkbox('Flip 180', key = '-FLIP180-')],
    [sg.Checkbox('Flip 90 Left', key = '-FLIP90-')],
    [sg.Checkbox('Flip 90 Right', key = '-FLIP90R-')],
    [sg.Checkbox('No Calibration', key = '-CAL-')],
    [sg.Checkbox('Use GPU (DirectML)', key = '-GPU-')],
    [sg.Button('Start'), sg.Button('Stop'), sg.Button('Draw ROI')],
]

# Create the Window
window = sg.Window('Project BabbleV1.0.3', layout, location = (800, 400))
event, values = window.read(timeout = 20)
calibjson = values['-MODEL-']

if calibjson == '':
     calibjson = 'calib.json'
calibration = Calibration(calibjson)
# ----------------  Event Loop  ----------------
while True:
    event, values = window.read(timeout = 20)
    OSCip= values['-OSC-'] #VR Chat OSC ip
    if OSCip == '':
        OSCip="127.0.0.1"
    OSCport= values['-PORT-'] #VR Chat OSC port
    if OSCport == '':
        OSCport = 8888
    else: 
        OSCport = int(OSCport)
    multi = values['-MULT-']
    if multi == '':
        multi = 1
    else:
        multi = int(multi)
    client = udp_client.SimpleUDPClient(OSCip, OSCport)
    model = values['-MODEL-']
    if model == '':
        model = 'EFV2300K45E57.onnx'
    if calibjson == '':
        calibjson = 'calib.json'
    usegpu = values['-GPU-']

    calibration.update_calib(calibjson)     # Checks and updates values of the json file
    stored_values = calibration.jsonminmax
    flip180 = values['-FLIP180-']
    flip90 = values['-FLIP90-']
    flip90r = values['-FLIP90R-']
    location = values['-LOC-']
    ROI = None
    if event == sg.WIN_CLOSED or event == 'Stop':
        break
    if event == 'Start':
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        if not usegpu:
            sess = ort.InferenceSession(model, opts, providers=['CPUExecutionProvider'])
        if usegpu:
            sess = ort.InferenceSession(model, opts, providers=['DmlExecutionProvider'])
        input_name = sess.get_inputs()[0].name
        output_name = sess.get_outputs()[0].name
        url = values['-URL-']
        if url == '':
            url = 0
        elif url in '0123456789':
            url = int(url)
        steamer = WebcamVideoStream(url).start()
        while True:
            frame = steamer.read()
            if event == 'Draw ROI':
                ROI = cv2.selectROI(frame)
                cv2.destroyWindow("ROI selector")
                cv2.waitKey(1)
            if ROI != None:
                frame = frame[int(ROI[1]):int(ROI[1]+ROI[3]), int(ROI[0]):int(ROI[0]+ROI[2])]
            if flip180:
                frame = cv2.flip(frame, 0)
            if flip90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            if flip90r:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame2 = frame
            #frame = cv2.flip(frame, 1)
            calibration.update_calib(calibjson)       # Checks and updates values of the json file
            stored_values = calibration.jsonminmax  
            frame = cv2.resize(frame, (256, 256))
            #make it pil
            frame = Image.fromarray(frame)
            #make it grayscale
            frame = to_grayscale(frame)
            #make it a tensor
            frame = transforms.ToTensor()(frame)
            #make it a batch
            frame = frame.unsqueeze(0)
            #make it a numpy array
            frame = frame.numpy()
            #print te amout of outputs that are zero
            out = sess.run([output_name], {input_name: frame})
            end = time.time()
            output = out[0]
            output = output[0]
            if values['-CAL-'] == False:
                array = []
                for i in range(len(output)):
                    yeah = minmax(stored_values[i], output[i], True)    # Enabled passthrough to allow changes to happen with calib json
                    value = normalize_value(yeah)
                    array.append(value)
            else:
                array = output
            for i in range(len(output)):            # Clip values between 0 - 1
                output[i] = max(min(output[i], 1), 0) 
            client.send_message(location + "/cheekPuffLeft", array[0] * multi)
            client.send_message(location + "/cheekPuffRight", array[1] * multi)
            client.send_message(location + "/cheekSuckLeft", array[2] * multi)
            client.send_message(location + "/cheekSuckRight", array[3] * multi)
            client.send_message(location + "/jawOpen", array[4] * multi)
            client.send_message(location + "/jawForward", array[5] * multi)
            client.send_message(location + "/jawLeft", array[6] * multi)
            client.send_message(location + "/jawRight", array[7] * multi)
            client.send_message(location + "/noseSneerLeft", array[8] * multi)
            client.send_message(location + "/noseSneerRight", array[9] * multi)
            client.send_message(location + "/mouthFunnel", array[10] * multi)
            client.send_message(location + "/mouthPucker", array[11] * multi)
            client.send_message(location + "/mouthLeft", array[12] * multi)
            client.send_message(location + "/mouthRight", array[13] * multi)
            client.send_message(location + "/mouthRollUpper", array[14] * multi)
            client.send_message(location + "/mouthRollLower", array[15] * multi)
            client.send_message(location + "/mouthShrugUpper", array[16] * multi)
            client.send_message(location + "/mouthShrugLower", array[17] * multi)
            client.send_message(location + "/mouthClose", output[18] * multi)
            client.send_message(location + "/mouthSmileLeft", array[19] * multi)
            client.send_message(location + "/mouthSmileRight", array[20] * multi)
            client.send_message(location + "/mouthFrownLeft", array[21] * multi)
            client.send_message(location + "/mouthFrownRight", array[22] * multi)
            client.send_message(location + "/mouthDimpleLeft", array[23] * multi)
            client.send_message(location + "/mouthDimpleRight", array[24] * multi)
            client.send_message(location + "/mouthUpperUpLeft", array[25] * multi)
            client.send_message(location + "/mouthUpperUpRight", array[26] * multi)
            client.send_message(location + "/mouthLowerDownLeft", array[27] * multi)
            client.send_message(location + "/mouthLowerDownRight", array[28] * multi)
            client.send_message(location + "/mouthPressLeft", array[29] * multi)
            client.send_message(location + "/mouthPressRight", array[30] * multi)
            client.send_message(location + "/mouthStretchLeft", array[31] * multi)
            client.send_message(location + "/mouthStretchRight", array[32] * multi)
            client.send_message(location + "/tongueOut", array[33] * multi)
            client.send_message(location + "/tongueUp", array[34] * multi)
            client.send_message(location + "/tongueDown", array[35] * multi)
            client.send_message(location + "/tongueLeft", array[36] * multi)
            client.send_message(location + "/tongueRight", array[37] * multi)
            client.send_message(location + "/tongueRoll", array[38] * multi)
            client.send_message(location + "/tongueBendDown", array[39] * multi)
            client.send_message(location + "/tongueCurlUp", array[40] * multi)
            client.send_message(location + "/tongueSquish", array[41] * multi)
            client.send_message(location + "/tongueFlat", array[42] * multi)
            client.send_message(location + "/tongueTwistLeft", array[43] * multi)
            client.send_message(location + "/tongueTwistRight", array[44] * multi)
            frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            imgbytes = cv2.imencode('.png', frame2)[1].tobytes()  # ditto
            window['-IMAGE-'].update(data=imgbytes)
            event, values = window.read(timeout = 20)
            if event == sg.WIN_CLOSED or event == 'Stop':
                break
        steamer.stop()
window.close()
