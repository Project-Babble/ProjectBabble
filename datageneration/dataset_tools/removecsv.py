import os
import shutil

# specify the directories
source_dir = "C:\\Users\\epicm\\Desktop\\BabbleTraining\\lipimages"
destination_dir = "C:\\Users\\epicm\\Desktop\\BabbleTraining\\lipcsv"

# create the destination directory if it doesn't exist
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)

# loop through all files in the source directory
for file_name in os.listdir(source_dir):
    # check if the file is a CSV file
    if file_name.endswith('.csv'):
        # construct the full path to the file
        source_file = os.path.join(source_dir, file_name)
        destination_file = os.path.join(destination_dir, file_name)
        
        # move the file to the destination directory
        shutil.move(source_file, destination_file)
        
print("CSV files moved successfully!")