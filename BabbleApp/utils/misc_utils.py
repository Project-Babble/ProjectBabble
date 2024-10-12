import typing
import serial
import sys
import glob
import os
import platform
import cv2
import subprocess
import re
from pygrabber.dshow_graph import FilterGraph

is_nt = True if sys.platform.startswith('win') else False
graph = FilterGraph()


def list_camera_names():
    cam_list = graph.get_input_devices()
    cam_names = []
    for index, name in enumerate(cam_list):
        cam_names.append(name)
    cam_names = cam_names + list_serial_ports()
    return cam_names

# Detect the operating system
is_nt = True if os.name == "nt" else False
os_type = platform.system()

if is_nt:
    from pygrabber.dshow_graph import FilterGraph
    graph = FilterGraph()


def list_cameras_opencv():
    """ Use OpenCV to check available cameras by index (fallback for Linux/macOS) """
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(f"/dev/video{index}")
        cap.release()
        index += 1
    return arr


def is_uvc_device(device):
    """ Check if the device is a UVC video device (not metadata) """
    try:
        result = subprocess.run(
            ['v4l2-ctl', f'--device={device}', '--all'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = result.stdout.decode('utf-8')

        # Check if "UVC Payload Header Metadata" is in the output
        if "UVC Payload Header Metadata" in output:
            return False  # It's metadata, not actual video
        return True  # It's a valid video device
    except Exception as e:
        return False


def list_linux_uvc_devices():
    """ List UVC video devices on Linux (excluding metadata devices) """
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')

        lines = output.splitlines()
        devices = []
        current_device = None
        for line in lines:
            if not line.startswith("\t"):
                current_device = line.strip()
            else:
                if "/dev/video" in line and is_uvc_device(line.strip()):
                    devices.append(line.strip())  # We return the path like '/dev/video0'

        return devices

    except Exception as e:
        return [f"Error listing UVC devices on Linux: {str(e)}"]


def list_camera_names():
    """ Cross-platform function to list camera names """

    if is_nt:
        # On Windows, use pygrabber to list devices
        cam_list = graph.get_input_devices()
        return cam_list + list_serial_ports()

    elif os_type == "Linux":
        # On Linux, return UVC device paths like '/dev/video0'
        return list_linux_uvc_devices() + list_serial_ports()

    elif os_type == "Darwin":
        # On macOS, fallback to OpenCV (device names aren't fetched)
        return list_cameras_opencv() + list_serial_ports()

    else:
        return ["Unsupported operating system"]

def list_serial_ports():
    print("DEBUG: Listed Serial Ports")
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def get_camera_index_by_name(name):
    """ Cross-platform function to get the camera index by its name or path """
    cam_list = list_camera_names()

    # On Linux, we use device paths like '/dev/video0' and match directly
    if os_type == "Linux":
        for i, device_path in enumerate(cam_list):
            if device_path == name:
                return i

    # On Windows, match by camera name
    elif is_nt:
        for i, device_name in enumerate(cam_list):
            if device_name == name:
                return i

    # On macOS or other systems, fallback to OpenCV device index
    elif os_type == "Darwin":
        for i, device in enumerate(cam_list):
            if device == name:
                return i

    return None

def is_valid_float_input(value):
    # Allow empty string, negative sign, or a float number
    return bool(re.match(r'^-?\d*\.?\d*$', value))

def is_valid_int_input(value):
    # Allow empty string, negative sign, or an integer number
    return bool(re.match(r'^-?\d*$', value))



# Placeholder for sound functions on Windows
def PlaySound(*args, **kwargs):
    pass


SND_FILENAME = SND_ASYNC = 1

if is_nt:
    import winsound

    PlaySound = winsound.PlaySound
    SND_FILENAME = winsound.SND_FILENAME
    SND_ASYNC = winsound.SND_ASYNC
