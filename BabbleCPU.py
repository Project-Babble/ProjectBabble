import os
import json

os.environ["OMP_NUM_THREADS"] = "1"
import onnxruntime as ort
import time
import PySimpleGUI as sg
import cv2
from osc import *
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
       # if self._last_update != os.stat(self.CALIBRATION_FILE).st_mtime:
             print("Change detected, reloading calibration file")
             self._load_calibration(filename)
             return True
        #return False

    def _load_calibration(self, filename):   
        with open(filename) as user_file:       # Open and load the file into a dict 
            self.calib = json.load(user_file)
            self._last_update = os.fstat(user_file.fileno()).st_mtime
        self.jsonminmax = [
                [self.calib["cheekPuff"]["min"],self.calib["cheekPuff"]["max"]],                     # CheekPuff
                [self.calib["cheekSquintLeft"]["min"],self.calib["cheekSquintLeft"]["max"]],         # cheekSquintLeft
                [self.calib["cheekSquintRight"]["min"],self.calib["cheekSquintRight"]["max"]],       # cheekSquintRight
                [self.calib["noseSneerLeft"]["min"],self.calib["noseSneerLeft"]["max"]],             # noseSneerLeft
                [self.calib["noseSneerRight"]["min"],self.calib["noseSneerRight"]["max"]],           # noseSneerRight
                [self.calib["jawOpen"]["min"],self.calib["jawOpen"]["max"]],                         # jawOpen
                [self.calib["jawForward"]["min"],self.calib["jawForward"]["max"]],                   # jawForward
                [self.calib["jawLeft"]["min"],self.calib["jawLeft"]["max"]],                         # jawLeft 
                [self.calib["jawRight"]["min"],self.calib["jawRight"]["max"]],                       # jawRight
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
            ]
        return self.jsonminmax
    
        
         
                
def onesizefitsallminmaxarray():                # Some predefined ranges in stored values instead of the generated ones
    stored_values = [
        [0.2, 0.6],                   # CheekPuff
        [0, 1],                       # cheekSquintLeft
        [0, 1],                       # cheekSquintRight
        [0, 1],                       # noseSneerLeft
        [0, 1],                       # noseSneerRight
        [0.03, 0.6],                  # jawOpen
        [0.1, 0.8],                   # jawForward
        [0.05, 0.5],                  # jawLeft 
        [0.05, 0.5],                  # jawRight
        [0.1, 0.6],                   # mouthFunnel      
        [0.4, 1],                     # mouthPucker
        [0.05, 0.5],                  # mouthLeft
        [0.05, 0.5],                  # mouthRight
        [0, 0.5],                     # mouthRollUpper
        [0, 0.3],                     # mouthRollLower
        [0.03, 0.5],                  # mouthShrugUpper
        [0.03, 0.5],                  # mouthShrugLower
        [0, 0.5],                     # mouthClose
        [0.1, 1],                     # mouthSmileLeft
        [0.1, 1],                     # mouthSmileRight
        [0, 0.6],                     # mouthFrownLeft
        [0, 0.6],                     # mouthFrownRight
        [0, 1],                       # mouthDimpleLeft
        [0, 1],                       # mouthDimpleRight
        [0.02, 0.8],                  # mouthUpperUpLeft  
        [0.02, 0.8],                  # mouthUpperUpRight
        [0.02, 0.8],                  # mouthLowerDownLeft
        [0.02, 0.8],                  # mouthLowerDownRight
        [0, 1],                       # mouthPressLeft
        [0, 1],                       # mouthPressRight
        [0.3, 1],                     # mouthStretchLeft
        [0.3, 1],                     # mouthStretchRight
        [0.2, 0.8],                   # tongueOut
    ]
    return stored_values



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
            array = (0, value, 1)
        else:                                   # if value is greater than the max or less than the min, set it.
            if value < stored_values[0]: stored_values[0] = value
            if value > stored_values[1]: stored_values[1] = value
            array = (stored_values[0], value, stored_values[1])
    else: 
        array = stored_values                               # Formats the min max value without changing the values
        array = (stored_values[0], value, stored_values[1])
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

model = 'v1.1B0.onnx'
OSCip ="127.0.0.1"
OSCport = 9000
multi = 1

layout = [
    [sg.Image(key = '-IMAGE-')], #I just hardcoded default values here.. they should be stored in a class variable list.
    [sg.Text('Enter Webcam URL or Number'), sg.Input("0", key = '-URL-', size = (2, 1))],
    [sg.Text('Enter Onnx model name (Defualt v1.1B0.onnx)'), sg.Input("v1.1B0.onnx", key = '-MODEL-', size = (30, 1))],
    [sg.Text('OSC Location Address'), sg.Input(key = '-LOC-', size = (30, 1))],
    [sg.Text('Output Mutiplier (Defualt 1. Use 100 if you are using the Unity demo.)'), sg.Input("1", key = '-MULT-', size = (30, 1))],
    [sg.Text('Enter OSC IP (Defualt 127.0.0.1)'), sg.Input("127.0.0.1", key = '-OSC-', size = (15, 1))],
    [sg.Text('Enter OSC Port (Defualt 9000)'), sg.Input("9000",key = '-PORT-', size = (10, 1))],
    [sg.Button('Save')],
    [sg.Text('Press Ok to start the webcam')],  
    [sg.Checkbox('Flip 180', key = '-FLIP180-'),
    sg.Checkbox('Flip 90 Left', key = '-FLIP90-'),
    sg.Checkbox('Flip 90 Right', key = '-FLIP90R-')],
    [sg.Checkbox('No Calibration', key = '-CAL-')],
    [sg.Button('Start'), sg.Button('Stop'), sg.Button('Draw ROI')],
]

# Create the Window
window = sg.Window('Project BabbleV1.1', layout, location = (800, 400))
event, values = window.read(timeout = 20)
calibjson = values['-MODEL-']


calibjson = 'calib.json'
calibration = Calibration(calibjson)
# ----------------  Event Loop  ----------------
while True:
    event, values = window.read(timeout = 20)

    if event == "Save":
         #this whole block of stuff in this iff could be re-written tbh...
        OSCip = values['-OSC-'] #VR Chat OSC ip
        if OSCip == '':
            OSCip ="127.0.0.1"
        OSCport = values['-PORT-'] #VR Chat OSC port
        if OSCport == '':
            OSCport = 9000
        OSC.set_osc(OSCip, OSCport)
        multi = values['-MULT-']
        if multi == '':
            multi = 1
        else:
            multi = int(multi)
        if model == '':
            model = 'v1.1B0.onnx'
        model = values['-MODEL-']
        calibration.update_calib(calibjson)       # Checks and updates values of the json file


  #  calibration.update_calib(calibjson)     # Checks and updates values of the json file
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
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        sess = ort.InferenceSession(model, opts, providers=['CPUExecutionProvider'])
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
            output = [0 if x < 0 else x for x in output]
            if values['-CAL-'] == False:
                array = []
                for i in range(len(output)):
                    yeah = minmax(stored_values[i], output[i], True)    # Enabled passthrough to allow changes to happen with calib json
                    value = normalize_value(yeah)
                    array.append(value)
            else:
                array = output

            OSC.send_osc(array, multi, location)

            imgbytes = cv2.imencode('.png', frame2)[1].tobytes()  # ditto
            window['-IMAGE-'].update(data=imgbytes)
            event, values = window.read(timeout = 20)
            if event == sg.WIN_CLOSED or event == 'Stop':
                break
        steamer.stop()
window.close()
