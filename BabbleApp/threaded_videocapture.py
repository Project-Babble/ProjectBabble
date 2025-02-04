import cv2
import threading
import concurrent.futures
import time

def read_frame(cap):
    return cap.read()

class VideoCaptureThread:
    def __init__(self, stream_url, timeout=5):
        self.stream_url = stream_url
        self.timeout = timeout
        self.cap = cv2.VideoCapture(self.stream_url)
        self.frame = None
        self.ret = None
        self.running = True
        self.lock = threading.Lock()
        self.new_frame_available = threading.Condition(self.lock)
        self.thread = self.start_thread()

    def start_thread(self):
        thread = threading.Thread(target=self.update, daemon=True)
        thread.start()
        return thread

    def update(self):
        self.cap = cv2.VideoCapture(self.stream_url)
        while self.running:
            try:
                if self.cap.isOpened():
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(read_frame, self.cap)
                        try:
                            readframe = future.result(timeout=self.timeout)  # Wait for result with timeout
                            ret, frame = readframe
                        except concurrent.futures.TimeoutError:
                            print("Timeout: cap.read() took too long!")
                            self.reconnect()
                            self.thread = self.start_thread()  # Restart the thread
                            ret, frame = False, None
                    if ret:
                        with self.lock:
                            self.ret = ret
                            self.frame = frame
                            self.new_frame_available.notify_all()  # Notify waiting threads
                    else:
                        print("Frame read failed. Attempting reconnect...")
                        self.reconnect()
                time.sleep(0.01)  # Small delay to prevent 100% CPU usage
            except Exception as e:
                print(f"Unexpected error in update thread: {e}")
                self.reconnect()
                self.thread = self.start_thread()  # Restart the thread
                break  # Exit the loop to allow the new thread to take over

    def get_fps(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return fps if fps > 0 else 30  # Default to 30 FPS if unknown

    def read(self):
        """Blocks until a new frame is available or times out."""
        start_time = time.time()
        with self.lock:
            while self.frame is None:
                elapsed_time = time.time() - start_time
                if elapsed_time >= self.timeout:
                    print("Timeout: No frame received in time. Restarting capture...")
                    self.reconnect()
                    return None, None  # Return None if timeout occurs
                
                # Wait with a short timeout to allow the background thread to update the frame
                self.new_frame_available.wait(timeout=0.1)
            
            # Return the frame if available
            time.sleep(1/60)
            return self.ret, self.frame
        
    def set(self, kw, val):
        self.cap.set(kw, val)
        
    def get(self, kw):
        return self.cap.get(kw)

    def isOpened(self):
        return self.cap.isOpened()

    def reconnect(self):
        """Safely restarts the video capture."""
        self.cap.release()
        time.sleep(2)  # Small delay to allow a clean reconnect
        self.cap = cv2.VideoCapture(self.stream_url)
        print("Capture restarted.")

    def release(self):
        self.running = False
        self.thread.join()
        self.cap.release()