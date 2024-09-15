"""
MIT License

Copyright DragonDreams GmbH 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import multiprocessing.queues
import multiprocessing
import queue as pqueue
import traceback
import platform
import logging
from struct import pack, unpack
import cv2
import numpy as np
from vivefacialtracker.camera import FTCamera
from vivefacialtracker.vivetracker import ViveTracker


class FTCameraController:
    """Opens a camera grabbing frames as numpy arrays."""

    _logger = logging.getLogger("evcta.FTCameraController")

    def __init__(self: 'FTCameraController', index: int) -> None:
        """Create camera grabber.

        The camera is not yet opened. Set "callback_frame" then call
        "open()" to open the device and "start_read()" to start capturing.

        Keyword arguments:
        index -- Index of the camera. Under Linux this uses the device
                 file "/dev/video{index}".
        """
        self._index: int = index
        self._proc_read: multiprocessing.Process = None
        self._proc_queue: multiprocessing.queues.Queue = None

    def close(self: 'FTCameraController') -> None:
        """Closes the device if open.

        If capturing stops capturing first.
        """
        FTCameraController._logger.info("FTCameraController.close: index {}".format(self._index))
        self._stop_read()

    def open(self: 'FTCameraController') -> None:
        """Start capturing frames if not capturing and device is open."""
        if self._proc_read is not None:
            return

        FTCameraController._logger.info("FTCameraController.open: start process")
        self._proc_queue = multiprocessing.Queue(maxsize=1)
        self._proc_read = multiprocessing.Process(target=self._read_process, args=(self._proc_queue,))
        self._proc_read.start()

    def _reopen(self: 'FTCameraController') -> None:
        FTCameraController._logger.info("FTCameraController._reopen")
        self.close()
        self.open()

    def get_image(self: 'FTCameraController') -> np.ndarray:
        """Get next image or None."""
        try:
            frame = self._proc_queue.get(True, 1)
            shape = unpack('HHH', frame[0:6])
            image = np.frombuffer(frame[6:], dtype=np.uint8).reshape(shape)
            return image
        except pqueue.Empty:
            FTCameraController._logger.info("FTCameraController.get_image: timeout, reopen device")
            self._reopen()
            return None
        except Exception:
            FTCameraController._logger.exception(
                "FTCameraController.get_image: Failed getting image")
            print(traceback.format_exc())
            return None

    def _stop_read(self: 'FTCameraController') -> None:
        """Stop capturing frames if capturing."""
        if self._proc_read is None:
            return
        FTCameraController._logger.info("FTCameraController._stop_read: Linux: stop process")
        self._proc_read.terminate()  # sends a SIGTERM
        self._proc_read.join(1)

        if self._proc_read.exitcode is not None:
            FTCameraController._logger.info(
                "FTCameraController.stop_read: Linux: process terminated")
        else:
            FTCameraController._logger.info(
                "FTCameraController._stop_read: Linux: process not responding, killing it")
            self._proc_read.kill()  # sends a SIGKILL
            self._proc_read.join(1)
            FTCameraController._logger.info(
                "FTCameraController._stop_read: Linux: process killed")
        self._proc_read = None

    def _read_process(self: 'FTCameraController',
                      queue: multiprocessing.connection.Connection) -> None:
        FTCameraController._logger.info("FTCameraController._read_process: ENTER")
        class Helper(FTCamera.Processor):
            """Helper."""
            def __init__(self: 'FTCameraController.Helper',
                         queue: multiprocessing.connection.Connection) -> None:
                self.camera: FTCamera = None
                self.tracker: ViveTracker = None
                self._queue = queue

            def open_camera(self: 'FTCameraController.Helper', index: int,
                            queue: multiprocessing.connection.Connection) -> None:
                """Open camera."""
                self.camera = FTCamera(index)
                self.camera.terminator = FTCamera.Terminator()
                self.camera.processor = self
                self.camera.queue = queue
                self.camera.open()

            def open_tracker(self: 'FTCameraController.Helper') -> None:
                """Open tracker."""
                if platform.system() == 'Linux':
                    self.tracker = ViveTracker(self.camera.device.fileno())
                else:
                    self.tracker = ViveTracker(self.camera.device, self.camera.device_index)

            def close(self: 'FTCameraController.Helper') -> None:
                """Close tracker and camera."""
                if self.tracker is not None:
                    self.tracker.dispose()
                    self.tracker = None
                if self.camera is not None:
                    self.camera.close()
                    self.camera.processor = None
                    self.camera.terminator = None
                    self.camera.queue = None
                    self.camera = None

            def process(self, frame) -> None:
                """Process frame."""
                channel = cv2.split(frame)[0]
                frame = cv2.merge((channel, channel, channel))
                if self.tracker is not None:
                    frame = self.tracker.process_frame(frame)
                self._queue.put(pack('HHH', *frame.shape) + frame.tobytes())

        helper: Helper = Helper(queue)
        try:
            FTCameraController._logger.info(
                "FTCameraController._read_process: open device")
            helper.open_camera(self._index, queue)

            if not ViveTracker.is_camera_vive_tracker(helper.camera.device):
                FTCameraController._logger.exception(
                    "FTCameraController._read_process: not a VIVE Facial Tracker")
                raise RuntimeError("not a VIVE Facial Tracker")

            helper.open_tracker()

            FTCameraController._logger.info(
                "FTCameraController._read_process: start reading")
            helper.camera.read()
        except Exception:
            FTCameraController._logger.exception(
                "FTCameraController._read_process: failed open device")
            print(traceback.format_exc())
        finally:
            helper.close()

        FTCameraController._logger.info("FTCameraController._read_process: EXIT")
