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

import time
import platform
import logging
import signal
from enum import Enum
import numpy as np
from utils.misc_utils import os_type

if os_type == "Linux":
    import v4l2py as v4l
    import v4l2py.device as v4ld
elif os_type == "Windows":
    import pygrabber.dshow_graph as pgdsg
    import pygrabber.dshow_ids as pgdsi


class FTCamera:
    """Opens a camera grabbing frames as numpy arrays."""

    class ControlType(Enum):
        """Type of the control."""

        INTEGER = "int"
        BOOLEAN = "bool"
        SELECT = "select"

    if os_type == "Linux":

        class Control:
            """Control defined by the hardware."""

            def __init__(
                self: "FTCamera.ControlInfo", control: v4ld.BaseControl
            ) -> None:
                self._control = control
                self.name = control.name
                self.type = None
                self.minimum: int = 0
                self.maximum: int = 0
                self.step: int = 1
                self.default: int = 0
                self.clipping: bool = False
                self.choices: dict[int:str] = {}
                match control.type:
                    case v4ld.ControlType.INTEGER:
                        self.type = FTCamera.ControlType.INTEGER
                        self.minimum = control.minimum
                        self.maximum = control.maximum
                        self.step = control.step
                        self.default = control.default
                        self.clipping = control.clipping
                    case v4ld.ControlType.BOOLEAN:
                        self.type = FTCamera.ControlType.BOOLEAN
                        self.default = control.default
                    case v4ld.ControlType.MENU:
                        self.type = FTCamera.ControlType.SELECT
                        self.choices = dict(control.data)
                        self.default = control.default

            @property
            def value(self: "FTCamera.ControlInfo") -> int | bool:
                """Control value."""
                return self._control.value

            @value.setter
            def value(self: "FTCamera.ControlInfo", new_value: int | bool):
                self._control.value = new_value

            @property
            def is_writeable(self: "FTCamera.ControlInfo") -> bool:
                """Control is writeable."""
                return self._control.is_writeable

    elif os_type == "Windows":

        class Control:
            """Control defined by the hardware."""

            def __init__(self: "FTCamera.ControlInfo") -> None:
                raise RuntimeError("Not supported")

            @property
            def value(self: "FTCamera.ControlInfo") -> int | bool:
                """Control value"""
                return 0

            @value.setter
            def value(self: "FTCamera.ControlInfo", new_value: int | bool):
                pass

            @property
            def is_writeable(self: "FTCamera.ControlInfo") -> bool:
                """Control is writeable."""
                pass

        class FrameSize:
            """Frame size."""

            def __init__(
                self: "FTCamera.FrameSize",
                index: int,
                width: int,
                height: int,
                min_fps: int,
            ) -> None:
                self.index = index
                self.width = width
                self.height = height
                self.min_fps = min_fps

            def __repr__(self: "FTCamera.FrameSize") -> str:
                return "(width={}, height={}, fps={})".format(
                    self.width, self.height, self.min_fps
                )

        class FrameFormat:
            """Frame format."""

            def __init__(
                self: "FTCamera.FrameFormat", pixel_format: str, description: str
            ) -> None:
                self.pixel_format = pixel_format
                self.description = description

            def __repr__(self: "FTCamera.FrameFormat") -> str:
                return "(pixel_format={}, description='{}')".format(
                    self.pixel_format, self.description
                )

    class Terminator:
        """Terminator."""

        terminate_requested = False

        def __init__(self):
            signal.signal(signal.SIGINT, self.request_terminate)
            signal.signal(signal.SIGTERM, self.request_terminate)

        def request_terminate(self, signum, frame):
            """Request to terminate process."""
            self.terminate_requested = True

    class Processor:
        """Processor."""

        def __init__(self):
            pass

        def process(self, frame) -> None:
            """Process frame."""

    _logger = logging.getLogger("evcta.FTCamera")

    def __init__(self: "FTCamera", index: int) -> None:
        """Create camera grabber.

        The camera is not yet opened. Set "callback_frame" then call
        "open()" to open the device and "start_read()" to start capturing.

        Keyword arguments:
        index -- Index of the camera. Under Linux this uses the device
                 file "/dev/video{index}".
        """
        self._index: int = index
        if os_type == "Linux":
            self._device: v4l.Device = None
        elif os_type == "Windows":
            self._device: pgdsg.VideoInput = None
            self._filter_graph: pgdsg.FilterGraph = None
            self._filter_video = None
            self._filter_grabber = None

        self._controls: "list[FTCamera.Control]" = []
        self._has_frame: bool = False
        self._read_frame: np.ndarray = None
        self._arr_data: np.ndarray = None
        self._arr_c2: np.ndarray = None
        self._arr_c3: np.ndarray = None
        self._arr_merge: np.ndarray = None
        self._format: FTCamera.FrameFormat = None
        self._frame_size: FTCamera.FrameSize = None
        self._frame_width: int = 0
        self._frame_height: int = 0
        self._pixel_count: int = 0
        self._half_pixel_count: int = 0
        self._half_frame_width: int = 0
        self._half_frame_height: int = 0

        self.terminator: FTCamera.Terminator = None
        self.processor: FTCamera.Processor = None

    def open(self: "FTCamera") -> None:
        """Open device if closed.

        This opens the device using Video4Linux. Finds frame size and
        format to use. Also finds all supported controls.

        This method does not start recording.

        Throws "Exception" if:
        - Device can not be found
        - Device can not be opened
        - Device has no format supporting capturing
        - Device has no YUV format
        - Device has no size with YUV format and at least 30 frame rate
        """
        if self._device:
            return
        FTCamera._logger.info("FTCamera.open: index {}".format(self._index))
        if os_type == "Linux":
            self._device = v4l.Device.from_id(self._index)
            self._device.open()
        elif os_type == "Windows":
            self._filter_graph = pgdsg.FilterGraph()

            self._filter_graph.add_video_input_device(self._index)
            self._filter_video = self._filter_graph.get_input_device()
            FTCamera._logger.info(
                "Video input filter: {}".format(self._filter_video.Name)
            )
            self._device = self._filter_video

            self._filter_graph.add_sample_grabber(self._async_grabber)
            self._filter_grabber = self._filter_graph.filters[
                pgdsg.FilterType.sample_grabber
            ]

            self._filter_graph.add_null_render()
        self._find_format()
        self._find_frame_size()
        self._set_frame_format()
        self._init_arrays()
        self._find_controls()

        if not os_type == "Linux":
            self._filter_graph.prepare_preview_graph()
            # self._filter_graph.print_debug_info()

    def _find_format(self: "FTCamera") -> None:
        """Logs all formats supported by camera and picks best one.

        Picks the first format which is YUV and supports capturing.

        Throws "Exception" if no suitable format is found.
        """
        FTCamera._logger.info("formats:")
        if os_type == "Linux":
            for x in self._device.info.formats:
                FTCamera._logger.info("- {}".format(x))
            self._format = next(
                x
                for x in self._device.info.formats
                if x.pixel_format == v4l.PixelFormat.YUYV
            )
        elif os_type == "Windows":
            for x in self._filter_video.get_formats():
                FTCamera._logger.info(x)
            fmt = next(
                x
                for x in self._filter_video.get_formats()
                if x["media_type_str"] in ["YUY2"]
            )
            self._format = FTCamera.FrameFormat(
                fmt["media_type_str"], fmt["media_type_str"]
            )
        FTCamera._logger.info("using format: {}".format(self._format))

    def _find_frame_size(self: "FTCamera") -> None:
        """Logs all sizes supported by camera and picks best one.

        Picks the first size with YUV format and a minimum FPS of 30.

        Throws "Exception" if no suitable size is found.
        """
        if os_type == "Linux":
            FTCamera._logger.info("sizes:")
            for x in self._device.info.frame_sizes:
                FTCamera._logger.info("- {}".format(x))
            self._frame_size = next(
                x
                for x in self._device.info.frame_sizes
                if x.pixel_format == v4l.PixelFormat.YUYV and x.min_fps >= 30
            )
        elif os_type == "Windows":
            fsize = next(
                x
                for x in self._filter_video.get_formats()
                if x["media_type_str"] == self._format.pixel_format
                and x["min_framerate"] >= 30
            )
            self._frame_size = FTCamera.FrameSize(
                fsize["index"],
                fsize["width"],
                fsize["height"],
                int(fsize["max_framerate"]),
            )

        FTCamera._logger.info("using frame size : {}".format(self._frame_size))
        self._frame_width = self._frame_size.width
        self._frame_height = self._frame_size.height
        self._pixel_count = self._frame_width * self._frame_height
        self._half_pixel_count = self._pixel_count // 2
        self._half_frame_width = self._frame_width // 2
        self._half_frame_height = self._frame_height // 2

    def _set_frame_format(self: "FTCamera") -> None:
        """Activates the found format and size."""
        if os_type == "Linux":
            self._device.set_format(
                buffer_type=v4ld.BufferType.VIDEO_CAPTURE,
                width=self._frame_size.width,
                height=self._frame_size.height,
                pixel_format=self._format.pixel_format,
            )
        elif os_type == "Windows":
            self._filter_video.set_format(self._frame_size.index)

            # make grabber accept YUV2 not RGB24
            guid_yuv2 = "{32595559-0000-0010-8000-00AA00389B71}"
            self._filter_grabber.set_media_type(pgdsg.MediaTypes.Video, guid_yuv2)

            # by changing the format we have to replace the callback
            # handler too. this is required since the original callback
            # handler expects a 3-channel image and YUV2 delivers
            # 2 channels. this crashes python_grabber
            class SampleGrabberYUV2(pgdsg.SampleGrabberCallback):
                """Sample grabber using YUV2."""

                def __init__(
                    self: "SampleGrabberYUV2",
                    callback: pgdsg.Callable[[pgdsg.Mat], None],
                ):
                    super().__init__(callback)
                    self.keep_photo: bool = False

                def BufferCB(
                    self: "SampleGrabberYUV2",
                    this,
                    SampleTime,
                    pBuffer: pgdsg.NPBUFFER,
                    BufferLen: int,
                ) -> int:
                    """Buffer callback."""
                    if self.keep_photo:
                        self.keep_photo = False
                        w = self.image_resolution[0]
                        h = self.image_resolution[1]
                        img = np.ctypeslib.as_array(pBuffer, shape=(h, w, 2))
                        # this is brain-dead. the video is returned with the
                        # x and y axis flipped. this totally breaks the YUV
                        # decoding. switching axes fixes this mess
                        img = np.moveaxis(img, 0, 1)
                        self.callback(img)
                    return 0

            self._filter_grabber.set_callback(SampleGrabberYUV2(self._async_grabber), 1)

            # an alternative is pgdsi.GUID_NULL accepting everything

    def _init_arrays(self: "FTCamera") -> None:
        """Create numpy arrays to fill during capturing."""
        self._arr_data = np.zeros([self._pixel_count * 2], dtype=np.uint8)
        self._arr_merge = np.zeros([self._pixel_count, 3], dtype=np.uint8)
        self._arr_c2 = np.empty([self._half_pixel_count], np.uint8)
        self._arr_c3 = np.empty([self._half_pixel_count], np.uint8)

    def _find_controls(self: "FTCamera") -> None:
        """Logs all controls and stores them for use."""
        self._controls = []
        FTCamera._logger.info("controls:")
        if os_type == "Linux":
            for x in self._device.controls.values():
                FTCamera._logger.info("- {}".format(x))
                control = FTCamera.Control(x)
                if not control.type:
                    continue
                self._controls.append(control)

    @property
    def device_index(self: "FTCamera") -> int:
        """Device index."""
        return self._index

    if os_type == "Linux":

        @property
        def device(self: "FTCamera") -> v4l.Device:
            """Video4Linux device if open or None if closed."""
            return self._device

    elif os_type == "Windows":

        @property
        def device(self: "FTCamera") -> pgdsg.VideoInput:
            """Device if open or None if closed."""
            return self._device

    @property
    def frame_width(self: "FTCamera") -> int:
        """Width in pixels of captured frames.

        Only valid if device is open."""
        return self._frame_width

    @property
    def frame_height(self: "FTCamera") -> int:
        """Height in pixels of captured frames.

        Only valid if device is open."""
        return self._frame_height

    @property
    def frame_fps(self: "FTCamera") -> float:
        """Capture frame rate.

        Only valid if device is open."""
        return float(self._frame_size.min_fps)

    @property
    def frame_format(self: "FTCamera") -> str:
        """Capture pixel format.

        Only valid if device is open."""
        return self._frame_size.pixel_format.name

    @property
    def frame_format_description(self: "FTCamera") -> str:
        """Capture pixel format description.

        Only valid if device is open."""
        return self._format.description

    @property
    def controls(self: "FTCamera") -> "list[FTCamera.Control]":
        """List of all supported controls.

        Only valid if device is open."""
        return self._controls

    def close(self: "FTCamera") -> None:
        """Closes the device if open.

        If capturing stops capturing first.
        """
        if not self._device:
            return
        FTCamera._logger.info("FTCamera.close: index {}".format(self._index))
        try:
            if os_type == "Linux":
                self._device.close()
            elif os_type == "Windows":
                self._filter_graph.stop()
                self._filter_graph.remove_filters()
                self._filter_grabber = None
                self._filter_video = None
                self._filter_graph = None
        except Exception:
            pass
        self._device = None

    if os_type == "Linux":

        def read(self: "FTCamera") -> None:
            """Read next frame."""
            FTCamera._logger.info("FTCamera.read: ENTER")
            for frame in self._device:
                if self.terminator.terminate_requested:
                    break
                self._process_frame(frame)
            FTCamera._logger.info("FTCamera.read: EXIT")

    elif os_type == "Windows":

        def read(self: "FTCamera") -> None:
            """Read frames until requested to exit."""
            self._filter_graph.run()
            while not self.terminator.terminate_requested:
                self._filter_graph.grab_frame()
                time.sleep(0.001)

        def _async_grabber(self: "FTCamera", image: np.ndarray) -> None:
            self._process_frame(image)

    if os_type == "Linux":

        def _process_frame(self: "FTCamera", frame) -> None:
            """Process captured frames.

            Operates only on YUV422 format right now. Calls _decode_yuv422
            for processing the frame. See _decode_yuv422_y_only for an
            optimized version producing only Y grayscale frame.

            The captured frame is reshaped to (height, width, 3) before
            sending it to "callback_frame".
            """
            if len(frame.data) == 0:
                return

            try:
                match frame.pixel_format:
                    case v4l.PixelFormat.YUYV:
                        self._decode_yuv422(frame.data)
                    case _:
                        FTCamera._logger.error(
                            "Unsupported pixel format: {}".format(frame.pixel_format)
                        )
                        return False
                self.processor.process(
                    self._arr_merge.reshape([frame.height, frame.width, 3])
                )
            except Exception:
                FTCamera._logger.exception("FTCamera._process_frame")

    elif os_type == "Windows":

        def _process_frame(self: "FTCamera", frame: np.ndarray) -> None:
            if len(frame) == 0:
                return
            try:
                match self._format.pixel_format:
                    case "YUY2":
                        self._decode_yuv422(frame)
                    case _:
                        FTCamera._logger.error(
                            "Unsupported pixel format: {}".format(
                                self._format.pixel_format
                            )
                        )
                        return False
                self.processor.process(
                    self._arr_merge.reshape(
                        [self._frame_size.height, self._frame_size.width, 3]
                    )
                )
            except Exception:
                FTCamera._logger.exception("FTCamera._process_frame")

    if os_type == "Linux":

        def _decode_yuv422(self: "FTCamera", frame: list[bytes]) -> None:
            """Decode YUV422 frame into YUV444 frame."""
            self._arr_data[:] = np.frombuffer(frame, dtype=np.uint8)

            self._arr_merge[:, 0] = np.array(self._arr_data[0::2])
            self._arr_c2[:] = np.array(self._arr_data[1::4])
            self._arr_c3[:] = np.array(self._arr_data[3::4])

            self._arr_merge[0 : self._pixel_count : 2, 1] = self._arr_c2
            self._arr_merge[1 : self._pixel_count : 2, 1] = self._arr_c2
            self._arr_merge[0 : self._pixel_count : 2, 2] = self._arr_c3
            self._arr_merge[1 : self._pixel_count : 2, 2] = self._arr_c3

    elif os_type == "Windows":

        def _decode_yuv422(self: "FTCamera", frame: np.ndarray) -> None:
            self._arr_merge[:, 0] = frame[:, :, 0].ravel(order="F")

            self._arr_c2[:] = np.array(frame[:, :, 1:].ravel(order="F")[0::2])
            self._arr_c3[:] = np.array(frame[:, :, 1:].ravel(order="F")[1::2])

            self._arr_merge[0 : self._pixel_count : 2, 1] = self._arr_c2
            self._arr_merge[1 : self._pixel_count : 2, 1] = self._arr_c2
            self._arr_merge[0 : self._pixel_count : 2, 2] = self._arr_c3
            self._arr_merge[1 : self._pixel_count : 2, 2] = self._arr_c3

    def _decode_yuv422_y_only(self: "FTCamera", frame: list[bytes]) -> None:
        """Fast version of _decode_yuv422.

        This version is faster since it only copies the Y channel
        of the image data. The result is thus a single channel
        image (grayscale image). This is suitible for cameras
        like the VIVE that output the same image on all channels
        """
        self._arr_data[:] = np.frombuffer(frame, dtype=np.uint8)

        self._arr_merge[:, 0] = np.array(self._arr_data[0::2])
