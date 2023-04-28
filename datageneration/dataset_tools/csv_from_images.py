import os
from PIL import Image

class EncodeDecode():
    def float_to_uint24(self, f):
        f = round(f, 8)
        f_clamped = max(0, min(1, f))
        uint24 = int(f_clamped * ((1 << 24) - 1))
        return uint24
    
    def uint24_to_float(self, uint24):
        f = uint24 / ((1 << 24) - 1)
        return f

    def encode(self, f, index):  # uint24 to blender pixel (1.0, 1.0, 1.0) 
        hex_str = format(f, '06x')
        hex_str = list(hex_str.strip(" "))
        #print(hex_str)
        #bpy.data.scenes["Scene"].node_tree.nodes["Group.002"].inputs[index].default_value = ((int('0x' + hex_str[0] + hex_str[1], 0) / 255),(int('0x' + hex_str[2] + hex_str[3], 0) / 255),(int('0x' + hex_str[4] + hex_str[5], 0) / 255),1)
        return ((int('0x' + hex_str[0] + hex_str[1], 0) / 255),(int('0x' + hex_str[2] + hex_str[3], 0) / 255),(int('0x' + hex_str[4] + hex_str[5], 0) / 255),1)

    def decode(self, pixel):    # Pixel to uint24 (255, 255, 255)
        output_hex = ('0x' + hex(pixel[0]).replace('0x', '').rjust(2, "0") + hex(pixel[1]).replace('0x', '').rjust(2, "0") + hex(pixel[2]).replace('0x', '').rjust(2, "0"))
        output_hex = int(output_hex, 0)
        return(output_hex)

# Path to subdirectory containing text files
path_to_files = "X:/Downloads/render/render/"

# Output file name
output_file = "babble_dataset.csv"

# Header row
header = str(["cheekPuff", "jawOpen", "jawForward", "jawLeft", "jawRight", "noseSneerLeft", "noseSneerRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", 
"mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmileLeft", 
"mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", 
"mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthStretchLeft", 
"mouthStretchRight", "tongueOut", "filename"])
header = header.replace("'", "")
header = header.replace("[", "")
header = header.replace("]", "")
header = header.replace(' ', "")


# Open output file for writing and write header row

shape_index = ["cheekPuff", "jawOpen", "jawForward", "jawLeft", "jawRight", "noseSneerLeft", "noseSneerRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", 
"mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmileLeft", 
"mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", 
"mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthStretchLeft", 
"mouthStretchRight", "tongueOut"]

def get_shapes(ed, img):    
    px = img.load()
    output = ed.decode(px[0, 256])  # Shape count
    shapes = []
    for i in range(output):
        uint = ed.decode(px[(i + 1), 256])  # Skip the bottom left pixel because it's a uint24 of the shape count
        shapes.append(ed.uint24_to_float(uint))
    return shapes

ed = EncodeDecode()
shape_defs = dict(              # 31 shapes
    cheekPuff = [],
    jawOpen = [],
    jawForward = [],     # added
    jawLeft = [],     # added
    jawRight = [],     # added
    noseSneerLeft = [], # added
    noseSneerRight = [], # added
    mouthFunnel = [],     # added
    mouthPucker = [], # fixed in vrcft master
    mouthLeft = [],     # added
    mouthRight = [],     # added
    mouthRollUpper = [],     # fixed in vrcft master
    mouthRollLower = [],     # fixed in vrcft master
    mouthShrugUpper = [],     # added
    mouthShrugLower = [],     # added
    mouthClose = [],             # MUST BE EQUAL TO jawOpen
    mouthSmileLeft = [],     # added
    mouthSmileRight = [],    # added
    mouthFrownLeft = [],     # added
    mouthFrownRight = [],     # added
    mouthDimpleLeft = [],   # added
    mouthDimpleRight = [],      # added
    mouthUpperUpLeft = [],      # added		
    mouthUpperUpRight = [],      # added
    mouthLowerDownLeft = [], 	 # added	
    mouthLowerDownRight = [],      # added
    mouthPressLeft = [],      # added
    mouthPressRight = [],      # added
    mouthStretchLeft = [],     # added
    mouthStretchRight = [],    # added
    tongueOut = [], 
    filename = []
)

count = 0
with open(output_file, "w", buffering=10000) as outfile:
    outfile.write(header)
    # Loop over all files in subdirectory
    for filename in os.listdir(path_to_files):
        # Only process files with .csv extension
        if filename.endswith(".png"):
            # Read data from input file and write to output file
            data = []
            img = Image.open(path_to_files + filename)
            data = get_shapes(ed, img)
            data.append(path_to_files + filename)
            data = str(data)
            data = data.replace("'", "")
            data = data.replace("[", "")
            data = data.replace("]", "")
            data = data.replace(' ', "")
            contents = data


            if count == 0:
                outfile.write(f"\n{contents}\n")
            else:
                outfile.write(f"{contents}\n")
            print(f"Combined {count} files!")
            count += 1
