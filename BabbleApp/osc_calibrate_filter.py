import numpy as np
from enum import IntEnum
from utils.misc_utils import playSound
import os

from lang_manager import LocaleStringManager as lang

class CamId(IntEnum):
    CAM = 0
    SETTINGS = 1

class EKFBlendShapeCalibrator:
    def __init__(self, num_blendshapes):
        self.num_blendshapes = num_blendshapes

        self.x = np.zeros((num_blendshapes * 2, 1))
        self.x[:num_blendshapes, 0] = 0.5
        self.x[num_blendshapes:, 0] = 0.1

        self.P = np.eye(num_blendshapes * 2) * 0.1
        self.Q = np.eye(num_blendshapes * 2) * 1e-4
        self.R = np.eye(num_blendshapes) * 0.01

    def update(self, measurement):
        measurement = np.clip(measurement, 0, 1).reshape(-1, 1)

        F = np.eye(self.num_blendshapes * 2)
        x_pred = F @ self.x
        P_pred = F @ self.P @ F.T + self.Q

        H = np.zeros((self.num_blendshapes, self.num_blendshapes * 2))
        H[:, :self.num_blendshapes] = np.eye(self.num_blendshapes)

        y = measurement - H @ x_pred
        S = H @ P_pred @ H.T + self.R
        K = P_pred @ H.T @ np.linalg.inv(S)

        self.x = x_pred + K @ y
        self.P = (np.eye(self.num_blendshapes * 2) - K @ H) @ P_pred

        mean = self.x[:self.num_blendshapes, 0]
        std = np.sqrt(np.abs(self.x[self.num_blendshapes:, 0])) + 1e-6

        calibrated = (measurement.flatten() - mean) / (3 * std)
        calibrated = np.clip(calibrated * 0.5 + 0.5, 0, 1)

        confidence = np.exp(-np.square(y.flatten() / std))

        return calibrated, confidence

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
            self.calibrator = EKFBlendShapeCalibrator(num_blendshapes=len(array))

        calibrated, confidence = self.calibrator.update(array)

        if self.settings and hasattr(self.settings, 'continuous_calibration'):
            self.continuous_enabled = self.settings.continuous_calibration

        if self.continuous_enabled:
            self.calibrated_array = calibrated
            self.confidence = confidence

            if hasattr(self.settings, 'calib_array'):
                mean = self.calibrator.x[:len(array), 0]
                std = np.sqrt(np.abs(self.calibrator.x[len(array):, 0]))
                self.settings.calib_array = np.array2string(np.vstack((mean, std)), separator=",")
                if hasattr(self.settings, 'main_config') and hasattr(self.settings.main_config, 'save'):
                    self.settings.main_config.save()

            return self.calibrated_array
        else:
            self.calibrated_array = np.clip(array, 0, 1)
            self.confidence = np.ones_like(array)
            return self.calibrated_array

    def get_outputs(self):
        return self.calibrated_array, self.raw_array, self.confidence
