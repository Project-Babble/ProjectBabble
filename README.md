# ProjectBabble
A Mouth tracking system for VR, 100% Opensource!

Currently the architecture is a moddified mobilenetv2 training on blenshapes from ARKit! The model outputs 33 blenshapes of which most cross over with SRanipals blendshapes.

### A few things to note
1. The current version of the model may not work for your mouth as it has been trained on a not very diverse dataset. Expect this to change in newer versions. 
2. Not all blendshapes may work as there isnt enough data collected in the dataset. 
3. No detailed setup guide will be provided until later more stable versions. 
4. The (ML) model is currently un optimized so expect large amounts of CPU or GPU usage. This will be worked on in later versions



### Current setup guide 
1. Clone the repo 
2. Install the dependencies in requirements.txt with python 3.8 (or newer).
3. run model_loader_no_crop.py 
4. run the unity build in the unity build folder
5. make a netural face and move the camera around your mouth area until the avatar in the unity app makes a netural face too. 
6. Enjoy mouth tracking! 

### Credit 

Thanks to dfgHiatus#7426 for proviving the unity scripts in the demo!! 
