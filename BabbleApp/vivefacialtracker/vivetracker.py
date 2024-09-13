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

import platform
import logging
import ctypes
import time
import cv2 as cv
import numpy as np
from timeit import default_timer as timer

isLinux = platform.system() == 'Linux'

if isLinux:
    import fcntl

    _IOC_NRBITS = 8
    _IOC_TYPEBITS = 8
    _IOC_SIZEBITS = 14
    _IOC_DIRBITS = 2

    _IOC_NRSHIFT = 0
    _IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
    _IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
    _IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

    _IOC_WRITE = 1
    _IOC_READ = 2

    def _IOC(dir_, type_, nr, size):
        return (
            ctypes.c_int32(dir_ << _IOC_DIRSHIFT).value
            | ctypes.c_int32(ord(type_) << _IOC_TYPESHIFT).value
            | ctypes.c_int32(nr << _IOC_NRSHIFT).value
            | ctypes.c_int32(size << _IOC_SIZESHIFT).value
        )

    def _IOC_TYPECHECK(t):
        return ctypes.sizeof(t)

    def _IOWR(type_, nr, size):
        return _IOC(_IOC_READ | _IOC_WRITE, type_, nr, _IOC_TYPECHECK(size))

else:
    import pygrabber.dshow_graph as pgdsg
    import comtypes as comt
    import ctypes.wintypes as ctwt

    c_void_p = ctypes.c_void_p
    c_wchar = ctypes.c_wchar
    c_wchar_p = ctypes.c_wchar_p
    c_ulong = ctypes.c_ulong
    c_uint = ctypes.c_uint
    c_uint8 = ctypes.c_uint8
    c_uint16 = ctypes.c_uint16
    c_enum = ctypes.c_int
    Structure = ctypes.Structure
    POINTER = ctypes.POINTER
    DWORD = ctwt.DWORD
    COMMETHOD = comt.COMMETHOD
    GUID = comt.GUID
    REFIID = POINTER(GUID)
    IUnknown = comt.IUnknown
    HRESULT = ctypes.HRESULT

    KSNODETYPE_DEV_SPECIFIC = GUID('{941C7AC0-C559-11D0-8A2B-00A0C9255AC1}')
    GUID_EXT_CTRL_UNIT = GUID('{2ccb0bda-6331-4fdb-850e-79054dbd5671}')

    class KSPROPERTY(Structure):
        _fields_ = [
            ('Set', GUID),
            ('Id', c_ulong),
            ('Flags', c_ulong)
        ]

    class KSP_NODE(Structure):
        _fields_ = [
            ('Property', KSPROPERTY),
            ('NodeId', ctypes.c_ulong),
            ('Reserved', ctypes.c_ulong)
        ]

    class KSTOPOLOGY_CONNECTION(Structure):
        _fields_ = [
            ('FromNode', c_ulong),
            ('FromNodePin', c_ulong),
            ('ToNode', c_ulong),
            ('ToNodePin', c_ulong)
        ]

    class IExtensionUnit(IUnknown):
        _case_insensitive_ = True
        'IExtensionUnit Interface'
        _iid_ = GUID_EXT_CTRL_UNIT
        _idlflags_ = []
        _methods_ = [
            COMMETHOD(
                [], HRESULT, 'get_InfoSize',
                (['out'], POINTER(c_ulong), 'pulSize')),
            COMMETHOD(
                [], HRESULT, 'get_Info',
                (['in'], c_ulong, 'ulSize'),
                (['in', 'out'], POINTER(c_uint8), 'pInfo')),
            COMMETHOD(
                [], HRESULT, 'get_PropertySize',
                (['in'], c_ulong, 'PropertyId'),
                (['out'], POINTER(c_ulong), 'pulSize')),
            COMMETHOD(
                [], HRESULT, 'get_Property',
                (['in'], c_ulong, 'PropertyId'),
                (['in'], c_ulong, 'ulSize'),
                (['in', 'out'], POINTER(c_uint8), 'pValue')),
            COMMETHOD(
                [], HRESULT, 'put_Property',
                (['in'], c_ulong, 'PropertyId'),
                (['in'], c_ulong, 'ulSize'),
                (['in', 'out'], POINTER(c_uint8), 'pValue')),
            COMMETHOD(
                [], HRESULT, 'get_PropertyRange',
                (['in'], c_ulong, 'PropertyId'),
                (['in'], c_ulong, 'ulSize'),
                (['in', 'out'], POINTER(c_uint8), 'pMin'),
                (['in', 'out'], POINTER(c_uint8), 'pMax'),
                (['in', 'out'], POINTER(c_uint8), 'pSteppingDelta'),
                (['in', 'out'], POINTER(c_uint8), 'pDefault'))
            ]

    class IKsTopologyInfo(IUnknown):
        _case_insensitive_ = True
        'IKsTopologyInfo Interface'
        _iid_ = GUID('{720D4AC0-7533-11D0-A5D6-28DB04C10000}')
        _idlflags_ = []
        _methods_ = [
            COMMETHOD(
                [], HRESULT, 'get_NumCategories',
                (['out'], POINTER(DWORD), 'pdwNumCategories')),
            COMMETHOD(
                [], HRESULT, 'get_Category',
                (['in'], DWORD, 'dwIndex'),
                (['out'], POINTER(GUID), 'pCategory')),
            COMMETHOD(
                [], HRESULT, 'get_NumConnections',
                (['out'], POINTER(DWORD), 'pdwNumConnections')),
            COMMETHOD(
                [], HRESULT, 'get_ConnectionInfo',
                (['in'], DWORD, 'dwIndex'),
                (['out'], POINTER(KSTOPOLOGY_CONNECTION), 'pConnectionInfo')),
            COMMETHOD(
                [], HRESULT, 'get_NodeName',
                (['in'], DWORD, 'dwNodeId'),
                # pwchNodeName is actually 'out' but not possible to
                # be declared like this in comtypes
                (['in'], c_wchar_p, 'pwchNodeName'),
                (['in'], DWORD, 'dwBufSize'),
                (['out'], POINTER(DWORD), 'pdwNameLen')),
            COMMETHOD(
                [], HRESULT, 'get_NumNodes',
                (['out'], POINTER(DWORD), 'pdwNumNodes')),
            COMMETHOD(
                [], HRESULT, 'get_NodeType',
                (['in'], DWORD, 'dwNodeId'),
                (['out'], POINTER(GUID), 'pNodeType')),
            COMMETHOD(
                [], HRESULT, 'CreateNodeInstance',
                (['in'], DWORD, 'dwNodeId'),
                (['in'], REFIID, 'iid'),
                (['out'], POINTER(POINTER(IUnknown)), 'ppvObject'))]

    class KSPROPERTY(Structure):
        _fields_ = [
            ('Set', GUID),
            ('Id', c_ulong),
            ('Flags', c_ulong)
        ]

    class KSMETHOD(Structure):
        _fields_ = [
            ('Set', GUID),
            ('Id', c_ulong),
            ('Flags', c_ulong)
        ]

    class KSEVENT(Structure):
        _fields_ = [
            ('Set', GUID),
            ('Id', c_ulong),
            ('Flags', c_ulong)
        ]

    class KSP_NODE(Structure):
        _fields_ = [
            ('Property', KSPROPERTY),
            ('NodeId', c_ulong),
            ('Reserved', c_ulong)
        ]

    class IKsControl(IUnknown):
        _case_insensitive_ = True
        'IKsControl Interface'
        _iid_ = GUID('{28F54685-06FD-11D2-B27A-00A0C9223196}')
        _idlflags_ = []
        _methods_ = [
            COMMETHOD(
                [], HRESULT, 'KsProperty',
                # (['in'], POINTER(KSPROPERTY), 'Property'),
                (['in'], POINTER(KSP_NODE), 'Property'),
                (['in'], c_ulong, 'PropertyLength'),
                (['in'], c_void_p, 'PropertyData'),
                (['in'], c_ulong, 'DataLength'),
                (['in'], POINTER(c_ulong), 'BytesReturned')),
            COMMETHOD(
                [], HRESULT, 'KsMethod',
                (['in'], POINTER(KSMETHOD), 'Method'),
                (['in'], c_ulong, 'MethodLength'),
                (['in', 'out'], c_void_p, 'MethodData'),
                (['in'], c_ulong, 'DataLength'),
                (['out'], POINTER(c_ulong), 'BytesReturned')),
            COMMETHOD(
                [], HRESULT, 'KsEvent',
                (['in'], POINTER(KSEVENT), 'Event'),
                (['in'], c_ulong, 'EventLength'),
                (['in', 'out'], c_void_p, 'EventData'),
                (['in'], c_ulong, 'DataLength'),
                (['out'], POINTER(c_ulong), 'BytesReturned'))
            ]

    def _find_extension_node(topo: IKsTopologyInfo, guid: GUID) -> int | None:
        count = topo.get_NumNodes()
        return next(i for i in range(count) if topo.get_NodeType(i) == guid)

    def _list_all_nodes(topo: IKsTopologyInfo) -> None:
        count = topo.get_NumNodes()
        name_buf = ctypes.create_unicode_buffer(255)
        for i in range(count):
            topo.get_NodeName(i, name_buf, 255)
            guid = topo.get_NodeType(i)
            print("- '{}' '{}'".format(name_buf.value, guid))

    KSPROPERTY_EXTENSION_UNIT_INFO = 0
    KSPROPERTY_TYPE_GET = 0x1
    KSPROPERTY_TYPE_SET = 0x2
    KSPROPERTY_TYPE_TOPOLOGY = 0x10000000

    def _control_propery_request(control: IKsControl, index: int,
                                 node: int, data: list[c_uint8]) -> int:
        extprop = KSP_NODE(
            KSPROPERTY(GUID_EXT_CTRL_UNIT, index,
                       KSPROPERTY_TYPE_GET | KSPROPERTY_TYPE_TOPOLOGY),
            node, 0)
        bytes_returned = ctypes.c_ulong(0)
        """
        print(["{}={}".format(n, getattr(extprop, n))
               for n, t in extprop._fields_])
        print(["{}={}".format(n, getattr(extprop.Property, n))
               for n, t in extprop.Property._fields_])
        print(("_control_propery_request: index={} node={},"
               + " len(data)={}, prop_size={}").format(
            index, node, len(data), _control_propery_request_len(
                control, index, node)))
        """
        control.KsProperty(extprop, ctypes.sizeof(extprop),
                           data, len(data), bytes_returned)
        # print("GetControlProperty: rec {}".format(bytes_returned.value))
        return bytes_returned.value

    def _control_propery_request_len(control: IKsControl, index: int,
                                     node: int) -> int:
        extprop = KSP_NODE(
            KSPROPERTY(GUID_EXT_CTRL_UNIT, index,
                       KSPROPERTY_TYPE_GET | KSPROPERTY_TYPE_TOPOLOGY),
            node, 0)
        bytes_returned = ctypes.c_ulong(0)
        try:
            control.KsProperty(extprop, ctypes.sizeof(extprop),
                               None, 0, bytes_returned)
        except comt.COMError as e:
            if e.hresult == -2147024662:  # more data available
                return bytes_returned.value
        return 0

    class KSPROPXUINFO(Structure):
        _fields_ = [
            ('Length', c_uint8),
            ('DescriptorType', c_uint8),
            ('DescriptorSubtype', c_uint8),
            ('bUnitID', c_uint8),
            ('guidExtensionCode', GUID),
            ('bNumControls', c_uint8),
            ('bNrInPins', c_uint8)
            # ('baSourceID', c_uint8 * 64)
        ]

    del COMMETHOD, GUID, HRESULT, POINTER, DWORD, REFIID
    del c_void_p, c_wchar, c_wchar_p, c_ulong, c_uint, c_uint8
    del c_uint16, c_enum, Structure


