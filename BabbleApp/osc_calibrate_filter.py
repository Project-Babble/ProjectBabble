import numpy as np
from math import log
from enum import IntEnum
from utils.misc_utils import playSound
import os

from lang_manager import LocaleStringManager as lang

class CamId(IntEnum):
    CAM = 0
    SETTINGS = 1

class BlendShapeCalibrator:
    """
    Continuous calibrator for blend shape model outputs.
    Tracks independent minimum and maximum values for each blend shape to robustly calibrate and normalize outputs.
    """
    def __init__(self, num_blendshapes, alpha=0.1, beta=0.1, threshold_multiplier=2.0):
        self.num_blendshapes = num_blendshapes
        self.alpha = alpha
        self.beta = beta
        self.multiplier = threshold_multiplier
        self.initialized = False
        self.min = np.full(num_blendshapes, np.inf)
        self.max = np.full(num_blendshapes, -np.inf)
        self.mean = np.zeros(num_blendshapes)
        self.variance = np.zeros(num_blendshapes)
        self.threshold = np.zeros(num_blendshapes)
        self.confidence = np.ones(num_blendshapes)
        self.sample_count = 0

    def update(self, input_array):
        input_array = np.asarray(input_array)
        if input_array.shape[0] != self.num_blendshapes:
            raise ValueError(f"Expected input of length {self.num_blendshapes}, got {input_array.shape[0]}")
        if not self.initialized:
            self.min = input_array.astype(float).copy()
            self.max = input_array.astype(float).copy()
            self.mean = input_array.astype(float).copy()
            self.variance = np.zeros(self.num_blendshapes)
            self.initialized = True
        # Update min and max independently
        self.min = np.minimum(self.min, input_array)
        self.max = np.maximum(self.max, input_array)
        # Optionally update mean/variance for confidence (legacy)
        diff = input_array - self.mean
        std = np.sqrt(self.variance)
        self.threshold = self.multiplier * std
        epsilon = 1e-6
        denom = self.threshold + epsilon
        confidence = np.exp(-np.abs(diff) / denom)
        # Only update mean if all (or most) blendshapes are below a low threshold (neutral)
        neutral_threshold = 0.15
        neutral_mask = np.abs(input_array) < neutral_threshold
        if np.sum(neutral_mask) >= int(0.8 * self.num_blendshapes):
            self.mean[neutral_mask] = self.alpha * input_array[neutral_mask] + (1 - self.alpha) * self.mean[neutral_mask]
        # Always update variance for tracking
        self.variance = self.beta * (diff ** 2) + (1 - self.beta) * self.variance
        self.confidence = confidence
        self.sample_count += 1
        return self.min, self.max, self.confidence

class cal:
    def __init__(self, settings=None):
        self.calibrator = None
        self.settings = settings
        self.calibrated_array = None
        self.raw_array = None
        self.confidence = None
        self.continuous_enabled = getattr(settings, 'continuous_calibration', True) if settings else True

    def cal_osc(self, array):
        self.raw_array = array
        if self.calibrator is None or (self.calibrator.num_blendshapes != len(array)):
            self.calibrator = BlendShapeCalibrator(num_blendshapes=len(array))
        if self.settings and hasattr(self.settings, 'continuous_calibration'):
            self.continuous_enabled = self.settings.continuous_calibration
        if self.continuous_enabled:
            min_vals, max_vals, confidence = self.calibrator.update(array)
            # Normalize using running min and max
            denom = (max_vals - min_vals)
            denom[denom == 0] = 1e-6  # Prevent division by zero
            calibrated = (array - min_vals) / denom
            self.calibrated_array = np.clip(calibrated, 0, 1)
            self.confidence = confidence
            # --- Begin patch: propagate calibration to config and widget ---
            if hasattr(self.settings, 'calib_array'):
                self.settings.calib_array = np.array2string(np.vstack((min_vals, max_vals)), separator=",")
                if hasattr(self.settings, 'main_config') and hasattr(self.settings.main_config, 'save'):
                    self.settings.main_config.save()
            # --- End patch ---
            print(self.confidence)
            return self.calibrated_array
        else:
            self.calibrated_array = np.clip(array, 0, 1)
            self.confidence = np.ones_like(array)
            return self.calibrated_array

    def get_outputs(self):
        return self.calibrated_array, self.raw_array, self.confidence

    def get_outputs(self):
        return self.calibrated_array, self.raw_array, self.confidence
