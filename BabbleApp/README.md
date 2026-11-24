# ProjectBabble
A Mouth tracking system for VR, 100% Opensource!

Currently the architecture is a modified efficientnetv2-b0 training on blenshapes from ARKit! The model outputs 31 blenshapes of which most cross over with SRanipals blendshapes.

### One thing to note
1. This model is not a 1 to 1 translation to SRanipal blenshapes. While most blendshapes do cross over with SRanipal cheek and tounge movements are limited.

### How to run
Go to the releases tab, download the latest exe. Clone this repo, and then move the calibration file (calib.json) to the same location as the exe. Next get the .onnx model in the repo and move it to the same location as the exe. Run the exe and enjoy!

### Running from source (Windows, macOS, Linux)
The UI is built with [Kivy](https://kivy.org), so the same code runs on every desktop platform and on Android. Requires Python 3.12.
```
pip install -r requirements.txt
python babbleapp.py
```
Package a desktop build with `pyinstaller babbleapp.spec`.

If the Chinese locales render as boxes, point `BABBLE_FONT` at a font file with CJK glyphs (the app searches the usual system fonts automatically).

### Android
Android builds use [buildozer](https://buildozer.readthedocs.io) (run on Linux, macOS or WSL2):
```
buildozer -v android debug
```
* ONNX Runtime isn't available for python-for-android, so on Android the model runs on OpenCV's DNN module. That needs a constant-folded copy of each model, created on a desktop machine with
  `python tools/export_opencv_model.py Models/<model folder>` (writes `onnx/model.opencv.onnx`). The same fallback is used on any desktop where `onnxruntime` isn't installed.
* Only network camera addresses (e.g. `http://<ip>/`) work on Android; USB/UVC cameras, serial devices and the Vive Facial Tracker need desktop OS APIs.

### PLEASE HIT THE TURN OFF CALIBRATION BUTTON UNTILL FURTHER NOTICE
It ruins the model's quality 

### Warranty
Lol 

### Credit 

Thank you to dfgHiatus#7426 for providing the unity demo as well as the intergrations with other apps!

Thank you to Rames The Generic#3540 who made the dataset, tested and evaluated the performence for the models, and for being awesome!

Copyright (c) 2022 Sameer Suri
