import typing
import serial
import sys
import glob
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

def list_serial_ports():
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
    #cam_list = list_camera_names()
    cam_list = graph.get_input_devices()
    #rint(f"name: {name}")
    #rint(f"cam_list: {cam_list}")

    for i, device_name in enumerate(cam_list):
        if device_name == name:
            return i

    return None

#def get_serial_port(name):
#    for i, device in enumerate(cam_list):



def PlaySound(*args, **kwargs): pass


SND_FILENAME = SND_ASYNC = 1

if is_nt:
    import winsound

    PlaySound = winsound.PlaySound
    SND_FILENAME = winsound.SND_FILENAME
    SND_ASYNC = winsound.SND_ASYNC
