import os
import json
os.environ["OMP_NUM_THREADS"] = "1"
import onnxruntime as ort
import time
import PySimpleGUI as sg
import cv2
import numpy as np
from pythonosc import udp_client
from torchvision.transforms.functional import to_grayscale
import PIL.Image as Image
from torchvision import transforms
from threading import Thread
from one_euro_filter import OneEuroFilter

def run_model(self):



    min_cutoff = self.config.gui_min_cutoff #15.5004
    beta = self.config.gui_speed_coefficient #0.62
    noisy_point = np.array([45])
    filter = OneEuroFilter(
        noisy_point,
        min_cutoff=min_cutoff,
        beta=beta
    )

    frame = cv2.resize(self.current_image_gray, (256, 256))
    # make it pil
    frame = Image.fromarray(frame)
    # make it grayscale
    frame = to_grayscale(frame)
    # make it a tensor
    frame = transforms.ToTensor()(frame)
    # make it a batch
    frame = frame.unsqueeze(0)
    # make it a numpy array
    frame = frame.numpy()

    out = self.sess.run([self.output_name], {self.input_name: frame})
    #end = time.time()
    output = out[0]
    output = output[0]
    output = filter(output)
    for i in range(len(output)):  # Clip values between 0 - 1
        output[i] = max(min(output[i], 1), 0)
    self.output = output