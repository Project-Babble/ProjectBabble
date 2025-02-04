from mjpeg.client import MJPEGClient
from time import sleep
import numpy as np
import cv2


url='http://192.168.1.186:8080/video'

# Create a new client thread
client = MJPEGClient(url)

# Allocate memory buffers for frames
bufs = client.request_buffers(65536, 50)
for b in bufs:
    client.enqueue_buffer(b)
    
# Start the client in a background thread
client.start()
while True:
    client.print_stats()
    buf = client.dequeue_buffer()
    client.enqueue_buffer(buf)
    data = memoryview(buf.data)[:buf.used]
    img_array = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        # Check if the frame was decoded correctly
    if frame is not None:
        cv2.imshow("MJPEG Stream", frame)
    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    #print(frame.shape)
    #print(len(array))
