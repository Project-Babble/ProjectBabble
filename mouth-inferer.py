from imutils.video import VideoStream
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
import time
def nothing1(x):
    print(x)
def nothing2(y):
    print(y)
def nothing3(z):
    print(z)
def nothing4(y):
    print(y)	
# construct the argument parser and parse the arguments
# initialize dlib's face detector (HOG-based) and then load our
# trained shape predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("model_3.dat")
# initialize the video stream and allow the cammera sensor to warmup
print("[INFO] camera sensor warming up...")
vs = VideoStream(0).start()
#create a window
cv2.namedWindow('Frame')
cv2.createTrackbar('1','Frame',1,1000,nothing1)
cv2.createTrackbar('2','Frame',1,1000,nothing2)
cv2.createTrackbar('3','Frame',1,1000,nothing3)
cv2.createTrackbar('4','Frame',1,1000,nothing4)
# loop over the frames from the video stream
while True:
	a = 100
	b = 200
	c = 200
	d = 100	
	# grab the frame from the video stream, resize it to have a
	# maximum width of 400 pixels, and convert it to grayscale
	frame = vs.read()
	frame = imutils.resize(frame, width=400)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	rect = dlib.rectangle(int(cv2.getTrackbarPos('1','Frame')),int(cv2.getTrackbarPos('2','Frame')),int(cv2.getTrackbarPos('3','Frame')),int(cv2.getTrackbarPos('4','Frame'))) 
	(x, y, w, h) = face_utils.rect_to_bb(rect)
	cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
	start = time.time()
	shape = predictor(gray, rect)
	shape = face_utils.shape_to_np(shape)
	# loop over the (x, y)-coordinates from our dlib shape
	# predictor model draw them on the image 
	
	for (sX, sY) in shape:
		cv2.circle(frame, (sX, sY), 1, (0, 0, 255), -1)
	end = time.time()
	try:
		fps = 1/(end - start)
		cv2.putText(frame, "MODEL FPS: {:.2f}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
	except:
		pass
	cv2.imshow("Frame", frame)	#print fps
	key = cv2.waitKey(1) & 0xFF
	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()