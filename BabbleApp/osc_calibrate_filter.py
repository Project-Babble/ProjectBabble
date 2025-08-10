import numpy as np
from math import log
from enum import IntEnum
from utils.misc_utils import playSound
import os

from lang_manager import LocaleStringManager as lang

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
        self.sample_counts = np.zeros(num_blendshapes, dtype=int)
        self.calibrated_flags = np.zeros(num_blendshapes, dtype=bool)
        self.warmup_frames = 300  # 5 seconds at 60 FPS

        self.adaptation_rate = 1.0
        self.min_adaptation_rate = 0.01
        self.adaptation_decay = 0.99998  # Slower decay for long sessions
        self.hysteresis_threshold = 0.05

        self.decay_counters = np.zeros(num_blendshapes, dtype=int)
        self.decay_threshold = 54000  # 10 minutes at 90 FPS (conservatively long)
        self.decay_levels = np.zeros(num_blendshapes)

    def update(self, input_array):
        input_array = np.asarray(input_array)
        if input_array.shape[0] != self.num_blendshapes:
            raise ValueError(f"Expected input of length {self.num_blendshapes}, got {input_array.shape[0]}")

        if self.sample_count > 0:
            self.adaptation_rate = max(self.min_adaptation_rate, self.adaptation_rate * self.adaptation_decay)

        if not self.initialized:
            self.min = input_array.astype(float).copy()
            self.max = input_array.astype(float).copy()
            self.mean = input_array.astype(float).copy()
            self.variance = np.zeros(self.num_blendshapes)
            self.initialized = True

        if self.sample_count < self.warmup_frames:
            self.min = np.minimum(self.min, input_array)
            self.max = np.maximum(self.max, input_array)
            self.mean = self.alpha * input_array + (1 - self.alpha) * self.mean
            self.sample_count += 1
            return self.min, self.max, np.ones(self.num_blendshapes), self.calibrated_flags

        neutral_threshold = 0.15
        neutral_mask = np.abs(input_array) < neutral_threshold
        active_mask = ~neutral_mask
        is_neutral_pose = np.sum(neutral_mask) >= int(0.8 * self.num_blendshapes)

        min_diff = self.min - input_array
        max_diff = input_array - self.max

        if is_neutral_pose:
            update_min_mask = (min_diff > self.hysteresis_threshold) & neutral_mask
            self.min[update_min_mask] = self.adaptation_rate * input_array[update_min_mask] + (1 - self.adaptation_rate) * self.min[update_min_mask]
            self.mean[neutral_mask] = self.alpha * input_array[neutral_mask] + (1 - self.alpha) * self.mean[neutral_mask]

        update_max_mask = (max_diff > self.hysteresis_threshold) & active_mask

        # Modify adaptation rate if shape decayed a lot
        per_shape_adaptation = np.full(self.num_blendshapes, self.adaptation_rate)
        high_decay_mask = self.decay_levels > 0.1  # Threshold for high decay
        per_shape_adaptation[high_decay_mask] = 0.5  # More aggressive update

        self.max[update_max_mask] = per_shape_adaptation[update_max_mask] * input_array[update_max_mask] + \
                                     (1 - per_shape_adaptation[update_max_mask]) * self.max[update_max_mask]

        below_max_mask = input_array < self.max * 0.9
        self.decay_counters[below_max_mask] += 1
        decay_mask = self.decay_counters > self.decay_threshold
        self.decay_levels[decay_mask] += 0.01  # track how much it's been decayed
        self.max[decay_mask] *= 0.999  # Very slow decay
        self.decay_counters[~below_max_mask] = 0
        self.decay_levels[~below_max_mask] *= 0.95  # Slowly fade decay level back down

        swap_mask = self.min > self.max
        avg = (self.min[swap_mask] + self.max[swap_mask]) / 2
        self.min[swap_mask] = avg
        self.max[swap_mask] = avg

        diff = input_array - self.mean
        self.variance = self.beta * (diff ** 2) + (1 - self.beta) * self.variance
        std = np.sqrt(self.variance) + 1e-6
        self.threshold = self.multiplier * std
        self.confidence = np.exp(-np.abs(diff) / self.threshold)

        self.sample_count += 1
        self.sample_counts += 1

        for i in range(self.num_blendshapes):
            if not self.calibrated_flags[i]:
                if (self.max[i] - self.min[i] > 1e-3 and
                    self.sample_counts[i] >= 300 and  # ~5s at 60FPS
                    self.variance[i] > 1e-4):
                    self.calibrated_flags[i] = True

        return self.min, self.max, self.confidence, self.calibrated_flags


class cal:
    def __init__(self, settings=None):
        self.calibrator = None
        self.settings = settings
        self.calibrated_array = None
        self.raw_array = None
        self.confidence = None
        self.continuous_enabled = getattr(settings, 'continuous_calibration', True) if settings else True

    def clear_calibration(self):
        self.calibrator = None
        self.calibrated_array = None
        self.raw_array = None
        self.confidence = None

    def cal_osc(self, array):
        self.raw_array = array
        if self.calibrator is None or (self.calibrator.num_blendshapes != len(array)):
            self.calibrator = BlendShapeCalibrator(num_blendshapes=len(array))
        if self.settings and hasattr(self.settings, 'continuous_calibration'):
            self.continuous_enabled = self.settings.continuous_calibration
        if self.continuous_enabled:
            min_vals, max_vals, confidence, calibrated_flags = self.calibrator.update(array)
            denom = (max_vals - min_vals)
            denom[denom == 0] = 1e-6
            calibrated = np.zeros_like(array)
            for i in range(len(array)):
                if calibrated_flags[i]:
                    calibrated[i] = (array[i] - min_vals[i]) / denom[i]
            self.calibrated_array = np.clip(calibrated, 0, 1)
            self.confidence = confidence
            if hasattr(self.settings, 'calib_array'):
                self.settings.calib_array = np.array2string(np.vstack((min_vals, max_vals)), separator=",")
                if hasattr(self.settings, 'main_config') and hasattr(self.settings.main_config, 'save'):
                    self.settings.main_config.save()
            return self.calibrated_array
        else:
            self.calibrated_array = np.clip(array, 0, 1)
            self.confidence = np.ones_like(array)
            return self.calibrated_array

    def get_outputs(self):
        return self.calibrated_array, self.raw_array, self.confidence
