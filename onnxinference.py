import onnx 
import torch
import onnxruntime as ort
import numpy as np
import cv2
import time
from pythonosc import udp_client

OSCip="127.0.0.1" 
OSCport= 9000 #VR Chat OSC port
client = udp_client.SimpleUDPClient(OSCip, OSCport)

classes = ["cheekPuff", "cheekSquint_L", "cheekSquint_R", "noseSneer_L", "noseSneer_R", "jawOpen", "jawForward", "jawLeft", "jawRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", "mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmile_L", "mouthSmile_R", "mouthFrown_L", "mouthFrown_R", "mouthDimple_L", "mouthDimple_R", "mouthUpperUp_L", "mouthUpperUp_R", "mouthLowerDown_L", "mouthLowerDown_R", "mouthPress_L", "mouthPress_R", "mouthStretch_L", "mouthStretch_R", "tongueOut"]   

cap = cv2.VideoCapture(0)
sessionOptions = ort.SessionOptions()
ort_sess = ort.InferenceSession("modelv2.2.onnx", providers = ['CPUExecutionProvider'])
while True:
    #read the frame
    ret, frame = cap.read()
    #convert the frame to gr ayscale
    frame = cv2.resize(frame, (100,100))
    #remove 10 pixels from the top
    frame = frame[10:,:,:]
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (100,100))
    gray = cv2.GaussianBlur(img, (3, 3), 0)
    image = gray.reshape(1,1, 100, 100)
    image = torch.from_numpy(image).float()
    #make numpy array
    image = image.numpy()
    outputs = ort_sess.run(None, {'input': image})
    end = time.time()
    output = outputs[0][0]
    output = output.tolist()
    print(output[0])
    output = [x * 100 for x in output]
    client.send_message("/cheekPuff", output[0])
    client.send_message("/cheekSquintLeft", output[1])
    client.send_message("/cheekSquintRight", output[2])
    client.send_message("/noseSneerLeft", output[3])
    client.send_message("/noseSneerRight", output[4])
    client.send_message("/jawOpen", output[5])
    client.send_message("/jawForward", output[6])
    client.send_message("/jawLeft", output[7])
    client.send_message("/jawRight", output[8])
    client.send_message("/mouthFunnel", output[9])
    client.send_message("/mouthPucker", output[10])
    client.send_message("/mouthLeft", output[11])
    client.send_message("/mouthRight", output[12])
    client.send_message("/mouthRollUpper", output[13])
    client.send_message("/mouthRollLower", output[14])
    client.send_message("/mouthShrugUpper", output[15])
    client.send_message("/mouthShrugLower", output[16])
    client.send_message("/mouthClose", output[17])
    client.send_message("/mouthSmileLeft", output[18])
    client.send_message("/mouthSmileRight", output[19])
    client.send_message("/mouthFrownLeft", output[20])
    client.send_message("/mouthFrownRight", output[21])
    client.send_message("/mouthDimpleLeft", output[22])
    client.send_message("/mouthDimpleRight", output[23])
    client.send_message("/mouthUpperUpLeft", output[24])
    client.send_message("/mouthUpperUpRight", output[25])
    client.send_message("/mouthLowerDownLeft", output[26])
    client.send_message("/mouthLowerDownRight", output[27])
    client.send_message("/mouthPressLeft", output[28])
    client.send_message("/mouthPressRight", output[29])
    client.send_message("/mouthStretchLeft", output[30])
    client.send_message("/mouthStretchRight", output[31])
    client.send_message("/tongueOut", output[32])
    #show image
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()