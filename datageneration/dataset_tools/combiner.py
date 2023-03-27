import os

# Path to subdirectory containing text files
path_to_files = "lipcsv"

# Output file name
output_file = "dataset_30K3.2_mar-23-2023_OV2640-160.csv"

# Header row
header = str(['cheekPuff','cheekSquintLeft','cheekSquintRight','noseSneerLeft','noseSneerLeft','jawOpen',
    'jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight',
    'mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose',
    'mouthSmileLeft','mouthSmileRight','mouthFrownLeft','mouthFrownRight','mouthDimpleLeft','mouthDimpleRight',
    'mouthUpperUpLeft','mouthUpperUpRight','mouthLowerDownLeft','mouthLowerDownRight','mouthPressLeft',
    'mouthPressRight','mouthStretchLeft','mouthStretchRight','tongueOut','filename'])
header = header.replace("'", "")
header = header.replace("[", "")
header = header.replace("]", "")
header = header.replace(' ', "")

count = 0
# Open output file for writing and write header row

with open(output_file, "w", buffering=10000) as outfile:
    outfile.write(header)
    # Loop over all files in subdirectory
    for filename in os.listdir(path_to_files):
        # Only process files with .csv extension
        if filename.endswith(".csv"):
            with open(os.path.join(path_to_files, filename), "r") as infile:
                # Read data from input file and write to output file
                contents = infile.read()

                if count == 0:
                    outfile.write(f"\n{contents}\n")
                else:
                    outfile.write(f"{contents}\n")
                print(f"Combined {count} files!")
                count += 1
