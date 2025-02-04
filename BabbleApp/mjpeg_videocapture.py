import requests
import numpy as np
import cv2
import threading
import time
import queue

class MJPEGVideoCapture:
    def __init__(self, url, max_buffer_size=1024*1024):
        self.url = url
        self.session = requests.Session()
        self.stream = None
        self.byte_buffer = b""
        self.max_buffer_size = max_buffer_size  # Maximum allowed size for byte_buffer (e.g., 1 MB)
        self.running = False
        self.thread = None
        # Use a queue with maxsize=1 so that only the latest frame is kept.
        self.frame_queue = queue.Queue(maxsize=1)
        print("VC Opened")
    
    def open(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            # Allow some time for the update thread to start and capture a frame.
            time.sleep(2)
    
    def _update(self):
        while self.running:
            try:
                self.stream = self.session.get(self.url, stream=True, timeout=1)
                for chunk in self.stream.iter_content(chunk_size=512):
                    if not self.running:
                        break
                    self.byte_buffer += chunk

                    # Flush the buffer if it grows too large.
                    if len(self.byte_buffer) > self.max_buffer_size:
                        print("Warning: byte_buffer exceeded maximum size; flushing buffer.")
                        self.byte_buffer = b""
                        continue

                    # Instead of taking the first complete JPEG frame, we look for the latest complete one.
                    # Find the last occurrence of the JPEG start and end markers.
                    start = self.byte_buffer.rfind(b'\xff\xd8')
                    end = self.byte_buffer.rfind(b'\xff\xd9')
                    
                    # If a complete JPEG is found, extract it and flush the entire buffer.
                    if start != -1 and end != -1 and end > start:
                        jpg = self.byte_buffer[start:end+2]
                        self.byte_buffer = b""  # Discard all other data.
                        
                        image = np.frombuffer(jpg, dtype=np.uint8)
                        if image.size != 0:
                            # Decode as grayscale.
                            frame = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
                            if frame is not None:
                                # Resize to 240x240.
                                frame = cv2.resize(frame, (240, 240))
                                # Convert grayscale to 3-channel image with shape (240, 240, 3).
                                frame = np.stack([frame] * 3, axis=-1)
                                
                                # Try to put the frame into the queue.
                                # If the queue is full, remove the old frame first.
                                try:
                                    self.frame_queue.put(frame, block=False)
                                except queue.Full:
                                    try:
                                        self.frame_queue.get_nowait()
                                    except queue.Empty:
                                        pass
                                    self.frame_queue.put(frame, block=False)
            except requests.RequestException:
                # On failure, simply continue to try again.
                continue
    
    def read(self):
        """
        Block until a frame is available and return the latest frame.
        This mimics the blocking behavior of cap.read(), but always returns the latest frame.
        """
        frame = self.frame_queue.get()  # This call blocks until a frame is available.
        return True, frame.copy()
    
    def isOpened(self):
        return self.running
    
    def release(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.stream = None
        self.byte_buffer = b""
        self.session.close()

# Testing code:
test = True
if test:
    if __name__ == "__main__":
        cap = MJPEGVideoCapture("http://192.168.1.186:8080/video")
        cap.open()
        
        while cap.isOpened():
            ret, frame = cap.read()
            # Print the current byte_buffer length to monitor its size.
            print("Current byte_buffer length:", len(cap.byte_buffer))
            if ret:
                cv2.imshow("MJPEG Stream", frame)
            
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        
        cap.release()
        cv2.destroyAllWindows()
