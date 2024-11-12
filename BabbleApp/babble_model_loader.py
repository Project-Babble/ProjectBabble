import os
import json
os.environ["OMP_NUM_THREADS"] = "1"
import onnxruntime as ort
import cv2
import numpy as np
import utils.image_transforms as transforms


def run_model(self, embedding, netural_blends):
    if self.runtime in ("ONNX", "Default (ONNX)"):
        frame = cv2.resize(self.current_image_gray, (256, 256))
        frame = transforms.to_tensor(frame)
        frame = transforms.unsqueeze(frame, 0)
        frame = transforms.normalize(frame)
        frame = frame * 2 - 1 
        #make the image 3 channels but concat
        frame = np.concatenate((frame, frame, frame), axis=1)
        


        output_emb = self.sess_encoder.run([self.output_name_encoder], {self.input_name_encoder: frame})
        output_emb = output_emb[0]
        #concat output_emb, and embedding from 1,128 in both to 1.256
        output_emb = np.concatenate((output_emb, embedding), axis=-1)
        #pass it to the model head 

        output = self.sess_head.run([self.output_name_head], {self.input_name_head: output_emb})

        output = output[0][0] - netural_blends
    
        output = self.one_euro_filter(output)

        # for i in range(len(output)):  # Clip values between 0 - 1
        #     output[i] = max(min(output[i], 1), 0)
        ## Clip values between 0 - 1
        output = np.clip(output, 0, 1)
    self.output = output

def run_model_embeding(self):
    if self.runtime in ("ONNX", "Default (ONNX)"):
        #load BabbleApp\UserData\neutral_frame.jpg
        frame = cv2.imread("UserData/neutral_frame.jpg")

        #convert to black and white
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #convert back to color
        #frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        if frame is None:
            print("No frame")
            frame = np.zeros((256, 256, 3), dtype=np.uint8)
        frame = cv2.resize(frame, (256, 256))
        frame = transforms.to_tensor(frame)
        frame = transforms.unsqueeze(frame, 0)
        frame = transforms.normalize(frame)
        frame = frame * 2 - 1 
        
        #convert to color by duplicating the channels
        frame = np.concatenate((frame, frame, frame), axis=1)
        
        out = self.sess_encoder.run([self.output_name_encoder], {self.input_name_encoder: frame})
        out = out[0]
        output_emb = np.concatenate((out, out), axis=-1)
        output_netural = self.sess_head.run([self.output_name_head], {self.input_name_head: output_emb})


        output = out
        output_netural = output_netural[0][0]
        #save to np array in UserData
        np.save("UserData/model_embeding.npy", output) #TODO: Expose this in settings
        np.save("UserData/netural.npy", output_netural) #TODO: Expose this in settings