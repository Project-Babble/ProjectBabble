# ProjectBabble: Data generation
A Mouth tracking system for VR, 100% Opensource!

Currently the most of the generated blenshapes are from ARKit! The model outputs 45 blenshapes of which most cross over with SRanipals blendshapes.

## Description
Contains all of the tools and source files for creating the synthetic face dataset for training. 
The current scripts in the V4.1 folder and separated in two different folders. The "Blender" folder contains scripts intended to be run in the provided Blender scenes. The "Processing" folder contains scripts for extracing shape values from the images into a csv file or in the console for inspection. 

### One thing to note
1. At the moment, this only contains scripts and scenes for generaing lower face blendshape datasets. Support for the full face and landmarks is planned for the future. 


## Usage

### DatasetGeneratorV4.1:
#### Generates the randomized shapes to be rendered. 
1. Open one of the blender scenes and import the script from the scripting tab.
2. Adjust the amount of desired images with the frame range in the Output Properties tab on the right
3. Change the "mesh" variable with the name of the corrisponding avatar (ex. "Babble_CA_M").
4. (Optional) Toggle the Blender system console by going Window ==> Toggle System Console. Useful for seeing the generation progress 
5. Press the play button at the top of the blender text editor and wait for the script to finish. 
  #### Note: The script can be stopped at any time by pressing Ctrl + C in the console. Once saved, the file can be rendered at any time by rendering as an animation. 
  
### csv_from_images:
#### Extracts blendshape values encoded in the rendered images and write them to a csv file. 
1. Install dependences: pip install Pillow
2. Edit the "path_to_files" variable to the directory with the rendered images.
3. Run the script


## Outputs
| Blendshapes        |
| ------------- |
|CheekSquintLeft|
|CheekSquintRight|
|CheekPuffLeft|
|CheekPuffRight|
|NoseSneerLeft|
|NoseSneerRight|
|CheekSuckLeft|
|CheekSuckRight|
|LipSuckUpperRight|
|LipSuckUpperLeft|
|LipSuckLowerRight|
|LipSuckLowerLeft|
|JawOpen|
|JawLeft|
|JawRight|
|JawForward|
|LipFunnelUpperRight|
|LipFunnelUpperLeft|
|LipFunnelLowerRight|
|LipFunnelLowerLeft|
|LipPuckerLeft|
|LipPuckerRight|
|MouthApeShape|
|MouthClose|
|MouthUpperLeft|
|MouthLowerLeft|
|MouthUpperRight|
|MouthLowerRight|
|MouthSmileLeft|
|MouthSmileRight|
|MouthFrownLeft|
|MouthFrownRight|
|MouthDimpleLeft|
|MouthDimpleRight|
|MouthRaiserUpper|
|MouthRaiserLower|
|MouthShrugLower|
|MouthUpperUpLeft|
|MouthUpperUpRight|
|MouthLowerDownLeft|
|MouthLowerDownRight|
|MouthPressLeft|
|MouthPressRight|
|MouthTightenerLeft|
|MouthTightenerRight|
|MouthStretchLeft|
|MouthStretchRight|
|TongueOut|
|TongueDown|
|TongueUp|
|TongueLeft|
|TongueRight|
|TongueRoll|
