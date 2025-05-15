import requests
import numpy as np
import cv2
import threading
import time


class MJPEGVideoCapture:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        self.stream = None
        self.byte_buffer = b""
        self.frame = None
        self.running = False
        self.frame_ready = False
        self.thread = None

    def open(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()

    def _update(self):
        while self.running:
            try:
                self.stream = self.session.get(self.url, stream=True, timeout=1)
                for chunk in self.stream.iter_content(chunk_size=1024):
                    if not self.running:
                        break
                    self.byte_buffer += chunk
                    # Process all available complete frames in the buffer
                    while True:
                        start = self.byte_buffer.find(b"\xff\xd8")  # JPEG start marker
                        end = self.byte_buffer.find(b"\xff\xd9")  # JPEG end marker
                        if start != -1 and end != -1:
                            jpg = self.byte_buffer[start : end + 2]
                            self.byte_buffer = self.byte_buffer[end + 2 :]

                            image = np.frombuffer(jpg, dtype=np.uint8)
                            if image.size != 0:
                                frame = cv2.imdecode(image, cv2.IMREAD_COLOR)
                                if frame is not None:
                                    self.frame = (
                                        frame  # Always update to the latest frame
                                    )
                                    self.frame_ready = True
                        else:
                            break
            except requests.RequestException:
                # If a network error occurs, wait briefly and retry
                time.sleep(0.1)
                continue

    def read(self):
        # Return whether a frame exists and its copy
        start = time.time()
        while True:
            if self.frame is not None and self.frame_ready:
                # time.sleep(self.sleep_time)
                self.frame_old = self.frame
                self.frame_ready = False
                return True, self.frame.copy()
            else:
                end = time.time()
                time.sleep(1 / 120)
                if end - start > 1:
                    return False, None

            # return False, None

    def isOpened(self):
        return self.running

    def isPrimed(self):
        if self.frame is not None:
            return True
        else:
            return False

    def release(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.stream = None
        self.frame = None
        self.byte_buffer = b""
        self.session.close()

    def get(self, item):
        pass
        return 1


if __name__ == "__main__":
    cap = MJPEGVideoCapture("http://openiristracker.local")
    cap.open()

    while cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            cv2.imshow("MJPEG Stream", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