class ViveTracker:
    """Provides support to activate data steam on VIVE Facial Tracker camera."""
    _XU_TASK_SET = 0x50
    _XU_TASK_GET = 0x51
    _XU_REG_SENSOR = 0xab

    if isLinux:
        _UVC_SET_CUR = 0x01
        _UVC_GET_CUR = 0x81
        _UVC_GET_MIN = 0x82
        _UVC_GET_MAX = 0x83
        _UVC_GET_RES = 0x84
        _UVC_GET_LEN = 0x85
        _UVC_GET_INFO = 0x86
        _UVC_GET_DEF = 0x87

        class _uvc_xu_control_query(ctypes.Structure):
            _fields_ = [
                ('unit', ctypes.c_uint8),
                ('selector', ctypes.c_uint8),
                ('query', ctypes.c_uint8),
                ('size', ctypes.c_uint16),
                ('data', ctypes.POINTER(ctypes.c_uint8)),
            ]

        _UVCIOC_CTRL_QUERY = _IOWR('u', 0x21, _uvc_xu_control_query)

    _logger = logging.getLogger("evcta.ViveTracker")

    if isLinux:
        def __init__(self: 'ViveTracker', fd: int) -> None:
            """Create VIVE Face Tracker instance.

            Constructor tries first to detect if this is a VIVE Face Tracker.
            Then device parameters are set and the data stream eventually
            activated.

            Make sure to call "dispose()" once the tracker is no more needed
            to deactivate the data stream.

            Keyword arguments:
            fd --- File descriptor of device. Using Video4Linux device use
                "device.fileno()" for this argument. Using FTCamera use
                "ftcamera.device.fileno()" for this argument.
            """
            ViveTracker._logger.info("create vive tracker")
            if not fd:
                raise Exception("Missing camera file descriptor")
            self._fd: int = fd
            self._init_common()
    else:
        def __init__(self: 'ViveTracker', device: pgdsg.VideoInput,
                     index: int) -> None:
            """Create VIVE Face Tracker instance.

            Constructor tries first to detect if this is a VIVE Face Tracker.
            Then device parameters are set and the data stream eventually
            activated.

            Make sure to call "dispose()" once the tracker is no more needed
            to deactivate the data stream.

            Keyword arguments:
            device --- DirectShow device
            """
            self._device = device
            self._device_index = index
            self._xu_control: IKsControl = None

            ViveTracker._logger.info("create vive tracker")

            try:
                self._open_controller()
                self._init_common()
            except Exception:
                self.dispose()

    def _init_common(self: 'ViveTracker') -> None:
        self._dataBufLen = 384
        self._resize_data_buf()
        self._bufferRegister: list[ctypes.c_uint8] = (ctypes.c_uint8 * 17)()

        self._debug = False

        self._detect_vive_tracker()
        self._activate_tracker()

    def _resize_data_buf(self: 'ViveTracker') -> None:
        self._bufferSend: list[ctypes.c_uint8] = (ctypes.c_uint8 * self._dataBufLen)()
        self._bufferReceive: list[ctypes.c_uint8] = (ctypes.c_uint8 * self._dataBufLen)()

        self._dataTest: list[ctypes.c_uint8] = (ctypes.c_uint8 * self._dataBufLen)()
        self._dataTest[0] = 0x51
        self._dataTest[1] = 0x52
        if self._dataBufLen >= 256:
            self._dataTest[254] = 0x53
            self._dataTest[255] = 0x54
    if isLinux:
        @staticmethod
        def is_camera_vive_tracker(device: 'v4l.Device') -> bool:
            """Detect if this is a VIVE Face Tracker.

            This is done right now by looking at the human readable device
            description which might not be fool proof. Better would be to
            check the vendor-id(0x0bb4) and device-id (0x0321). But these
            can be only found by querying full USB descriptor. Left for
            the reader as excercise.
            """
            check = "HTC Multimedia Camera" in device.info.card
            ViveTracker._logger.info("is_camera_vive_tracker: '{}' -> {}".
                                     format(device.info.card, check))
            return check
    else:
        @staticmethod
        def is_camera_vive_tracker(device: 'pgdsg.VideoInput') -> bool:
            check = "HTC Multimedia Camera" in device.Name
            ViveTracker._logger.info("is_camera_vive_tracker: '{}' -> {}".
                                     format(device.Name, check))
            return check

    def dispose(self: 'ViveTracker') -> None:
        """Dispose of tracker.

        Deactivates data stream."""
        ViveTracker._logger.info("dispose vive tracker")

        if isLinux:
            self._deactivate_tracker()
        else:
            self._deactivate_tracker()
            self._close_controller()

    def process_frame(self: 'ViveTracker', data: np.ndarray) -> np.ndarray:
        """Process a captured frame.

        Right now this applies a median blur but other manipulations
        are possible to improve the image if desired.

        Keyword arguments:
        data --- Frame to process
        """
        lum = cv.split(data)[0]

        """
        gamma = 2.2
        inv_gamma = 1.0 / gamma
        lut = np.array([((i / 255.0) ** inv_gamma) * 255
                        for i in np.arange(0, 256)]).astype("uint8")
        lum = cv.LUT(lum, lut)
        """

        lum = lum[:, 0:200]

        lum = cv.resize(lum, (400, 400))

        """
        lum = cv.medianBlur(lum, 5)
        """

        return cv.merge((lum, lum, lum))

    if not isLinux:
        def _open_controller(self: 'ViveTracker') -> None:
            if self._xu_control:
                return

            logger = ViveTracker._logger

            sdenum = pgdsg.SystemDeviceEnum().system_device_enum
            filenum = sdenum.CreateClassEnumerator(
                comt.GUID(pgdsg.DeviceCategories.VideoInputDevice), dwFlags=0)
            moniker, count = filenum.Next(1)
            i = 0
            while i != self._device_index and count > 0:
                moniker, count = filenum.Next(1)
                i = i + 1

            """
            ipb = comt.persist.IPropertyBag
            propbag = moniker.BindToStorage(0, 0, ipb._iid_).QueryInterface(ipb)
            self._dev_name = propbag.Read("FriendlyName", pErrorLog=None)
            try:
                self._dev_desc = propbag.Read("Description", pErrorLog=None)
            except Exception:
                self._dev_desc = ""
            self._dev_path = propbag.Read("DevicePath", pErrorLog=None)
            logger.info("device info:")
            logger.info("- description: {}".format(self._dev_desc))
            logger.info("- friendly name: {}".format(self._dev_name))
            logger.info("- device path: {}".format(self._dev_path))
            """

            topo = self._device.instance.QueryInterface(IKsTopologyInfo)

            # _list_all_nodes(topo)
            self._xu_node_index = _find_extension_node(
                topo, KSNODETYPE_DEV_SPECIFIC)

            xu_node: IUnknown = topo.CreateNodeInstance(
                self._xu_node_index, IUnknown._iid_)

            self._xu_control = xu_node.QueryInterface(IKsControl)

            """
            data = (ctypes.c_uint8 * 250)(0)
            length = _control_propery_request(
                self._xu_control, KSPROPERTY_EXTENSION_UNIT_INFO,
                self._xu_node_index, data)
            xupi = KSPROPXUINFO.from_buffer_copy(data)
            # print(["{:02x}".format(x) for x in data[:length]])
            print(["{}={}".format(n, getattr(xupi, n))
                   for n, t in xupi._fields_])
            """

        def _close_controller(self: 'ViveTracker') -> None:
            self._xu_control = None

    def _xu_get_len(self: 'ViveTracker', selector: int) -> int:
        """Send GET_LEN command to device extension unit.

        Keyword arguments:
        selector --- Selector
        """
        if isLinux:
            length = (ctypes.c_uint8 * 2)(0, 0)
            c = ViveTracker._uvc_xu_control_query(
                4, selector, ViveTracker._UVC_GET_LEN, 2, length)
            fcntl.ioctl(self._fd, ViveTracker._UVCIOC_CTRL_QUERY, c)
            return (length[1] << 8) + length[0]
        else:
            return _control_propery_request_len(
                self._xu_control, 2, self._xu_node_index)

    def _xu_get_cur(self: 'ViveTracker', selector: int,
                    data: list[ctypes.c_uint8]) -> None:
        """Send GET_CUR command to device extension unit.

        Keyword arguments:
        selector --- Selector
        data -- Buffer to store response to. Has to be 384 bytes long.
        """
        if isLinux:
            c = ViveTracker._uvc_xu_control_query(
                4, selector, ViveTracker._UVC_GET_CUR, len(data), data)
            fcntl.ioctl(self._fd, ViveTracker._UVCIOC_CTRL_QUERY, c)
        else:
            xuprop = KSP_NODE(
                KSPROPERTY(GUID_EXT_CTRL_UNIT, selector,
                           KSPROPERTY_TYPE_GET | KSPROPERTY_TYPE_TOPOLOGY),
                self._xu_node_index, 0)
            received = ctypes.c_ulong(0)
            """
            print(["{}={}".format(n, getattr(xuprop, n))
                   for n, t in xuprop._fields_])
            print(["{}={}".format(n, getattr(xuprop.Property, n))
                   for n, t in xuprop.Property._fields_])
            print("_xu_get_cur: index={} node={}, len(data)={}, prop_size={}".
                  format(selector, self._xu_node_index, len(data),
                         _control_propery_request_len(
                             self._xu_control, selector, self._xu_node_index)))
            """
            self._xu_control.KsProperty(xuprop, ctypes.sizeof(xuprop),
                                        data, len(data), received)
            # print("received: {}".format(received.value))

    def _xu_set_cur(self: 'ViveTracker', selector: int,
                    data: list[ctypes.c_uint8]) -> None:
        """Send SET_CUR command to device extension unit.

        Keyword arguments:
        selector --- Selector
        data -- Data to send. Has to be 384 bytes long.
        """
        if isLinux:
            c = ViveTracker._uvc_xu_control_query(
                4, selector, ViveTracker._UVC_SET_CUR, len(data), data)
            fcntl.ioctl(self._fd, ViveTracker._UVCIOC_CTRL_QUERY, c)
        else:
            xuprop = KSP_NODE(
                KSPROPERTY(GUID_EXT_CTRL_UNIT, selector,
                           KSPROPERTY_TYPE_SET | KSPROPERTY_TYPE_TOPOLOGY),
                self._xu_node_index, 0)
            received = ctypes.c_ulong(0)
            """
            print(["{}={}".format(n, getattr(xuprop, n))
                   for n, t in xuprop._fields_])
            print(["{}={}".format(n, getattr(xuprop.Property, n))
                   for n, t in xuprop.Property._fields_])
            print("_xu_set_cur: index={} node={}, len(data)={}, prop_size={}".
                  format(selector, self._xu_node_index, len(data),
                         _control_propery_request_len(
                             self._xu_control, selector, self._xu_node_index)))
            """
            self._xu_control.KsProperty(xuprop, ctypes.sizeof(xuprop),
                                        data, len(data), received)

    def _get_len(self: 'ViveTracker') -> int:
        """Get buffer length of device."""
        return self._xu_get_len(2)

    def _set_cur(self: 'ViveTracker', command: list[ctypes.c_uint8],
                 timeout: float = 0.5) -> None:
        """Send SET_CUR command to device extension unit with proper handling.

        Sends SET_CUR command to the device. Then sends GET_CUR commands to
        device until the "command finished" response is found.

        Keyword arguments:
        command --- Command to send.
        timeout -- Timeout in seconds.
        """
        length = len(command)
        self._bufferSend[:length] = command
        self._xu_set_cur(2, self._bufferSend)
        if self._debug:
            ViveTracker._logger.debug("set_cur({})".format(
                [hex(x) for x in command[:16]]))
        lenbuf = len(self._bufferReceive)
        stime = timer()
        while True:
            self._bufferReceive[:] = (ctypes.c_uint8 * lenbuf)(0)
            self._xu_get_cur(2, self._bufferReceive)
            if self._bufferReceive[0] == 0x55:
                # command not finished yet
                if self._debug:
                    ViveTracker._logger.debug("-> getCur: pending")
            elif self._bufferReceive[0] == 0x56:
                # the full command is repeated minus the last byte.
                # we check only the first 16 bytes here
                if self._bufferReceive[1:17] == self._bufferSend[0:16]:
                    if self._debug:
                        ViveTracker._logger.debug("-> getCur: finished")
                    return  # command finished
                else:
                    raise Exception(
                        "set_cur({}): response not matching command".
                        format([hex(x) for x in command[:16]]))
            else:
                raise Exception("set_cur({}): invalid response: {}".format(
                    [hex(x) for x in command[:16]],
                    [hex(x) for x in self._bufferReceive[:16]]))

            elapsed = (timer() - stime)
            if self._debug:
                ViveTracker._logger.debug("-> elasped {:d}ms".format(
                    int(elapsed * 1000)))
            if elapsed > timeout:
                raise Exception("set_cur({}): timeout".format(
                    [hex(x) for x in command[:16]]))

    def _set_cur_no_resp(self: 'ViveTracker',
                         command: list[ctypes.c_uint8]) -> None:
        """Send SET_CUR command to device without proper handling.

        Keyword arguments:
        command --- Command to send.
        """
        self._bufferSend[:len(command)] = command
        self._xu_set_cur(2, self._bufferSend)
        if self._debug:
            ViveTracker._logger.debug("set_cur_no_resp({})".format(
                [hex(x) for x in command[:16]]))

    def _init_register(self: 'ViveTracker', command: int, reg: int,
                       address: int, address_len: int,
                       value: int, value_len: int) -> None:
        """Init buffer for manipulating a register.

        Keyword arguments:
        command --- Command
        reg --- Register
        address --- Address
        address_len --- Length of address in bytes
        value --- Value
        value_len --- Length of value in bytes
        """
        br = self._bufferRegister
        br[0] = ctypes.c_uint8(command)
        br[1] = ctypes.c_uint8(reg)
        br[2] = ctypes.c_uint8(0x60)
        br[3] = ctypes.c_uint8(address_len)  # address width in bytes
        br[4] = ctypes.c_uint8(value_len)  # data width in bytes

        # address
        br[5] = ctypes.c_uint8((address > 24) & 0xff)
        br[6] = ctypes.c_uint8((address > 16) & 0xff)
        br[7] = ctypes.c_uint8((address > 8) & 0xff)
        br[8] = ctypes.c_uint8(address & 0xff)

        # page address
        br[9] = ctypes.c_uint8(0x90)
        br[10] = ctypes.c_uint8(0x01)
        br[11] = ctypes.c_uint8(0x00)
        br[12] = ctypes.c_uint8(0x01)

        # value
        br[13] = ctypes.c_uint8((value > 24) & 0xff)
        br[14] = ctypes.c_uint8((value > 16) & 0xff)
        br[15] = ctypes.c_uint8((value > 8) & 0xff)
        br[16] = ctypes.c_uint8(value & 0xff)

    def _set_register(self: 'ViveTracker', reg: int, address: int,
                      value: int, timeout: float = 0.5) -> None:
        """Set device register.

        Keyword arguments:
        reg --- Register to manipulate
        address --- Address to manipulate
        value --- Value to set
        timeout --- Timeout in seconds. Use 0 to send register without
                    proper request handling
        """
        self._init_register(ViveTracker._XU_TASK_SET, reg, address, 1, value, 1)
        if timeout > 0:
            self._set_cur(self._bufferRegister, timeout)
        else:
            self._set_cur_no_resp(self._bufferRegister)

    def _get_register(self: 'ViveTracker', reg: int, address: int,
                      timeout: float = 0.5) -> int:
        """Get device register.

        Keyword arguments:
        reg --- Register to fetch
        address --- Address to fetch
        timeout --- Timeout in seconds
        """
        self._init_register(ViveTracker._XU_TASK_GET, reg, address, 1, 0, 1)
        self._set_cur(self._bufferRegister, timeout)
        return int(self._bufferReceive[17])

    def _set_register_sensor(self: 'ViveTracker', address: int, value: int,
                             timeout: float = 0.5) -> None:
        """Set device sensor register.

        Keyword arguments:
        address --- Address to manipulate
        value --- Value to set
        timeout --- Timeout in seconds. Use 0 to send register without
                    proper request handling
        """
        self._set_register(ViveTracker._XU_REG_SENSOR, address, value, timeout)

    def _get_register_sensor(self: 'ViveTracker', address: int,
                             timeout: float = 0.5) -> int:
        """Get device sensor register.

        Keyword arguments:
        address --- Address to fetch
        timeout --- Timeout in seconds
        """
        return self._get_register(ViveTracker._XU_REG_SENSOR, address, timeout)

    def _set_enable_stream(self: 'ViveTracker', enable: bool) -> None:
        """Enable or disable data stream.

        Keyword arguments:
        enable --- Enable or disable data stream.
        """
        buf = (ctypes.c_uint8 * 4)(ViveTracker._XU_TASK_SET, 0x14, 0x00,
                                   0x01 if enable else 0x00)
        self._set_cur_no_resp(buf)

    def _detect_vive_tracker(self: 'ViveTracker') -> None:
        """Try to detect if this is a VIVE Face Tracker device.

        uses GET_LEN to get the data buffer length. VIVE Face Tracker
        uses 384. If this is not the case then this is most probebly
        something else but not a VIVE Face Tracker.
        """
        if isLinux:
            length = self._get_len()
        else:
            length = _control_propery_request_len(
                self._xu_control, 2, self._xu_node_index)
        if length == 384:
            pass
        elif length == 64:
            self._dataBufLen = 64
            self._resize_data_buf()
        else:
            raise Exception("length check failed: {} instead of 384/64".
                            format(length))
        ViveTracker._logger.info("vive tracker detected")

    def _activate_tracker(self: 'ViveTracker') -> None:
        """Activate tracker.

        Sets parameters and enables data stream."""
        ViveTracker._logger.info("activate vive tracker")

        ViveTracker._logger.info("-> disable stream")
        self._set_cur(self._dataTest)
        self._set_enable_stream(False)
        time.sleep(0.25)

        ViveTracker._logger.info("-> set camera parameters")
        self._set_cur(self._dataTest)
        self._set_register_sensor(0x00, 0x40)
        self._set_register_sensor(0x08, 0x01)
        self._set_register_sensor(0x70, 0x00)
        self._set_register_sensor(0x02, 0xff)
        self._set_register_sensor(0x03, 0xff)
        self._set_register_sensor(0x04, 0xff)
        self._set_register_sensor(0x0e, 0x00)
        self._set_register_sensor(0x05, 0xb2)
        self._set_register_sensor(0x06, 0xb2)
        self._set_register_sensor(0x07, 0xb2)
        self._set_register_sensor(0x0f, 0x03)

        ViveTracker._logger.info("-> enable stream")
        self._set_cur(self._dataTest)
        self._set_enable_stream(True)
        time.sleep(0.25)

    def _deactivate_tracker(self: 'ViveTracker') -> None:
        """Deactivate tracker.

        Disables data stream.
        """
        ViveTracker._logger.info("deactivate vive tracker")

        ViveTracker._logger.info("SKIPPED")
        """
        ViveTracker._logger.info("-> disable stream")
        self._set_cur(self._dataTest)
        self._set_enable_stream(False)
        time.sleep(0.25)
        """
