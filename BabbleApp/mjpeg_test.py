import requests
import numpy as np
import cv2
import threading
import io

class MJPEGVideoCapture:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        self.stream = None
        self.byte_buffer = b""
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
    
    def open(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
    
    def _update(self):
        while self.running:
            try:
                self.stream = self.session.get(self.url, stream=True, timeout=3)
                for chunk in self.stream.iter_content(chunk_size=1024):
                    if not self.running:
                        break
                    self.byte_buffer += chunk
                    start = self.byte_buffer.find(b'\xff\xd8')  # JPEG start
                    end = self.byte_buffer.find(b'\xff\xd9')  # JPEG end
                    
                    if start != -1 and end != -1:
                        jpg = self.byte_buffer[start:end+2]
                        self.byte_buffer = self.byte_buffer[end+2:]
                        
                        image = np.frombuffer(jpg, dtype=np.uint8)
                        if image.size != 0:
                            frame = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
                            if frame is not None:
                                with self.lock:
                                    self.frame = frame
            except requests.RequestException:
                continue  # Retry on failure
    
    def read(self):
        with self.lock:
            return self.frame is not None, self.frame.copy() if self.frame is not None else None
    
    def isOpened(self):
        return self.running
    
    def release(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.stream = None
        self.frame = None
        self.byte_buffer = b""
        self.session.close()

if __name__ == "__main__":
    cap = MJPEGVideoCapture("http://openiristracker.local")
    cap.open()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            cv2.imshow("MJPEG Stream", frame)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    cap.release()
    cv2.destroyAllWindows()
