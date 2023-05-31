'''
For use with the RenderSceneV3.2 blender project: https://drive.google.com/drive/folders/1fx8OhrEaV0z3oLK1KmecpEHhlRkXSiT4?usp=share_link
ARKit mouth dataset Generation Script
Made with the finest yandev logic
A rewrite definitely is required for next time :facepalm:

Randomizes the lighting setup, camera position, and blendshapes (predefined random combinations).
Each image also gets a corrisponding csv file with the generated blendshapes.
Use the combiner script to combine all the csv files into one. 



Possible mesh naming schemes for automatic blendshape generation (WIP): 
    MBLab_(Race)_(Sex)
    
Race: 
    Afro: AF
    Asian: AS
    Caucasian: CA
    Latino: LA
    
Sex:
    Female: F
    Male: M
    
Ex: MBLab_AS_M
    



How to use: 
    
1. Create a character with the MBLab plugin, randomize the facial features and finalize

2. Rename the root of the character to MBLab_SK and 
   the body mesh to an automatic blendshape generation name
   
3. Add a Copy Location modifier to the CameraRig and set the Target
   to MBLab_SK and the newly created bone slot to head
'''




import bpy
import math
import random
import csv
import copy
import os
from datetime import datetime
import time

                            # Assigning blendshapes to arkit variable names
cheekPuff = 'mouthInflate'
cheekSquintLeft = 'cheekSquint_L' # Don't use
cheekSquintRight = 'cheekSquint_R' # Don't use
noseSneerLeft = 'Expressions_cheekSneerL_max' # added
noseSneerRight = 'Expressions_cheekSneerR_max' # added
jawOpen = 'Expressions_mouthOpen_max'
jawForward = 'Expressions_jawOut_max'      # added
jawLeft = 'jawLeft'     # added
jawRight = 'jawRight'     # added
mouthFunnel = 'mouthFunnel'     # added
mouthPucker = 'mouthPucker'
mouthLeft = 'mouthLeft'     # added
mouthRight = 'mouthRight'     # added
mouthRollUpper = 'mouthRollUpper'     # added
mouthRollLower = 'Expressions_mouthLowerOut_min'     # added
mouthShrugUpper = 'mouthShrugUpper'     # added
mouthShrugLower = 'mouthShrugLower'     # added
mouthClose = 'mouthClose'             # MUST BE EQUAL TO jawOpen
mouthSmileLeft = 'mouthSmileL'     # added
mouthSmileRight = 'mouthSmileR'     # added
mouthFrownLeft = 'mouthFrownLeft'     # added
mouthFrownRight = 'mouthFrownRight'     # added
mouthDimpleLeft = 'mouthDimple_L'   # added
mouthDimpleRight = 'mouthDimple_R'      # added
mouthUpperUpLeft = 'mouthUpperUp_L'      # added				
mouthUpperUpRight = 'mouthUpperUp_R'      # added
mouthLowerDownLeft = 'mouthLowerDown_L' 	 # added	
mouthLowerDownRight = 'mouthLowerDown_R'      # added
mouthPressLeft = 'mouthPress_L'      # added
mouthPressRight = 'mouthPress_R'      # added
mouthStretchLeft = 'mouthStretch_L'     # added
mouthStretchRight = 'mouthStretch_R'    # added
tongueOut = 'tongueOut'

shapes_index = [cheekPuff, cheekSquintLeft, cheekSquintRight, noseSneerLeft, noseSneerRight, 
jawOpen, jawForward, jawLeft, jawRight, mouthFunnel, mouthPucker, mouthLeft, mouthRight, 
mouthRollUpper, mouthRollLower, mouthShrugUpper, mouthShrugLower, mouthClose, mouthSmileLeft, 
mouthSmileRight, mouthFrownLeft, mouthFrownRight, mouthDimpleLeft, mouthDimpleRight, mouthUpperUpLeft, 
mouthUpperUpRight, mouthLowerDownLeft, mouthLowerDownRight, mouthPressLeft, mouthPressRight, mouthStretchLeft, 
mouthStretchRight, tongueOut]

lables_name = ['cheekPuff','cheekSquintLeft','cheekSquintRight','noseSneerLeft','noseSneerLeft','jawOpen',
'jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight',
'mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose',
'mouthSmileLeft','mouthSmileRight','mouthFrownLeft','mouthFrownRight','mouthDimpleLeft','mouthDimpleRight',
'mouthUpperUpLeft','mouthUpperUpRight','mouthLowerDownLeft','mouthLowerDownRight','mouthPressLeft',
'mouthPressRight','mouthStretchLeft','mouthStretchRight','tongueOut','filename']


def get_objs(collection):                   # Returns all meshes in a collection
    collection = bpy.data.collections[collection]
    for obj in collection.all_objects:
        ob = bpy.data.objects[str(obj.name)]
        if ob.type == 'MESH':
            mesh_name = obj.name
            #shapekey_name = shapekey_name.split()
    return mesh_name 

def copy_all_shape_keys(source, dest):                  # Transfers Blendshapes from one mesh to another assuming they have identical geometry
    bpy.data.objects[source].select_set(True)
    bpy.data.objects[dest].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[dest]
    source = bpy.data.objects[source]
    dest = bpy.data.objects[dest]
    if len(bpy.context.selected_objects) == 2:
        for v in bpy.context.selected_objects:
            if v is not dest:
                source = v
                break
        
        print("Source: ", source.name)
        print("Destination: ", dest.name)
        
        if source.data.shape_keys is None:
            print("Source object has no shape keys!") 
        else:
            for idx in range(1, len(source.data.shape_keys.key_blocks)):
                source.active_shape_key_index = idx
                print("Copying Shape Key - ", source.active_shape_key.name)
                bpy.ops.object.shape_key_transfer()
        bpy.context.object.show_only_shape_key = False
        print("Disabling show_only_shape_key")
    else:
        print('No selected Objects')



