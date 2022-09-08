import mobilenetv2
import cv2 
import torch
import time
from pythonosc import udp_client
import multiprocessing as mp

OSCip="127.0.0.1" 
OSCport= 9000 #VR Chat OSC port
client = udp_client.SimpleUDPClient(OSCip, OSCport)



def vc():
    vc.height = 1
    vc.width = 1
    vc.roicheck = 1
vc()
#check if cuda is available
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("CUDA is available")
else:
    device = torch.device("cpu")
    thread = mp.cpu_count()
    
    torch.set_num_threads(int(thread/2))
    print("CUDA is not available")

#cheekPuff,cheekSquint_L,cheekSquint_R,noseSneer_L,noseSneer_R,jawOpen,jawForward,jawLeft,jawRight,mouthFunnel,mouthPucker,mouthLeft,mouthRight,mouthRollUpper,mouthRollLower,mouthShrugUpper,mouthShrugLower,mouthClose,mouthSmile_L,mouthSmile_R,mouthFrown_L,mouthFrown_R,mouthDimple_L,mouthDimple_R,mouthUpperUp_L,mouthUpperUp_R,mouthLowerDown_L,mouthLowerDown_R,mouthPress_L,mouthPress_R,mouthStretch_L,mouthStretch_R,tongueOut
classes = ["cheekPuff", "cheekSquint_L", "cheekSquint_R", "noseSneer_L", "noseSneer_R", "jawOpen", "jawForward", "jawLeft", "jawRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", "mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmile_L", "mouthSmile_R", "mouthFrown_L", "mouthFrown_R", "mouthDimple_L", "mouthDimple_R", "mouthUpperUp_L", "mouthUpperUp_R", "mouthLowerDown_L", "mouthLowerDown_R", "mouthPress_L", "mouthPress_R", "mouthStretch_L", "mouthStretch_R", "tongueOut"]   
model =  mobilenetv2.mobilenetv2().to(device)
model.load_state_dict(torch.load('BestTrainNeck1.pt',map_location=torch.device(device))

cap = cv2.VideoCapture(0)
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
    image = torch.from_numpy(image).to(device)
    image = image.float()
    start = time.time()
    output = model(image)
    end = time.time()
    #print fps
    print(1/(end-start))
    output = output.detach().cpu().numpy()
    #get the avatar/parameter/jawOpen'
    output = output[0]
    output = output.tolist()     
    #multiply by 100 
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
    #show the image
    cv2.imshow("image", gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
