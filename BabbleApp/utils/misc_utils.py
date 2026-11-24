import serial
import serial.tools.list_ports
import sys
import glob
import os
import platform
import cv2
import re
import subprocess
import threading
import contextlib

# Android reports itself as "Linux" through platform.system() on Python 3.12, but none of the
# Linux-only paths (v4l2, fcntl ioctls, /dev/video*) are usable there, so detect it explicitly.
is_android = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")

# Set environment variable before importing sounddevice. Value is not important.
os.environ["SD_ENABLE_ASIO"] = "1"
try:
    # PortAudio / libsndfile are not available on every platform (notably Android).
    # When they are missing, sounds are played through Kivy's audio providers instead.
    if is_android:
        raise ImportError("sounddevice is not supported on Android")
    import sounddevice as sd
    import soundfile as sf
except (ImportError, OSError):
    sd = None
    sf = None

bg_color_highlight = "#424042"
bg_color_clear = "#242224"

onnx_providers = [
    "DmlExecutionProvider",
    "CUDAExecutionProvider",
    "CoreMLExecutionProvider",
    "CPUExecutionProvider",
]

# Detect the operating system ("Windows", "Linux", "Darwin" or "Android")
os_type = "Android" if is_android else platform.system()

if os_type == 'Windows':
    from pygrabber.dshow_graph import FilterGraph
    graph = FilterGraph()

def is_valid_float_input(value):
    # Allow empty string, negative sign, or a float number
    return bool(re.match(r"^-?\d*\.?\d*$", value))

def is_valid_int_input(value):
    # Allow empty string, negative sign, or an integer number
    return bool(re.match(r"^-?\d*$", value))

def list_camera_names():
    cam_list = graph.get_input_devices()
    cam_names = []
    for index, name in enumerate(cam_list):
        cam_names.append(name)
    cam_names = cam_names + list_serial_ports()
    return cam_names

@contextlib.contextmanager
def suppress_stderr():
    """Context manager to suppress stderr (used for OpenCV warnings)."""
    with open(os.devnull, 'w') as devnull:
        old_stderr_fd = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(old_stderr_fd, 2)
            os.close(old_stderr_fd)

def list_cameras_opencv():
    """Use OpenCV to check available cameras by index (fallback for Linux/macOS)"""
    index = 0
    arr = []
    with suppress_stderr():  # tell OpenCV not to throw "cannot find camera" while we probe for cameras
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.read()[0]:
                cap.release()
                break
            else:
                arr.append(f"/dev/video{index}")
                cap.release()
            index += 1
    return arr

def is_uvc_device(device):
    """Check if the device is a UVC video device (not metadata)"""
    try:
        result = subprocess.run(
            ["v4l2-ctl", f"--device={device}", "--all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = result.stdout.decode("utf-8")

        # Check if "UVC Payload Header Metadata" is in the output
        if "UVC Payload Header Metadata" in output:
            return False  # It's metadata, not actual video
        return True  # It's a valid video device
    except Exception as e:
        return False


def list_linux_uvc_devices():
    """List UVC video devices on Linux (excluding metadata devices)"""
    try:
        # v4l2-ctl --list-devices breaks if video devices are non-sequential.
        # So this might be better?
        result = glob.glob("/dev/video*");
        devices = []
        current_device = None
        for line in result:
            if is_uvc_device(line):
                devices.append(
                    line
                )  # We return the path like '/dev/video0'

        return devices

    except Exception as e:
        return [f"Error listing UVC devices on Linux: {str(e)}"]


def list_camera_names():
    """Cross-platform function to list camera names"""

    if os_type == 'Windows':
        # On Windows, use pygrabber to list devices
        cam_list = graph.get_input_devices()
        return cam_list + list_serial_ports()

    elif os_type == "Linux":
        # On Linux, return UVC device paths like '/dev/video0'
        return list_linux_uvc_devices() + list_serial_ports()

    elif os_type == "Darwin":
        # On macOS, fallback to OpenCV (device names aren't fetched)
        return list_cameras_opencv() + list_serial_ports()

    elif os_type == "Android":
        # Local cameras and serial ports are not reachable through OpenCV/pyserial on Android.
        # Network (MJPEG/HTTP) camera addresses can still be typed in manually.
        return []

    else:
        return ["Unsupported operating system"]


def list_serial_ports():
    #print("DEBUG: Listed Serial Ports")
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if not sys.platform.startswith(("win", "linux", "cygwin", "darwin")):
        raise EnvironmentError("Unsupported platform")

    ports = []
    try:
        for s in serial.tools.list_ports.comports():
            ports.append(s.device)
    except (AttributeError, OSError, serial.SerialException):
        pass
    return sorted(ports)


def get_camera_index_by_name(name):
    """Cross-platform function to get the camera index by its name or path"""
    cam_list = list_camera_names()

    # On Linux, we use device paths like '/dev/video0' and match directly
    # OpenCV expects the actual /dev/video#, not the offset into the device list
    if os_type == "Linux":
        if (name.startswith("/dev/ttyACM")):
            return int(str.replace(name,"/dev/ttyACM",""));
        else:
            return int(str.replace(name,"/dev/video",""));

    # On Windows, match by camera name
    elif os_type == 'Windows':
        for i, device_name in enumerate(cam_list):
            if device_name == name:
                return i

    # On macOS or other systems, fallback to OpenCV device index
    elif os_type == "Darwin":
        for i, device in enumerate(cam_list):
            if device == name:
                return i

    return None

def _play_sound_kivy(file):
    # Kivy's SoundLoader picks the right backend per platform (SDL2/GStreamer/Android MediaPlayer).
    from kivy.core.audio import SoundLoader

    sound = SoundLoader.load(file)
    if sound is not None:
        sound.play()


def playSound(file):
    if sd is not None:
        data, fs = sf.read(file)
        sd.play(data, fs)
        # Block worker threads until the sound finishes (previous behaviour), but never the UI thread.
        if threading.current_thread() is not threading.main_thread():
            sd.wait()
        return
    try:
        from kivy.clock import Clock

        Clock.schedule_once(lambda dt: _play_sound_kivy(file))
    except Exception as e:
        print(f"Unable to play sound {file}: {e}")

# Handle debugging virtual envs.
def ensurePath():
    if os.path.exists(os.path.join(os.getcwd(), "BabbleApp")):
        os.chdir(os.path.join(os.getcwd(), "BabbleApp"))