def select_model_armature():
    for obj in bpy.data.collections['MB_LAB_Character'].all_objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        return obj
        
def select_camera_armature():
    obj = bpy.data_objects['CameraRig'].select_set(True)
    bpy.context.view_layer.objects.active = obj  
    
    return obj 

def zero_camera():              # Sets the camera rig to a known rest pose.
    ob = bpy.data.objects['CameraRig'] 
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE') 
    pbone = ob.pose.bones['Camera']
    pbone.rotation_euler = (0, 0, 0)
    pbone = ob.pose.bones['CameraArm'] 
    pbone.rotation_euler = (0, 0, 0)
    pbone = ob.pose.bones['MBLabHead']
    pbone.rotation_euler = (0, 0, 0)
    pbone = ob.pose.bones['Dolly_Phone']
    pbone.location = (0, 0, 0)
    pbone = ob.pose.bones['Dolly_Mouthcam']
    pbone.location = (0, 0, 0)
    bpy.ops.object.mode_set(mode='OBJECT') 
    ob = bpy.data.objects['AimTarget']
    ob.location = (0, -0.150, 1.647)
    
def zero_lights():                  # Sets the rotation of all lights to 0
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = bpy.data.objects['Light1']
    ob.rotation_euler = (0, 0, 0)
    ob = bpy.data.objects['Light2']
    ob.rotation_euler = (0, 0, 0)
    ob = bpy.data.objects['Light3']
    ob.rotation_euler = (0, 0, 0)

def zero_bg():                  # Sets the Z position of all backgrounds to 0
    for i in range(14):
        ob = bpy.data.objects['BG' + str(i + 1)]
        ob.location[1] = 0

    


def set_index(shapekey_name, shapekey_value, setShapes):        # Checks for blendshape name to set the randomized value in a list
    
    if str(shapekey_name) == cheekPuff:
        setShapes[0] = shapekey_value
    if str(shapekey_name) == cheekSquintLeft:
        setShapes[1] = shapekey_value
    if str(shapekey_name) == cheekSquintRight:
        setShapes[2] = shapekey_value
    if str(shapekey_name) == noseSneerLeft:
        setShapes[3] = shapekey_value
    if str(shapekey_name) == noseSneerRight:
        setShapes[4] = shapekey_value
    if str(shapekey_name) == jawOpen:
        setShapes[5] = shapekey_value
    if str(shapekey_name) == jawForward:
        setShapes[6] = shapekey_value
    if str(shapekey_name) == jawLeft:
        setShapes[7] = shapekey_value
    if str(shapekey_name) == jawRight:
        setShapes[8] = shapekey_value
    if str(shapekey_name) == mouthFunnel:    
        setShapes[9] = shapekey_value  
    if str(shapekey_name) == mouthPucker:
        setShapes[10] = shapekey_value  
    if str(shapekey_name) == mouthLeft:
        setShapes[11] = shapekey_value
    if str(shapekey_name) == mouthRight:
        setShapes[12] = shapekey_value
    if str(shapekey_name) == mouthRollUpper:   
        setShapes[13] = shapekey_value
    if str(shapekey_name) == mouthRollLower:  
        setShapes[14] = shapekey_value
    if str(shapekey_name) == mouthShrugUpper:
        setShapes[15] = shapekey_value
    if str(shapekey_name) == mouthShrugLower:
        setShapes[16] = shapekey_value
    if str(shapekey_name) == mouthClose:
        setShapes[17] = shapekey_value
    if str(shapekey_name) == mouthSmileLeft:
        setShapes[18] = shapekey_value
    if str(shapekey_name) == mouthSmileRight:
        setShapes[19] = shapekey_value
    if str(shapekey_name) == mouthFrownLeft:
        setShapes[20] = shapekey_value
    if str(shapekey_name) == mouthFrownRight:
        setShapes[21] = shapekey_value
    if str(shapekey_name) == mouthDimpleLeft:
        setShapes[22] = shapekey_value
    if str(shapekey_name) == mouthDimpleRight:
        setShapes[23] = shapekey_value
    if str(shapekey_name) == mouthUpperUpLeft:
        setShapes[24] = shapekey_value
    if str(shapekey_name) == mouthUpperUpRight:
        setShapes[25] = shapekey_value
    if str(shapekey_name) == mouthLowerDownLeft:
        setShapes[26] = shapekey_value
    if str(shapekey_name) == mouthLowerDownRight:
        setShapes[27] = shapekey_value
    if str(shapekey_name) == mouthPressLeft:
        setShapes[28] = shapekey_value
    if str(shapekey_name) == mouthPressRight:
        setShapes[29] = shapekey_value
    if str(shapekey_name) == mouthStretchLeft:
        setShapes[30] = shapekey_value
    if str(shapekey_name) == mouthStretchRight:
        setShapes[31] = shapekey_value
    if str(shapekey_name) == tongueOut:
        setShapes[32] = shapekey_value

          
def rand_shape(shapekey_name, chance1, chance2, shape, setShapes, range1 = 0, range2 = 1):  # Randomize specified blendshape
    if random.randint(chance1, chance2) == 0:        
        if (shape.name == shapekey_name):
            shape.slider_min = -1
            shape.value=round(random.uniform(range1, range2), 3)
            if range1 < 0:
                #print(str(shape.value))
                set_index(shapekey_name, (-1 * round(shape.value, 3)), setShapes)
            else: 
                set_index(shapekey_name, round(shape.value, 3), setShapes)


