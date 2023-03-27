import os
import shutil
import threading

# specify the directories
source_dir = "X:\\Documents\\GitHub\\ProjectBabble\\datageneration\\training\\lipimages"
destination_dir = "C:\\Users\\epicm\\Desktop\\BabbleTraining\\lipimages"

# get a list of all files in the source directory
files = os.listdir(source_dir)

# loop through each file and copy it to the destination directory
for file_name in files:
    # construct the full path to the file
    source_file = os.path.join(source_dir, file_name)
    destination_file = os.path.join(destination_dir, file_name)
    
    # copy the file to the destination directory
    shutil.copy2(source_file, destination_file)
    
print("Files copied successfully!")