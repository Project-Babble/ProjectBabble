import numpy as np
from math import log
from enum import IntEnum
from utils.misc_utils import PlaySound, SND_FILENAME, SND_ASYNC

class CamId(IntEnum):
    CAM = 0
    SETTINGS = 1

class cal():

    def cal_osc(self, array):
        #print(self.calibration_frame_counter)
        if self.calibration_frame_counter == 0:
            if not self.config.use_n_calibration:
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
                self.settings.calib_array = np.array2string(self.min_max_array, separator=',')
                self.config_class.save()
                print("[INFO] Calibration completed.")

                PlaySound('Audio/completed.wav', SND_FILENAME | SND_ASYNC)

            if self.config.use_n_calibration:
                self.calibration_frame_counter = None
                values = np.array(self.val_list)
                deadzone_value = -0.01   # Maybe adjust from app????
                # Initialize the min_max_array with shape (2, num_outputs)
                num_outputs = values.shape[1]
                self.min_max_array = np.zeros((2, num_outputs))
                lower_threshold = np.clip([np.mean(values, axis = 0) + deadzone_value], 0, 1)
                upper_threshold = np.ones((1, num_outputs)) # We don't need to adjust the max values. 
                print(lower_threshold)
                print(upper_threshold)
                self.min_max_array = np.array([lower_threshold, upper_threshold])
                self.settings.calib_array = np.array2string(self.min_max_array, separator=',')
                self.config_class.save()
                print("[INFO] Calibration completed.")






        elif self.calibration_frame_counter != None:
            self.val_list.append(array)
            self.calibration_frame_counter -= 1
        

        if self.settings.calib_array is not None and self.config.use_calibration:
            self.min_max_array = np.fromstring(self.settings.calib_array.replace('[', '').replace(']', ''), sep=',')
            self.min_max_array = self.min_max_array.reshape((2, 45))

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

        if self.settings.calib_array is not None and self.config.use_n_calibration:
            self.min_max_array = np.fromstring(self.settings.calib_array.replace('[', '').replace(']', ''), sep=',')
            self.min_max_array = self.min_max_array.reshape((2, 45))

            calibrated_array = np.zeros_like(array)
            for i, value in enumerate(array):
                min_value = self.min_max_array[0, i]

                calibrated_value = (value - min_value) / (1.0 - min_value)

                calibrated_array[i] = calibrated_value
            array = calibrated_array
        print(array[4])
        #array[4] = log((np.clip(array[4]*10,0,10))+1.0, 11) Log Filter: Move to filter system. 
        return np.clip(array,0,1)   # Clamp outputs between 0-1