def set_shape(shape, shapekey_name, value, setShapes):
    if shape.name == shapekey_name:
        shape.value = value
        set_index(shapekey_name, value, setShapes)

def set_morph(shape, shapekey_name, value):
    if shape.name == shapekey_name:
        shape.value = value
          
            
    
def zero_blendshapes(dest):                 # Set all blendshape values to 0
    ob = bpy.data.objects[dest]
    for shape in ob.data.shape_keys.key_blocks:
        shape.value=0
         
             
  
def combo1(ob, setShapes):
    shapes = [0,0,0,0,0,0,0]
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    case_value = random.randint(0,3)
    if shapes[class_example] > 0.1:
        for i in range(len(shapes)):
            if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
            else: reroll_shapes[i] = shapes[class_example]
        for shape in ob.data.shape_keys.key_blocks:
            if case_value == 0 or class_example == 0:
                if shape == mouthFunnel: shape.value = reroll_shapes[0]
                set_shape(shape, mouthFunnel, reroll_shapes[0], setShapes)
            if case_value > 0 and not class_example == 0:
                if shape == mouthRollUpper: shape.value = reroll_shapes[1]
                if shape == mouthRollLower: shape.value = reroll_shapes[2]
                if shape == mouthUpperUpLeft: shape.value = reroll_shapes[3]
                if shape == mouthUpperUpRight: shape.value = reroll_shapes[4]
                if shape == mouthLowerDownLeft: shape.value = reroll_shapes[5]
                if shape == mouthLowerDownRight: shape.value = reroll_shapes[6]
                set_shape(shape, mouthRollUpper, reroll_shapes[1], setShapes)
                set_shape(shape, mouthRollLower, reroll_shapes[2], setShapes)
                set_shape(shape, mouthUpperUpLeft, reroll_shapes[3], setShapes)
                set_shape(shape, mouthUpperUpRight, reroll_shapes[4], setShapes)
                set_shape(shape, mouthLowerDownLeft, reroll_shapes[5], setShapes)
                set_shape(shape, mouthLowerDownRight, reroll_shapes[6], setShapes)
    if shapes[class_example] <= 0.1:
        for shape in ob.data.shape_keys.key_blocks:
            if shape == mouthFunnel: shape.value = shapes[0]
            if shape == mouthRollUpper: shape.value = shapes[1]
            if shape == mouthRollLower: shape.value = shapes[2]
            if shape == mouthUpperUpLeft: shape.value = shapes[3]
            if shape == mouthUpperUpRight: shape.value = shapes[4]
            if shape == mouthLowerDownLeft: shape.value = shapes[5]
            if shape == mouthLowerDownRight: shape.value = shapes[6]
            set_shape(shape, mouthFunnel, reroll_shapes[0], setShapes)
            set_shape(shape, mouthRollUpper, reroll_shapes[1], setShapes)
            set_shape(shape, mouthRollLower, reroll_shapes[2], setShapes)
            set_shape(shape, mouthUpperUpLeft, reroll_shapes[3], setShapes)
            set_shape(shape, mouthUpperUpRight, reroll_shapes[4], setShapes)
            set_shape(shape, mouthLowerDownLeft, reroll_shapes[5], setShapes)
            set_shape(shape, mouthLowerDownRight, reroll_shapes[6], setShapes)
            
            
def combo2(ob, setShapes):
    shapes = [0,0,0,0,0,0,0,0,0,0]
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    case_value = random.randint(0, 1)
    SmileFrown = random.randint(0, 1)
    if shapes[class_example] > 0.1:
        for i in range(len(shapes)):
            if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
            else: reroll_shapes[i] = shapes[class_example]
        for shape in ob.data.shape_keys.key_blocks:
            if 1 == random.randint(0,3):
                if shape == jawForward: 
                    shape.value = reroll_shapes[0]; set_shape(shape, jawForward, reroll_shapes[0], setShapes)
            if case_value == 0 or class_example == 1 and not class_example == 2:
                if 1 == random.randint(0,3) or class_example == 1:
                    if shape == jawLeft: shape.value = reroll_shapes[1]; 
                    set_shape(shape, jawLeft, reroll_shapes[1], setShapes)
            if case_value == 1 or class_example == 2 and not class_example == 1:
                if 1 == random.randint(0,3) or class_example == 2:
                    if shape == jawRight: shape.value = reroll_shapes[2]; 
                    set_shape(shape, jawRight, reroll_shapes[2], setShapes)
            
            
            
            if 1 == random.randint(0,3):
                if shape == mouthLeft: shape.value = reroll_shapes[4]; 
                set_shape(shape, mouthLeft, reroll_shapes[4], setShapes)
            if 1 == random.randint(0,3):
                if shape == mouthRight: shape.value = reroll_shapes[5]; 
                set_shape(shape, mouthRight, reroll_shapes[5], setShapes)
                
            if 6 <= class_example <= 7 or SmileFrown == 0 and not 8 <= class_example <= 9:
                if 1 == random.randint(0,3) or 6<= class_example <= 7:                     # Smile or frown
                    if shape == mouthSmileLeft: shape.value = reroll_shapes[6]; 
                    set_shape(shape, mouthSmileLeft, reroll_shapes[6], setShapes)
                if 1 == random.randint(0,3) or 6<= class_example <= 7:
                    if shape == mouthSmileRight: shape.value = reroll_shapes[7]; 
                    set_shape(shape, mouthSmileRight, reroll_shapes[7], setShapes)
            if 8 <= class_example <= 9 or SmileFrown == 1 and not 6 <= class_example <= 7:
                if 1 == random.randint(0,3) or 8 <= class_example <= 9:
                    if shape == mouthFrownLeft: shape.value = reroll_shapes[8]; 
                    set_shape(shape, mouthFrownLeft, reroll_shapes[8], setShapes)
                if 1 == random.randint(0,3) or 8 <= class_example <= 9:
                    if shape == mouthFrownRight: shape.value = reroll_shapes[9]; 
                    set_shape(shape, mouthFrownRight, reroll_shapes[9], setShapes)
                    
