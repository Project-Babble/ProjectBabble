import os
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
                
def onesizefitsallminmaxarray():                # Some predefined ranges in stored values instead of the generated ones
    stored_values = [
        [0.2, 0.6],                   # CheekPuff
        [0, 1],                       # cheekSquintLeft
        [0, 1],                       # cheekSquintRight
        [0, 1],                       # noseSneerLeft
        [0, 1],                       # noseSneerRight
        [0.1, 0.8],                   # jawOpen
        [0.1, 0.8],                   # jawForward
        [0.05, 0.5],                  # jawLeft 
        [0.05, 0.5],                  # jawRight
        [0.1, 1],                     # mouthFunnel      
        [0.03, 0.7],                  # mouthPucker
        [0.05, 0.5],                  # mouthLeft
        [0.05, 0.5],                  # mouthRight
        [0, 0.3],                     # mouthRollUpper
        [0, 0.3],                     # mouthRollLower
        [0.03, 0.5],                  # mouthShrugUpper
        [0.03, 0.5],                  # mouthShrugLower
        [0, 0.3],                     # mouthClose
        [0.1, 1],                     # mouthSmileLeft
        [0.1, 1],                     # mouthSmileRight
        [0, 0.4],                     # mouthFrownLeft
        [0, 0.4],                     # mouthFrownRight
        [0, 1],                       # mouthDimpleLeft
        [0, 1],                       # mouthDimpleRight
        [0.02, 0.8],                  # mouthUpperUpLeft  
        [0.02, 0.8],                  # mouthUpperUpRight
        [0.02, 0.8],                  # mouthLowerDownLeft
        [0.02, 0.8],                  # mouthLowerDownRight
        [0, 1],                       # mouthPressLeft
        [0, 1],                       # mouthPressRight
        [0, 1],                       # mouthStretchLeft
        [0, 1],                       # mouthStretchRight
        [0.1, 0.8],                   # tongueOut
    ]
    return stored_values



def makeminmaxarray(amount):
    stored_values = []
    for i in range(amount):
        stored_values.append([0,0])
    return stored_values


def minmax(stored_values, value):
    if stored_values[0] == 0 and stored_values[1] == 0:
        stored_values[0] = value
        stored_values[1] = value
        array = (0, value, 1)
    else:
        if value < stored_values[0]: stored_values[0] = value
        if value > stored_values[1]: stored_values[1] = value
        array = (stored_values[0], value, stored_values[1])
    return array

def normalize_value(array):
    normalized_value = ((array[1] - array[0]) / (array[2] - array[0]))
    return normalized_value

stored_values = makeminmaxarray(33)
stored_values = onesizefitsallminmaxarray()



"""
Demo program that allows a user to type in a webcam url or number and displays it using OpenCV
"""

# ----------------  Create Form  ----------------
sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
layout = [
    [sg.Image(key = '-IMAGE-')],
    [sg.Text('Enter Webcam URL or Number (Defualts to 0)'), sg.Input(key = '-URL-', size = (30, 1))],
    [sg.Text('Enter Onnx model name (Defualts to v1.onnx)'), sg.Input(key = '-MODEL-', size = (30, 1))],
    [sg.Text('OSC Location Address'), sg.Input(key = '-LOC-', size = (30, 1))],
    [sg.Text('Output Mutiplier (defualts to 1. Please use 100 if you are using the unity demo.)'), sg.Input(key = '-MULT-', size = (30, 1))],
    [sg.Text('Enter OSC IP (Defualts to 127.0.0.1)'), sg.Input(key = '-OSC-', size = (30, 1))],
    [sg.Text('Enter OSC Port (Defualts to 9000)'), sg.Input(key = '-PORT-', size = (30, 1))],
    [sg.Text('Press Ok to start the webcam')],  
    [sg.Checkbox('Flip 180', key = '-FLIP180-')],
    [sg.Checkbox('Flip 90 Left', key = '-FLIP90-')],
    [sg.Checkbox('Flip 90 Right', key = '-FLIP90R-')],
    [sg.Checkbox('No Calibration', key = '-CAL-')],
    [sg.Button('Start'), sg.Button('Stop'), sg.Button('Draw ROI')],
]

