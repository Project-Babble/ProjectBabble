import numpy as np

from enum import IntEnum
from utils.misc_utils import PlaySound, SND_FILENAME, SND_ASYNC

class EyeId(IntEnum):
    RIGHT = 0
    LEFT = 1
    BOTH = 2
    SETTINGS = 3


class cal():
    def cal_osc(self, array):

        if self.calibration_frame_counter == 0:
            self.calibration_frame_counter = None
            lower_threshold = np.percentile(self.calibrate_config, 1)
            upper_threshold = np.percentile(self.calibrate_config, 99)
            self.calibrate_config = self.calibrate_config[(self.calibrate_config >= lower_threshold) & (self.calibrate_config <= upper_threshold)]

            # Find maximum and minimum values in the array
            max_values = np.amax(self.calibrate_config, axis=1)
            min_values = np.amin(self.calibrate_config, axis=1)
            result = np.column_stack((min_values, max_values))
            result_flat = result.flatten()

            print("[INFO] Calibration completed.")
            #print(self.calibrate_config)
            self.settings.calib_array = result_flat
            PlaySound('Audio/completed.wav', SND_FILENAME | SND_ASYNC)
        if self.calibration_frame_counter == 10:

            self.calibration_frame_counter -= 1

        elif self.calibration_frame_counter != None:


            self.calibrate_config = np.vstack((self.calibrate_config, array.T))
           # np.append(self.calibrate_config, array.reshape(-1, 1), axis=1)

            self.calibration_frame_counter -= 1
        varcount = 0
        filtered_output = []
        if self.settings.calib_array != None:
            for value in array:
                low_v = self.settings.calib_array[varcount][0]
                high_v = self.settings.calib_array[varcount][1]
                filterv = (value - low_v) / (high_v - low_v)
                filtered_output.append(filterv)
                varcount += 1
            array = filtered_output
        return array