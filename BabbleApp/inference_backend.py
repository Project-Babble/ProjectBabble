"""
Model inference backends.

ONNX Runtime is used whenever it is installed (Windows, macOS, Linux). On platforms where it is
not available, most notably Android (python-for-android has no onnxruntime recipe), inference
falls back to OpenCV's DNN module, which ships with the OpenCV recipe.

OpenCV DNN cannot evaluate the dynamic "same" padding sub-graphs in the exported models, so it
loads a constant-folded copy of the model (``onnx/model.opencv.onnx``). Generate it on a desktop
machine with ``python tools/export_opencv_model.py <model dir>``.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

try:
    import onnxruntime as ort
except ImportError:  # Android, or a desktop install without onnxruntime
    ort = None

ONNX_MODEL = os.path.join("onnx", "model.onnx")
OPENCV_MODEL = os.path.join("onnx", "model.opencv.onnx")


class OnnxRuntimeBackend:
    name = "ONNX Runtime"

    def __init__(self, model_dir, threads, providers, provider_options=None):
        ort.disable_telemetry_events()
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = threads
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        # ~3% savings worth ~6ms avg latency. Not noticeable at 60fps?
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.enable_mem_pattern = False
        self.sess = ort.InferenceSession(
            os.path.join(model_dir, ONNX_MODEL),
            opts,
            providers=providers,
            provider_options=provider_options,
        )
        self.input_name = self.sess.get_inputs()[0].name
        self.output_name = self.sess.get_outputs()[0].name

    def infer(self, frame: np.ndarray) -> np.ndarray:
        """Run the model on a (1, 1, 224, 224) float32 tensor, returning the first output row."""
        return self.sess.run([self.output_name], {self.input_name: frame})[0][0]


class OpenCVDnnBackend:
    name = "OpenCV DNN"

    def __init__(self, model_dir, threads):
        import cv2

        path = os.path.join(model_dir, OPENCV_MODEL)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{path} not found. ONNX Runtime is unavailable on this platform, so the "
                "constant-folded model is required (see tools/export_opencv_model.py)."
            )
        cv2.setNumThreads(max(1, int(threads)))
        self.net = cv2.dnn.readNetFromONNX(path)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    def infer(self, frame: np.ndarray) -> np.ndarray:
        self.net.setInput(np.ascontiguousarray(frame, dtype=np.float32))
        return self.net.forward().reshape(-1)


def create_backend(model_dir, threads=2, use_gpu=False, gpu_index=0, providers=None):
    """Create the best available inference backend for ``model_dir``."""
    if ort is not None:
        if use_gpu and providers:
            available = set(ort.get_available_providers())
            chosen = [p for p in providers if p in available] or ["CPUExecutionProvider"]
            options = [
                {"device_id": gpu_index} if p in ("CUDAExecutionProvider", "DmlExecutionProvider") else {}
                for p in chosen
            ]
            return OnnxRuntimeBackend(model_dir, threads, chosen, options)
        return OnnxRuntimeBackend(model_dir, threads, ["CPUExecutionProvider"])
    return OpenCVDnnBackend(model_dir, threads)
