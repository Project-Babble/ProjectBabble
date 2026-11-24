import os

os.environ["OMP_NUM_THREADS"] = "1"
import cv2
import numpy as np
import utils.image_transforms as transforms


def run_model(self):
    if self.runtime in ("ONNX", "Default (ONNX)"):
        frame = cv2.resize(self.current_image_gray, (224, 224))
        frame = transforms.to_tensor(frame)
        frame = transforms.unsqueeze(frame, 0)
        output = self.sess.infer(frame)  # see inference_backend.py

        output = self.one_euro_filter(output)

        # for i in range(len(output)):  # Clip values between 0 - 1
        #     output[i] = max(min(output[i], 1), 0)
        ## Clip values between 0 - 1
        output = np.clip(output, 0, 1)
        self.output = output
