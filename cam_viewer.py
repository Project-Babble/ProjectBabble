import cv2

cap = cv2.VideoCapture(0)
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 0)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 0)
cap.set(cv2.CAP_PROP_FPS, 120)

while cap.isOpened():
    yeah, img = cap.read()
    cv2.imshow('win', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
