import os

# specify the directories
dir1 = "C:\\Users\\epicm\\Desktop\\BabbleTraining\\lipcsv"
dir2 = "C:\\Users\\epicm\\Desktop\\BabbleTraining\\lipimages"

# get a list of all files in the first directory
files1 = [os.path.splitext(file)[0] for file in os.listdir(dir1)]

# get a list of all files in the second directory
files2 = [os.path.splitext(file)[0] for file in os.listdir(dir2)]

# find the files in the first directory that don't have a pair in the second directory
for file1 in files1:
    if file1 not in files2:
        print(f"{file1} doesn't have a pair in the second directory")

# find the files in the second directory that don't have a pair in the first directory
for file2 in files2:
    if file2 not in files1:
        print(f"{file2} doesn't have a pair in the first directory")
