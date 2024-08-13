import os
import typing
from pygrabber.dshow_graph import FilterGraph

is_nt = True if os.name == "nt" else False
graph = FilterGraph()


def list_camera_names():
    cam_list = graph.get_input_devices()
    cam_names = []
    for index, name in enumerate(cam_list):
        cam_names.append(name)
    return cam_names


def get_camera_index_by_name(name):
    cam_list = graph.get_input_devices()

    for i, device_name in enumerate(cam_list):
        if device_name == name:
            return i

    return None


def PlaySound(*args, **kwargs): pass


SND_FILENAME = SND_ASYNC = 1

if is_nt:
    import winsound

    PlaySound = winsound.PlaySound
    SND_FILENAME = winsound.SND_FILENAME
    SND_ASYNC = winsound.SND_ASYNC