def combo3(ob, setShapes):
    shapes = [0,0,0]
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    #print(reroll_shapes)
    if shapes[class_example] > 0.1:
        for i in range(len(shapes)):
            if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
            else: reroll_shapes[i] = shapes[class_example]
        for shape in ob.data.shape_keys.key_blocks:
            if shape == mouthShrugUpper or shape == mouthShrugLower: 
                shape.value = reroll_shapes[0] 
            set_shape(shape, mouthShrugUpper, reroll_shapes[0], setShapes)
            set_shape(shape, mouthShrugLower, reroll_shapes[0], setShapes)
            if shape == mouthPressLeft:
                shape.value = reroll_shapes[1] 
            set_shape(shape, mouthPressLeft, reroll_shapes[1], setShapes)
            if shape == mouthPressRight:
                shape.value = reroll_shapes[2] 
            set_shape(shape, mouthPressRight, reroll_shapes[2], setShapes)
                
        

def combo4(ob, setShapes):
    shapes = [0,0,0,0,0,0,0,0,0]
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    #print(reroll_shapes)
    for shape in ob.data.shape_keys.key_blocks:
        for i in range(len(shapes)):
            if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
            else: reroll_shapes[i] = shapes[class_example]
            
        if shape == noseSneerLeft:
            shape.value = reroll_shapes[0] 
        set_shape(shape, noseSneerLeft, reroll_shapes[0], setShapes)
        if shape == noseSneerRight:
            shape.value = reroll_shapes[1] 
        set_shape(shape, noseSneerRight, reroll_shapes[1], setShapes)
        if shape == jawOpen:
            shape.value = reroll_shapes[2] 
        set_shape(shape, jawOpen, reroll_shapes[2], setShapes)
        if shape == mouthStretchLeft:
            shape.value = reroll_shapes[3] 
        set_shape(shape, mouthStretchLeft, reroll_shapes[3], setShapes)
        if shape == mouthStretchRight:
            shape.value = reroll_shapes[4] 
        set_shape(shape, mouthStretchRight, reroll_shapes[4], setShapes)
        if shape == mouthUpperUpLeft:
            shape.value = reroll_shapes[5] 
        set_shape(shape, mouthUpperUpLeft, reroll_shapes[5], setShapes)
        if shape == mouthUpperUpRight:
            shape.value = reroll_shapes[6] 
        set_shape(shape, mouthUpperUpRight, reroll_shapes[6], setShapes)
        if shape == mouthLowerDownLeft:
            shape.value = reroll_shapes[7] 
        set_shape(shape, mouthLowerDownLeft, reroll_shapes[7], setShapes)     
        if shape == mouthLowerDownRight:
            shape.value = reroll_shapes[8] 
        set_shape(shape, mouthLowerDownRight, reroll_shapes[8], setShapes)  

def combo5(ob, setShapes):
    shapes = [0,0,0,0]
    shapes_enable = [0,0,0,0]
    
    for i in range (len(shapes_enable)):
        shapes_enable[i] = random.uniform(0,1)
    
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    #print(reroll_shapes)
    for shape in ob.data.shape_keys.key_blocks:
        for i in range(len(shapes)):
            if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
            else: reroll_shapes[i] = shapes[class_example]
            
            if shapes_enable[0] == 1 or shapes_enable[0] == reroll_shapes[class_example]:
                if shape == mouthDimpleLeft:
                    shape.value = reroll_shapes[0]
                set_shape(shape, mouthDimpleLeft, reroll_shapes[0], setShapes)
            if shapes_enable[1] == 1 or shapes_enable[1] == reroll_shapes[class_example]:    
                if shape == mouthDimpleRight:
                    shape.value = reroll_shapes[1]
                set_shape(shape, mouthDimpleRight, reroll_shapes[1], setShapes)
            if shapes_enable[2] == 1 or shapes_enable[2] == reroll_shapes[class_example]:
                if shape == mouthRollUpper:
                    shape.value = reroll_shapes[2]
                set_shape(shape, mouthRollUpper, reroll_shapes[2], setShapes)
            if shapes_enable[3] == 1 or shapes_enable[3] == reroll_shapes[class_example]:
                if shape == mouthRollLower:
                    shape.value = reroll_shapes[3]
                set_shape(shape, mouthRollLower, reroll_shapes[3], setShapes)
                
