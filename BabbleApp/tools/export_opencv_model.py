"""
Create the OpenCV-DNN compatible copy of a Babble model (``onnx/model.opencv.onnx``).

ONNX Runtime isn't available on Android, so the app falls back to OpenCV's DNN module there.
OpenCV can't execute the dynamic "same" padding sub-graphs (Shape/Ceil/...) in the exported
EfficientNet models, so this script lets ONNX Runtime constant-fold them away (the models have a
fixed 1x1x224x224 input) and checks that OpenCV produces the same output.

Run on a desktop machine with onnxruntime installed:

    python tools/export_opencv_model.py Models/EFFB0E11BS128V7.5 [more model dirs...]
"""

import os
import sys

import cv2
import numpy as np
import onnxruntime as ort


def export(model_dir):
    src = os.path.join(model_dir, "onnx", "model.onnx")
    dst = os.path.join(model_dir, "onnx", "model.opencv.onnx")
    if not os.path.exists(src):
        raise FileNotFoundError(src)

    opts = ort.SessionOptions()
    # BASIC = constant folding + redundant node elimination, using only standard ONNX ops.
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    opts.optimized_model_filepath = dst
    ort.InferenceSession(src, opts, providers=["CPUExecutionProvider"])

    # Verify OpenCV can load it and agrees with ONNX Runtime.
    sess = ort.InferenceSession(src, providers=["CPUExecutionProvider"])
    shape = [d if isinstance(d, int) else 1 for d in sess.get_inputs()[0].shape]
    x = np.random.default_rng(0).random(shape, dtype=np.float32)
    expected = sess.run(None, {sess.get_inputs()[0].name: x})[0].reshape(-1)
    net = cv2.dnn.readNetFromONNX(dst)
    net.setInput(x)
    actual = net.forward().reshape(-1)
    diff = float(np.abs(expected - actual).max())
    print(f"{dst}: max abs difference vs ONNX Runtime = {diff:.2e}")
    if diff > 1e-3:
        raise RuntimeError(f"OpenCV output differs from ONNX Runtime ({diff})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for d in sys.argv[1:]:
        export(d)
