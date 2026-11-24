# Android build of the Babble App.
# Build on Linux or macOS (or WSL2 on Windows):  buildozer -v android debug
#
# Notes:
#  * onnxruntime has no python-for-android recipe; the app automatically falls back to OpenCV DNN,
#    which needs Models/<model>/onnx/model.opencv.onnx (see tools/export_opencv_model.py).
#  * Only network (HTTP/MJPEG) camera sources are supported on Android; USB/UVC, serial and the
#    Vive Facial Tracker need desktop OS APIs.

[app]
title = Babble App
package.name = babbleapp
package.domain = com.projectbabble
version = 2.0.7

source.dir = .
source.include_exts = py,png,jpg,ico,json,wav,onnx,ttf,otf
source.exclude_dirs = venv,venv-3.11.11,venv-3.12.3,venv-3.12.8,build,dist,inno,Logs,tools,__pycache__,.buildozer,bin
# The plain ONNX models are only used by onnxruntime (desktop); ship the OpenCV-ready copies.
source.exclude_patterns = Models/*/onnx/model.onnx,babble_settings.json,babble_settings.backup

# python3/hostpython3 are pinned to 3.12 to match the desktop build. The p4a python3 recipe takes
# any 3.11+ version; if a newer p4a release rejects it, remove the two pins to use its default.
# pydantic must be the release that matches p4a's pydantic-core recipe (2.41.4 at the time of
# writing => pydantic 2.12.3); bump both together.
requirements = python3==3.12.8,hostpython3==3.12.8,kivy==2.3.1,pyjnius,android,numpy,opencv,pillow,requests,urllib3,charset-normalizer,idna,certifi,python-osc==1.9.0,pydantic==2.12.3,pydantic-core,typing-extensions,typing-inspection,annotated-types,pyserial==3.5,colorama==0.4.6,psutil

icon.filename = %(source.dir)s/Images/logo.png
orientation = portrait, landscape, portrait-reverse, landscape-reverse
fullscreen = 0

android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE, WAKE_LOCK
# Keep the CPU awake while streaming tracking data
android.wakelock = True
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = False
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