def combo6(ob, setShapes):
    shapes = [0,0,0]
    shapes_enable = [0,0,0]
    LR = random.randint(0,1)
    for i in range (len(shapes_enable)):
        shapes_enable[i] = random.randint(0,1)
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    #print(reroll_shapes)
    for i in range(len(shapes)):
        if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
        else: reroll_shapes[i] = shapes[class_example]
    for shape in ob.data.shape_keys.key_blocks:
            
        if class_example == 0 or (shapes_enable[0] == 1):    
            if shape == jawOpen or shape == mouthClose:
                shape.value = reroll_shapes[0]
            set_shape(shape, jawOpen, reroll_shapes[0], setShapes)
            set_shape(shape, mouthClose, reroll_shapes[0], setShapes) 
        
        if (class_example == 1 and not class_example == 2) or (shapes_enable[1] == 1 and LR == 0):
            if shape == jawLeft:
                shape.value = reroll_shapes[1] 
            set_shape(shape, jawLeft, reroll_shapes[1], setShapes)
        if (class_example == 2 and not class_example == 1) or (shapes_enable[2] == 1 and LR == 1):
            if shape == jawRight:
                shape.value = reroll_shapes[2] 
            set_shape(shape, jawRight, reroll_shapes[2], setShapes)
            
def combo7(ob, setShapes):
    shapes = [0,0,0,0,0,0,0,0,0]
    shapes_enable = [0,0,0,0,0,0,0,0,0,0]
    LR = random.randint(0,1)
    for i in range (len(shapes_enable)):
        shapes_enable[i] = random.randint(0,1)
    for i in range(len(shapes)):
        shapes[i] = random.uniform(0, 1)
    shapes.append(random.uniform(0,0.3)) # Limited Jaw Movement
    class_example = int(shapes.index(max(shapes)))
    reroll_shapes = copy.copy(shapes)
    #print(shapes[class_example])
    #print(reroll_shapes)
    for shape in ob.data.shape_keys.key_blocks:
        for i in range(len(shapes)):
            if not i == class_example: reroll_shapes[i] = random.uniform(0, (shapes[class_example] - 0.1))
            else: reroll_shapes[i] = shapes[class_example]
            
        if class_example == 0 or (shapes_enable[0] == 1):
            if shape == mouthPucker:
                shape.value = reroll_shapes[0] 
            set_shape(shape, mouthPucker, reroll_shapes[0], setShapes)
            
        if class_example == 1 or (shapes_enable[1] == 1):    
            if shape == mouthUpperUpLeft:
                shape.value = reroll_shapes[1] 
            set_shape(shape, mouthUpperUpLeft, reroll_shapes[1], setShapes)
            
        if class_example == 2 or (shapes_enable[2] == 1):  
            if shape == mouthUpperUpRight:
                shape.value = reroll_shapes[2] 
            set_shape(shape, mouthUpperUpRight, reroll_shapes[2], setShapes)
        
        if class_example == 3 or (shapes_enable[3] == 1):  
            if shape == mouthLowerDownLeft:
                shape.value = reroll_shapes[3] 
            set_shape(shape, mouthLowerDownLeft, reroll_shapes[3], setShapes)
        
        if class_example == 4 or (shapes_enable[4] == 1):  
            if shape == mouthLowerDownRight:
                shape.value = reroll_shapes[4] 
            set_shape(shape, mouthLowerDownRight, reroll_shapes[4], setShapes)
            
        if class_example == 5 or (shapes_enable[5] == 1):  
            if shape == mouthStretchLeft:
                shape.value = reroll_shapes[5] 
            set_shape(shape, mouthLowerDownRight, reroll_shapes[5], setShapes)
            
        if class_example == 6 or (shapes_enable[6] == 1):  
            if shape == mouthStretchRight:
                shape.value = reroll_shapes[6] 
            set_shape(shape, mouthLowerDownRight, reroll_shapes[6], setShapes)
        
        if (class_example == 7 and not class_example == 8) or (shapes_enable[7] == 1 and LR == 0):
            if shape == jawLeft:
                shape.value = reroll_shapes[7] 
            set_shape(shape, jawLeft, reroll_shapes[7], setShapes)
            
        if (class_example == 8 and not class_example == 7) or (shapes_enable[8] == 1 and LR == 1):
            if shape == jawRight:
                shape.value = reroll_shapes[8] 
            set_shape(shape, jawRight, reroll_shapes[8], setShapes)
            
        if class_example == 9 or (shapes_enable[9] == 1):  
            if shape == jawOpen:
                shape.value = reroll_shapes[9] 
            set_shape(shape, jawOpen, reroll_shapes[9], setShapes)

def combo8(ob, setShapes):                  # Old shapes not enforcing class examples
    for shape in ob.data.shape_keys.key_blocks:      
        rand_shape(mouthFunnel, 0, 1, shape, setShapes)
        rand_shape(mouthRollUpper, 0, 1, shape, setShapes)
        rand_shape(mouthRollLower, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUpLeft, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUpRight, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDownLeft, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDownRight, 0, 1, shape, setShapes)
    
def combo9(ob, setShapes): 
    for shape in ob.data.shape_keys.key_blocks:  
        rand_shape(jawForward, 0, 1, shape, setShapes)
        rand_shape(jawLeft, 0, 1, shape, setShapes)
        rand_shape(jawRight, 0, 1, shape, setShapes)    
        rand_shape(mouthPucker, 0, 2, shape, setShapes)
        rand_shape(mouthLeft, 0, 1, shape, setShapes)
        rand_shape(mouthRight, 0, 1, shape, setShapes)
        if random.randint(0, 1) == 0:
            rand_shape(mouthSmileLeft, 0, 1, shape, setShapes)
            rand_shape(mouthSmileRight, 0, 1, shape, setShapes)
        else:
            rand_shape(mouthFrownLeft, 0, 1, shape, setShapes, -1, 0)
            rand_shape(mouthFrownRight, 0, 1, shape, setShapes, -1, 0)
        rand_shape(mouthDimpleLeft, 0, 1, shape, setShapes)
        rand_shape(mouthDimpleRight, 0, 1, shape, setShapes)
        
        rand_shape(mouthPressLeft, 0, 1, shape, setShapes)
        rand_shape(mouthPressRight, 0, 1, shape, setShapes)
                
        rand_shape(mouthStretchLeft, 0, 1, shape, setShapes)
        rand_shape(mouthStretchRight, 0, 1, shape, setShapes)
    
    
