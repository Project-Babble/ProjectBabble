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
        #print(self.calibration_frame_counter)
        if self.calibration_frame_counter == 0:

            self.calibration_frame_counter = None
            values = np.array(self.val_list)

            # Initialize the min_max_array with shape (2, num_outputs)
            num_outputs = values.shape[1]
            self.min_max_array = np.zeros((2, num_outputs))

            # Iterate over each output index
            for i in range(num_outputs):
                # Calculate the lower and upper thresholds for the current index
                lower_threshold = np.percentile(values[:, i], 1)
                upper_threshold = np.percentile(values[:, i], 99)

                # Filter out values within the thresholds for the current index
                filtered_values = values[(values[:, i] >= lower_threshold) & (values[:, i] <= upper_threshold), i]

                # Extract the minimum and maximum values for the current index
                min_value = np.min(filtered_values)
                max_value = np.max(filtered_values)

                # Store the min and max values in the min_max_array
                self.min_max_array[0, i] = min_value
                self.min_max_array[1, i] = max_value

                self.settings.calib_array = self.min_max_array
            print("[INFO] Calibration completed.")

            PlaySound('Audio/completed.wav', SND_FILENAME | SND_ASYNC)
        if self.calibration_frame_counter == 10:

            self.calibration_frame_counter -= 1
        elif self.calibration_frame_counter != None:

            self.val_list.append(array)


           # self.calibrate_config = np.vstack((self.calibrate_config, array.T))
           # np.append(self.calibrate_config, array.reshape(-1, 1), axis=1)

            self.calibration_frame_counter -= 1
        varcount = 0
        filtered_output = []
        if self.settings.calib_array is not None and np.any(self.settings.calib_array):
            calibrated_array = np.zeros_like(array)
            for i, value in enumerate(array):
                min_value = self.min_max_array[0, i]
                max_value = self.min_max_array[1, i]

                if min_value == max_value:
                    calibrated_value = 0.0  # Set to a default value (can be adjusted as needed)
                else:
                    calibrated_value = (value - min_value) / (max_value - min_value)

                calibrated_array[i] = calibrated_value
            array = calibrated_array
        return array