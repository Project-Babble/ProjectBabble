from PIL import Image, ImageFilter
import os
class EncodeDecode():
    def float_to_uint24(self, f):
        f = round(f, 8)
        f_clamped = max(0, min(1, f))
        uint24 = int(f_clamped * ((1 << 24) - 1))
        return uint24
    
    def uint24_to_float(self, uint24):
        f = uint24 / ((1 << 24) - 1)
        return f

    def encode(self, f, index):  # uint24 to blender pixel (1.0, 1.0, 1.0) RGB
        hex_str = format(f, '06x')
        hex_str = list(hex_str.strip(" "))
        #bpy.data.scenes["Scene"].node_tree.nodes["Group.002"].inputs[index].default_value = ((int('0x' + hex_str[0] + hex_str[1], 0) / 255),(int('0x' + hex_str[2] + hex_str[3], 0) / 255),(int('0x' + hex_str[4] + hex_str[5], 0) / 255),1)
        return ((int('0x' + hex_str[0] + hex_str[1], 0) / 255),(int('0x' + hex_str[2] + hex_str[3], 0) / 255),(int('0x' + hex_str[4] + hex_str[5], 0) / 255),1)

    def decode(self, pixel):    # Pixel to uint24 (255, 255, 255) RGB
        output_hex = ('0x' + hex(pixel[0]).replace('0x', '').rjust(2, "0") + hex(pixel[1]).replace('0x', '').rjust(2, "0") + hex(pixel[2]).replace('0x', '').rjust(2, "0"))
        output_hex = int(output_hex, 0)
        return(output_hex)
    
def get_shapes(ed, img):    
    px = img.load()
    output = ed.decode(px[0, 256])  # Shape count
    shapes = []
    for i in range(output):
        uint = ed.decode(px[(i + 1), 256])
        shapes.append(ed.uint24_to_float(uint))
    return shapes
        
shape_index = ["cheekPuff", "jawOpen", "jawForward", "jawLeft", "jawRight", "noseSneerLeft", "noseSneerRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", 
"mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmileLeft", 
"mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", 
"mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthStretchLeft", 
"mouthStretchRight", "tongueOut"]

path = r'Z:/BabbleDataGeneration/BabbleDataGeneration/render/'
dir_list = os.listdir(path)
ed = EncodeDecode()
shapes = []
'''
for i in range(len(dir_list)):
    img = Image.open(path + dir_list[i])
    shapes.append(get_shapes(ed, img))
'''
box = (0, 0, 256, 256)
img = Image.open(path + dir_list[1]).crop(box)
img = img.filter(ImageFilter.GaussianBlur(1.5))
#box = (0, 0, 256, 256)
#img = img.crop(box)
img.show()


print(shapes)