def combo10(ob, setShapes): 
    for shape in ob.data.shape_keys.key_blocks:    
        rand_shape(mouthFunnel, 0, 2, shape, setShapes)
        rand_shape(mouthRollUpper, 0, 1, shape, setShapes)
        rand_shape(mouthRollLower, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUpLeft, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUpRight, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDownLeft, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDownRight, 0, 1, shape, setShapes)
        if random.randint(0, 2) == 0:
            rand_shape(jawOpen, 0, 0, shape, setShapes, 0.6, 1)
            rand_shape(tongueOut, 0, 0, shape, setShapes)
        
def combo11(ob, setShapes): 
    for shape in ob.data.shape_keys.key_blocks:  
        rand_shape(cheekPuff, 0, 1, shape, setShapes)
        rand_shape(noseSneerLeft, 0, 1, shape, setShapes)
        rand_shape(noseSneerRight, 0, 1, shape, setShapes)
    
def combo12(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:  
        rand_shape(mouthFunnel, 0, 2, shape, setShapes)
        rand_shape(mouthSmileLeft, 0, 1, shape, setShapes)
        rand_shape(mouthSmileRight, 0, 1, shape, setShapes)

def combo13(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:  
        if random.randint(0, 1) == 0:
            if random.randint(0, 1) == 0:
                rand_shape(mouthSmileLeft, 0, 1, shape, setShapes)
                rand_shape(mouthSmileRight, 0, 1, shape, setShapes)
            else: 
                rand_shape(mouthPressLeft, 0, 1, shape, setShapes)
                rand_shape(mouthPressRight, 0, 1, shape, setShapes)
        else:
            rand_shape(mouthFrownLeft, 0, 1, shape, setShapes)
            rand_shape(mouthFrownRight, 0, 1, shape, setShapes)
        rand_shape(jawOpen, 0, 1, shape, setShapes)
        
def combo14(ob, setShapes):                 # Additive Cheek Puff
    for shape in ob.data.shape_keys.key_blocks:
        rand_shape(cheekPuff, 0, 1, shape, setShapes, 0.3, 1)

def combo15(ob, setShapes):                 # Additive Smile
    for shape in ob.data.shape_keys.key_blocks:
        rand_shape(mouthSmileLeft, 0, 1, shape, setShapes, 0.5, 1)
        rand_shape(mouthSmileRight, 0, 1, shape, setShapes, 0.5, 1)
        rand_shape(jawOpen, 0, 1, shape, setShapes, 0.2, 1)

def combo16(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:
        rand_shape(mouthRollUpper, 0, 1, shape, setShapes)
        rand_shape(mouthRollLower, 0, 1, shape, setShapes)

def combo17(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:
        rand_shape(jawForward, 0, 1, shape, setShapes, 0.55, 1)

def combo18(ob, setShapes):
    shapes = [0]
    for i in range(len(shapes)):
        shapes[i] = random.uniform(.3, 1)
    for shape in ob.data.shape_keys.key_blocks:
        if shape == jawOpen or shape == mouthClose:
            shape.value = shapes[0]
        set_shape(shape, jawOpen, shapes[0], setShapes)
        set_shape(shape, mouthClose, shapes[0], setShapes) 

def combo19(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:
        rand_shape(mouthDimpleLeft, 0, 1, shape, setShapes, 0.3, 1)
        rand_shape(mouthDimpleRight, 0, 1, shape, setShapes, 0.3, 1)
        
def combo20(ob, setShapes):
    shapes = [0,0]
    LR = random.randint(0,1)
    for i in range(len(shapes)):
        shapes[i] = random.uniform(.3, 1)
    
    for shape in ob.data.shape_keys.key_blocks:
        if LR == 0:
            if shape == mouthLeft:
                shape.value = shapes[0]
            set_shape(shape, mouthLeft, shapes[0], setShapes)
        if LR == 1:
            if shape == mouthRight:
                shape.value = shapes[1]
            set_shape(shape, mouthRight, shapes[1], setShapes) 

def combo21(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:
        rand_shape(mouthPucker, 0, 0, shape, setShapes, 0.4, 1)

def facemorph1(ob):

    for shape in ob.data.shape_keys.key_blocks:
        set_morph(shape, "WideJaw1", random.uniform(0, .5))
        set_morph(shape, "WideCheekBone1", random.uniform(0, .5))
        set_morph(shape, "RoundJaw1", random.uniform(0, .5))
        set_morph(shape, "ChinBack", random.uniform(0, .5))
        set_morph(shape, "CheekChub", random.uniform(1, 1))
        #set_morph(shape, "FaceTall", random.uniform(0, .2))          

s=bpy.context.scene
s.render.resolution_x = 256
s.render.resolution_y = 256
def main(dest, selector):
    
        setShapes = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,'filename']
        
        camera_list = ('ViveCamera', 'PhoneCamera', 'OVH2640-160')
        camera_select = camera_list[random.randint(0,2)]
        bpy.data.scenes['Scene'].camera = s.objects[camera_select]
        print(f"Switching camera to {camera_select}")
                                        # Randomize camera FOVs
        '''
        ob = bpy.data.objects['OVH2640-160']
        ob.data.lens = random.uniform(14, 18) #Reference 16 (Represents a wide angle espcamera) (95deg)

        ob = bpy.data.objects['ViveCamera']
        ob.data.lens = random.uniform(21, 23.5) #Reference 22.5  (Represents Vivefacial tracker) (77.3deg)

        ob = bpy.data.objects['PhoneCamera']
        ob.data.lens = random.uniform(72, 77) #Reference 74.4 (Represents cropped webcamera)  (27.2)
        '''
                            
            # Applies random rotation to the camera rig
        
        ob = bpy.data.scenes["Scene"].node_tree.nodes["Lens Distortion"].inputs[1]           # Compositer Lens Distortion
        ob.default_value = random.uniform(0.01, 0.27)                
        # Camera 
        ob = bpy.data.objects['CameraRig']  # The thing we're talking about
        bpy.context.view_layer.objects.active = ob   # Click it (make it the active selection)
        bpy.ops.object.mode_set(mode='POSE')    # Go into pose mode
        pbone = ob.pose.bones['Camera']   # Select the bone to rotate
        pbone.rotation_mode = 'XYZ'     # Set rotations to euler because quaternions are an alien technology
        axis = 'Z'  # Select rotaion axis (local)
        angle = random.uniform(-3, 4)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))             # Do the rotation
        
        # Camera Arm
        bpy.ops.object.mode_set(mode='POSE')   
        pbone = ob.pose.bones['CameraArm']   
        pbone.rotation_mode = 'XYZ'   
        axis = 'Z' 
        angle = random.uniform(-2, 2)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))
        
        # Camera Dolly
        bpy.ops.object.mode_set(mode='POSE') 
        pbone = ob.pose.bones['Dolly_Phone']
        multi = (4)
        pbone.location = (multi * random.uniform(-0.01, 0.01), multi * random.uniform(0, 0.005), multi * random.uniform(-0.01, 0.01))


        bpy.ops.object.mode_set(mode='POSE') 
        pbone = ob.pose.bones['Dolly_Mouthcam']
        multi = (2)
        pbone.location = (multi * random.uniform(-0.01, 0.01), multi * random.uniform(0, 0.005), multi * random.uniform(-0.01, 0.01))

        # MLabHead    
        bpy.ops.object.mode_set(mode='POSE')   
        pbone = ob.pose.bones['MBLabHead'] 
        pbone.rotation_mode = 'XYZ'    
        axis = 'Y' 
        angle = random.uniform(-2, 2)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))
        
        bpy.ops.object.mode_set(mode='POSE')    
        pbone = ob.pose.bones['MBLabHead']  
        pbone.rotation_mode = 'XYZ'   
        axis = 'Z' 
        angle = random.uniform(-2, 2)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))

        bpy.ops.object.mode_set(mode='OBJECT') 
        
                                                             # Applies random rotation to the scene hdri                      
        bpy.data.worlds["World"].node_tree.nodes["Mapping"].inputs[2].default_value[0] = random.uniform(0,360)  
        bpy.data.worlds["World"].node_tree.nodes["Mapping"].inputs[2].default_value[1] = random.uniform(0,360)  
        bpy.data.worlds["World"].node_tree.nodes["Mapping"].inputs[2].default_value[2] = random.uniform(0,360)                                                           
        

        
                                                            # Switches between vive light and scene lights
        light_type = random.randint(0,1)
        if light_type == 0:         # 0 = ViveLight, 1 = SceneLights
            ob = bpy.data.objects['ViveLight']
            ob.data.energy = random.uniform(0.05, 0.25) # Ref 0.15
            bpy.data.worlds["World"].node_tree.nodes["ColorRamp"].color_ramp.elements[1].color = (0, 0, 0, 1) #HDRI for bighting in Cycles, background in Eevee

        if light_type == 1:
            ob = bpy.data.objects['ViveLight']
            ob.data.energy = 0 
            bpy.data.worlds["World"].node_tree.nodes["ColorRamp"].color_ramp.elements[1].color = (1, 1, 1, 1)

        if bpy.context.scene.render.engine == 'BLENDER_EEVEE':  # Check if renderer is set to Eevee

                                                # Randomize Light Strength
            
            ob = bpy.data.objects['Area1']
            ob.data.energy = random.uniform(10, 45)

            ob = bpy.data.objects['Area2']
            ob.data.energy = random.uniform(10, 45)

            ob = bpy.data.objects['Area3']
            ob.data.energy = random.uniform(10, 45)

            ob = bpy.data.objects['Light1']
            ob.rotation_mode = 'XYZ'    
            axis = 'Z'  
            angle = random.uniform(0, 360)
            ob.rotation_euler.rotate_axis(axis, math.radians(angle))
            axis = 'Y' 
            angle = random.uniform(-40, 40)
            ob.rotation_euler.rotate_axis(axis, math.radians(angle))
            
            ob = bpy.data.objects['Light2']
            ob.rotation_mode = 'XYZ'    
            axis = 'Z'  
            angle = random.uniform(0, 360)
            ob.rotation_euler.rotate_axis(axis, math.radians(angle))
            axis = 'Y'  
            angle = random.uniform(-40, 40)
            ob.rotation_euler.rotate_axis(axis, math.radians(angle))
            
            ob = bpy.data.objects['Light3']
            ob.rotation_mode = 'XYZ'                
            axis = 'Z'  
            angle = random.uniform(0, 360)
            ob.rotation_euler.rotate_axis(axis, math.radians(angle))
            axis = 'Y' 
            angle = random.uniform(-40, 40)
            ob.rotation_euler.rotate_axis(axis, math.radians(angle))
        else: 
            ob = bpy.data.objects["Area1"]         # Turn off lights for Cycles HDRI
            ob.data.energy = 0

            ob = bpy.data.objects["Area2"]
            ob.data.energy = 0

            ob = bpy.data.objects["Area3"]
            ob.data.energy = 0
        '''
        ob = bpy.data.objects['AimTarget']          # Moves AimTarget
        ob.location = (0 + (0.5 * random.uniform(-0.0075, 0.0075)), -0.150, 1.647 + (0.2 * random.uniform(-0.03, 0.03)))
        '''                                                    # Enables and disables HMD
        hmd_type = random.randint(0,2)
        
        ob = bpy.data.objects['Pimax']
        ob.hide_render = True
        ob = bpy.data.objects['Quest2']
        ob.hide_render = True

        if hmd_type == 0:
            ob = bpy.data.objects['Pimax']
            ob.hide_render = True
            ob = bpy.data.objects['Quest2']
            ob.hide_render = True
        if hmd_type == 1:
            ob = bpy.data.objects['Pimax']
            ob.hide_render = False
        if hmd_type == 2:
            ob = bpy.data.objects['Quest2']
            ob.hide_render = False
        
              #   Background Randomization
        '''
        ob = bpy.data.objects['BG' + str(random.randint(1, 14))]
        ob.location[1] = -0.1
        '''
        ########    Blendshape Randomization    ########
        try:
            ob = bpy.data.objects[dest]
        except: 
            print("Combo ob already set")
        print(f"Dest: {dest}")
        
        # Morph Face

        facemorph1(ob)
        
        
        #selector = random.randint(20, 20)
        print(f"Combination: {selector}")       # Loop through each combo instead of randomly selecting to make the dataset a little more even. 
        if selector == 1:
            combo1(ob, setShapes)
        if selector == 2:
            combo2(ob, setShapes)
        if selector == 3:
            combo3(ob, setShapes)  
        if selector == 4:
            combo4(ob, setShapes)
        if selector == 5:
            combo5(ob, setShapes)
        if selector == 6:
            combo6(ob, setShapes)
        if selector == 7:
            combo7(ob, setShapes)
        if selector == 8:
            combo8(ob, setShapes)
        if selector == 9:
            combo9(ob, setShapes)
        if selector == 10:
            combo10(ob, setShapes)
        if selector == 11:
            combo11(ob, setShapes)
        if selector == 12:
            combo12(ob, setShapes)
        if selector == 13:
            combo13(ob, setShapes)
        if selector == 14:
            combo14(ob, setShapes)
        if selector == 15:
            combo15(ob, setShapes)
        if selector == 16:
            combo16(ob, setShapes)
        if selector == 17:
            combo17(ob, setShapes)
        if selector == 18:
            combo18(ob, setShapes)
        if selector == 19:
            combo19(ob, setShapes)
        if selector == 20:
            combo20(ob, setShapes)
        if selector == 21:
            combo21(ob, setShapes)


        if selector == 21:
            selector = 0
        selector = selector + 1
            
        return setShapes, selector
            
            
        