# Create the Window
window = sg.Window('Project BabbleV1.0', layout, location = (800, 400))
# ----------------  Event Loop  ----------------
while True:
    event, values = window.read(timeout = 20)
    OSCip= values['-OSC-'] #VR Chat OSC ip
    if OSCip == '':
        OSCip="127.0.0.1"
    OSCport= values['-PORT-'] #VR Chat OSC port
    if OSCport == '':
        OSCport = 9000
    multi = values['-MULT-']
    if multi == '':
        multi = 1
    else:
        multi = int(multi)
    client = udp_client.SimpleUDPClient(OSCip, OSCport)
    model = values['-MODEL-']
    if model == '':
        model = 'v1.onnx'
    flip180 = values['-FLIP180-']
    flip90 = values['-FLIP90-']
    flip90r = values['-FLIP90R-']
    location = values['-LOC-']
    ROI = None
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
    input_name = sess.get_inputs()[0].name
    output_name = sess.get_outputs()[0].name
    if event == sg.WIN_CLOSED or event == 'Stop':
        break
    if event == 'Start':
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
                    yeah = minmax(stored_values[i], output[i])
                    value = normalize_value(yeah)
                    array.append(value)
            else:
                array = output
            client.send_message(location + "/cheekPuff", array[0] * multi)
            client.send_message(location + "/cheekSquintLeft", output[1] * multi)
            client.send_message(location + "/cheekSquintRight", output[2] * multi)
            client.send_message(location + "/noseSneerLeft", output[3] * multi)
            client.send_message(location + "/noseSneerRight", output[4] * multi)
            client.send_message(location + "/jawOpen", array[5] * multi)
            client.send_message(location + "/jawForward", array[6] * multi)
            client.send_message(location + "/jawLeft", array[7] * multi)
            client.send_message(location + "/jawRight", array[8] * multi)
            client.send_message(location + "/mouthFunnel", array[9] * multi)
            client.send_message(location + "/mouthPucker", array[10] * multi)
            client.send_message(location + "/mouthLeft", array[11] * multi)
            client.send_message(location + "/mouthRight", array[12] * multi)
            client.send_message(location + "/mouthRollUpper", array[13] * multi)
            client.send_message(location + "/mouthRollLower", array[14] * multi)
            client.send_message(location + "/mouthShrugUpper", array[15] * multi)
            client.send_message(location + "/mouthShrugLower", array[16] * multi)
            client.send_message(location + "/mouthClose", output[17] * multi)
            client.send_message(location + "/mouthSmileLeft", array[18] * multi)
            client.send_message(location + "/mouthSmileRight", array[19] * multi)
            client.send_message(location + "/mouthFrownLeft", array[20] * multi)
            client.send_message(location + "/mouthFrownRight", array[21] * multi)
            client.send_message(location + "/mouthDimpleLeft", array[22] * multi)
            client.send_message(location + "/mouthDimpleRight", array[23] * multi)
            client.send_message(location + "/mouthUpperUpLeft", array[24] * multi)
            client.send_message(location + "/mouthUpperUpRight", array[25] * multi)
            client.send_message(location + "/mouthLowerDownLeft", array[26] * multi)
            client.send_message(location + "/mouthLowerDownRight", array[27] * multi)
            client.send_message(location + "/mouthPressLeft", array[28] * multi)
            client.send_message(location + "/mouthPressRight", array[29] * multi)
            client.send_message(location + "/mouthStretchLeft", array[30] * multi)
            client.send_message(location + "/mouthStretchRight", array[31] * multi)
            client.send_message(location + "/tongueOut", array[32] * multi)
            imgbytes = cv2.imencode('.png', frame2)[1].tobytes()  # ditto
            window['-IMAGE-'].update(data=imgbytes)
            event, values = window.read(timeout = 20)
            if event == sg.WIN_CLOSED or event == 'Stop':
                break
        steamer.stop()
window.close()