#bpy.app.handlers.frame_change_post.append(main) # for frame change
bpy.ops.wm.console_toggle()

print("Start Transfer")
dest = get_objs('MB_LAB_Character')
source = None
if dest == 'MBLab_CA_M':
    source = 'MBLabBase_CA_M'
if dest == 'MBLab_CA_F':
    source = 'MBLabBase_CA_F'
if dest == 'MBLab_AF_M':
    source = 'MBLabBase_AF_M'
if dest == 'MBLab_AF_F':
    source = 'MBLabBase_AF_F'
if dest == 'MBLab_AS_M':
    source = 'MBLabBase_AS_M'
if dest == 'MBLab_AS_F':
    source = 'MBLabBase_AS_F'
if dest == 'MBLab_LA_M':
    source = 'MBLabBase_LA_M'
if dest == 'MBLab_LA_F':
    source = 'MBLabBase_LA_F'
    
#copy_all_shape_keys(source, dest)
print("End Transfer") 
selector = 1
for i in range(s.frame_start,s.frame_end):              # Rendering stuff
    zero_camera() 
    zero_lights()
    zero_blendshapes(dest)
    mili_time = str(round(time.time() * 1000)) + str(random.randint(0,99999999))
    csvfilename = mili_time + '.csv'
    pngfilename = mili_time + '.png'
    data, selector = main(dest, selector)
    if not os.path.exists(bpy.path.abspath("//" + 'lipimages')):
        os.makedirs(bpy.path.abspath("//" + 'lipimages'))
    joined_string = ','.join(map(str, data)) 
    csvfilepath = bpy.path.abspath("//" + 'lipimages' + "/" + csvfilename)
    pngfilepath = bpy.path.abspath("//" + 'lipimages' + "/" + pngfilename)
    csvimagepath = ('lipimages' + '/' + pngfilename)
    data[33] = csvimagepath
    joined_string = ','.join(map(str, data)) 
    with open(csvfilepath, 'w') as file:
        file.write(joined_string)
        file.close()
    print(data)
    #time.sleep(.300)

    s.render.filepath = (
                        pngfilepath
                        )
    bpy.ops.render.render( #{'dict': "override"},
                          #'INVOKE_DEFAULT',  
                          False,            
                          animation=False, 
                          write_still=True
                         )


    # Do whatever you want that can't be done normally here (Changing resolution during animation, etc...)
    


    
    

