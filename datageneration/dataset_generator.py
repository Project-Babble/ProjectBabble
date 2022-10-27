'''
Dataset Generation Script made with the tears of Rames The Generic#3540
Randomizes the lighting setup, camera position, background, and blendshapes (predefined combinations).
Each image also gets a corrisponding csv file with the generated blendshapes.
Use the combiner script to combine all the csv files into one.  


Possible mesh naming schemees for automatic blendshape generation (WIP): 
    MBLabBase_(Race)_(Sex)
    
Race: 
    Afro: AF
    Asian: AS
    Caucasian: CA
    Latino: LA
    
Sex:
    Female: F
    Male: M
    
Ex: MBLabBase_AS_M
    



How to use: 
    
1. Create a character with the MBLab plugin, randomize the facial features and finalize
2. Rename the root of the character to MBLab_SK and the body mesh to MBLab_Mesh
3. Add a Copy Location modifier to the CameraRig and set the Target to MBLab_SK and 
   the newly created bone slot to head
4. Add missing blendshapes: (Refer to video: YT Link here and these reference: https://arkit-face-blendshapes.com/)
    mouthShrugUpper
    mouthShrugLower
    mouthDimple_L
    mouthDimple_R
    mouthUpperUp_L
    mouthUpperUp_R
    mouthLowerDown_L
    mouthLowerDown_R
    mouthPress_L
    mouthPress_R
    mouthStretch_L
    mouthStretch_R

'''




import bpy
import math
import random
import csv
from time import sleep


cheekPuff = 'Expressions_mouthInflated_max'
cheekSquint_L = 'cheekSquint_L'
cheekSquint_R = 'cheekSquint_R'
noseSneer_L = 'Expressions_cheekSneerL_max'
noseSneer_R = 'Expressions_cheekSneerR_max'
jawOpen = 'Expressions_mouthOpenLarge_max'
jawForward = 'Expressions_jawOut_max'
jawLeft = 'Expressions_jawHoriz_max'
jawRight = 'Expressions_jawHoriz_min'
mouthFunnel = 'Expressions_mouthOpenO_max'
mouthPucker = 'Expressions_mouthOpenLarge_min'
mouthLeft = 'Expressions_mouthHoriz_max'
mouthRight = 'Expressions_mouthHoriz_min'
mouthRollUpper = 'Expressions_mouthLowerOut_min'
mouthRollLower = 'Expressions_mouthLowerOut_max'
mouthShrugUpper = 'mouthShrugUpper' 
mouthShrugLower = 'mouthShrugLower' 
mouthClose = 'Expressions_mouthSmileOpen2_min'
mouthSmile_L = 'Expressions_mouthSmileL_max'
mouthSmile_R = 'Expressions_mouthSmileR_max'
mouthFrown_L = 'Expressions_mouthSmile_min' 
mouthFrown_R = 'Expressions_mouthSmile_min' 
mouthDimple_L = 'mouthDimple_L'
mouthDimple_R = 'mouthDimple_R' 
mouthUpperUp_L = 'mouthUpperUp_L' 				
mouthUpperUp_R = 'mouthUpperUp_R' 
mouthLowerDown_L = 'mouthLowerDown_L' 		
mouthLowerDown_R = 'mouthLowerDown_R' 
mouthPress_L = 'mouthPress_L' 
mouthPress_R = 'mouthPress_R' 
mouthStretch_L = 'mouthStretch_L' 
mouthStretch_R = 'mouthStretch_R' 
tongueOut = 'Expressions_tongueOut_max'

lables_name = ['cheekPuff','cheekSquint_L','cheekSquint_R','noseSneer_L','noseSneer_R','jawOpen',
'jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight',
'mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose',
'mouthSmile_L','mouthSmile_R','mouthFrown_L','mouthFrown_R','mouthDimple_L','mouthDimple_R',
'mouthUpperUp_L','mouthUpperUp_R','mouthLowerDown_L','mouthLowerDown_R','mouthPress_L',
'mouthPress_R','mouthStretch_L','mouthStretch_R','tongueOut','filename']


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
    bpy.ops.object.mode_set(mode='OBJECT') 
    
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
    if str(shapekey_name) == cheekSquint_L:
        setShapes[1] = shapekey_value
    if str(shapekey_name) == cheekSquint_R:
        setShapes[2] = shapekey_value
    if str(shapekey_name) == noseSneer_L:
        setShapes[3] = shapekey_value
    if str(shapekey_name) == noseSneer_R:
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
    if str(shapekey_name) == mouthSmile_L:
        setShapes[18] = shapekey_value
    if str(shapekey_name) == mouthSmile_R:
        setShapes[19] = shapekey_value
    if str(shapekey_name) == mouthFrown_L:
        setShapes[20] = shapekey_value
    if str(shapekey_name) == mouthFrown_R:
        setShapes[21] = shapekey_value
    if str(shapekey_name) == mouthDimple_L:
        setShapes[22] = shapekey_value
    if str(shapekey_name) == mouthDimple_R:
        setShapes[23] = shapekey_value
    if str(shapekey_name) == mouthUpperUp_L:
        setShapes[24] = shapekey_value
    if str(shapekey_name) == mouthUpperUp_R:
        setShapes[25] = shapekey_value
    if str(shapekey_name) == mouthLowerDown_L:
        setShapes[26] = shapekey_value
    if str(shapekey_name) == mouthLowerDown_R:
        setShapes[27] = shapekey_value
    if str(shapekey_name) == mouthPress_L:
        setShapes[28] = shapekey_value
    if str(shapekey_name) == mouthPress_R:
        setShapes[29] = shapekey_value
    if str(shapekey_name) == mouthStretch_L:
        setShapes[30] = shapekey_value
    if str(shapekey_name) == mouthStretch_R:
        setShapes[31] = shapekey_value
    if str(shapekey_name) == tongueOut:
        setShapes[32] = shapekey_value
            
def rand_shape(shapekey_name, chance1, chance2, shape, setShapes, range1 = 0, range2 = 1):  # Randomize specified blendshape
    if random.randint(chance1, chance2) == 0:        
        if (shape.name == shapekey_name):
            shape.slider_min = -1
            shape.value=round(random.uniform(range1, range2), 3)
            if range1 < 0:
                print(str(shape.value))
                set_index(shapekey_name, (-1 * round(shape.value, 3)), setShapes)
            else: 
                set_index(shapekey_name, round(shape.value, 3), setShapes)
            
            
    
def zero_blendshapes(dest):                 # Set all blendshape values to 0
    ob = bpy.data.objects[dest]
    for shape in ob.data.shape_keys.key_blocks:
        shape.value=0
         
             
            
def combo1(ob, setShapes):                  # Different manually selected combinations of blenshapes that won't create unnatural results
    for shape in ob.data.shape_keys.key_blocks:      
        rand_shape(mouthFunnel, 0, 1, shape, setShapes)
        rand_shape(mouthRollUpper, 0, 1, shape, setShapes)
        rand_shape(mouthRollLower, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUp_L, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUp_R, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDown_L, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDown_R, 0, 1, shape, setShapes)
        rand_shape(tongueOut, 0, 4, shape, setShapes)
    
def combo2(ob, setShapes): 
    for shape in ob.data.shape_keys.key_blocks:  
        rand_shape(jawForward, 0, 1, shape, setShapes)
        rand_shape(jawLeft, 0, 1, shape, setShapes)
        rand_shape(jawRight, 0, 1, shape, setShapes)    
        rand_shape(mouthPucker, 0, 2, shape, setShapes)
        rand_shape(mouthLeft, 0, 1, shape, setShapes)
        rand_shape(mouthRight, 0, 1, shape, setShapes)
    
        if random.randint(0, 3) == 0:
            rand_shape(mouthShrugUpper, 0, 0, shape, setShapes)
            rand_shape(mouthShrugLower, 0, 0, shape, setShapes)
        else: 
            if random.randint(0, 1) == 0:
                rand_shape(mouthSmile_L, 0, 1, shape, setShapes)
                rand_shape(mouthSmile_R, 0, 1, shape, setShapes)
            else:
                rand_shape(mouthFrown_L, 0, 1, shape, setShapes, -1, 0)
                rand_shape(mouthFrown_R, 0, 1, shape, setShapes, -1, 0)
            rand_shape(mouthClose, 0, 1, shape, setShapes)
        
        rand_shape(mouthDimple_L, 0, 1, shape, setShapes)
        rand_shape(mouthDimple_R, 0, 1, shape, setShapes)
        
        rand_shape(mouthPress_L, 0, 1, shape, setShapes)
        rand_shape(mouthPress_R, 0, 1, shape, setShapes)
                
        rand_shape(mouthStretch_L, 0, 1, shape, setShapes)
        rand_shape(mouthStretch_R, 0, 1, shape, setShapes)
    
    
def combo3(ob, setShapes): 
    for shape in ob.data.shape_keys.key_blocks:    
        rand_shape(mouthFunnel, 0, 2, shape, setShapes)
        rand_shape(mouthRollUpper, 0, 1, shape, setShapes)
        rand_shape(mouthRollLower, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUp_L, 0, 1, shape, setShapes)
        rand_shape(mouthUpperUp_R, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDown_L, 0, 1, shape, setShapes)
        rand_shape(mouthLowerDown_R, 0, 1, shape, setShapes)
        if random.randint(0, 2) == 0:
            rand_shape(jawOpen, 0, 0, shape, setShapes)
            rand_shape(tongueOut, 0, 0, shape, setShapes)
        else:
            rand_shape(mouthClose, 0, 1, shape, setShapes)
        
def combo4(ob, setShapes): 
    for shape in ob.data.shape_keys.key_blocks:  
        rand_shape(cheekPuff, 0, 1, shape, setShapes)
        rand_shape(noseSneer_L, 0, 1, shape, setShapes)
        rand_shape(noseSneer_R, 0, 1, shape, setShapes)
        #rand_shape(noseSneer_L, 0, 2, shape, setShapes)
        #rand_shape(noseSneer_R, 0, 2, shape, setShapes)
    
def combo5(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:  
        rand_shape(mouthFunnel, 0, 2, shape, setShapes)
        rand_shape(mouthSmile_L, 0, 1, shape, setShapes)
        rand_shape(mouthSmile_R, 0, 1, shape, setShapes)

def combo6(ob, setShapes):
    for shape in ob.data.shape_keys.key_blocks:  
        if random.randint(0, 1) == 0:
            if random.randint(0, 1) == 0:
                rand_shape(mouthSmile_L, 0, 1, shape, setShapes)
                rand_shape(mouthSmile_R, 0, 1, shape, setShapes)
            else: 
                rand_shape(mouthPress_L, 0, 1, shape, setShapes)
                rand_shape(mouthPress_R, 0, 1, shape, setShapes)
        else:
            rand_shape(mouthFrown_L, 0, 1, shape, setShapes)
            rand_shape(mouthFrown_R, 0, 1, shape, setShapes)
        rand_shape(jawOpen, 0, 1, shape, setShapes)
        
        
        

s=bpy.context.scene

s.render.resolution_x = 256 
s.render.resolution_y = 256


def main(dest):
    
        setShapes = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,'filename']
        
                            
            # Applies random rotation to the camera rig
            
            
        ob = bpy.data.cameras['Camera']  # Camera Focallength
        ob.lens = round(random.uniform(26, 34), 2)
        
        ob = bpy.data.scenes["Scene"].node_tree.nodes["Lens Distortion"].inputs[1]           # Compositer Lens Distortion
        ob.default_value = random.uniform(0.01, 0.27)                
        # Camera 
        ob = bpy.data.objects['CameraRig']  # The thing we're talking about
        bpy.context.view_layer.objects.active = ob   # Click it (make it the active selection)
        bpy.ops.object.mode_set(mode='POSE')    # Go into pose mode
        pbone = ob.pose.bones['Camera']   # Select the bone to rotate
        pbone.rotation_mode = 'XYZ'     # Set rotations to euler because quaternions are an alien technology
        axis = 'Z'  # Select rotaion axis (local)
        angle = random.uniform(-5, 7)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))             # Do the rotation
        
        # Camera Arm
        bpy.ops.object.mode_set(mode='POSE')   
        pbone = ob.pose.bones['CameraArm']  
        pbone.rotation_mode = 'XYZ'   
        axis = 'Z' 
        angle = random.uniform(-4, 4)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))
        
        # MLabHead    
        bpy.ops.object.mode_set(mode='POSE')   
        pbone = ob.pose.bones['MBLabHead'] 
        pbone.rotation_mode = 'XYZ'    
        axis = 'Y' 
        angle = random.uniform(-4, 4)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))
        
        bpy.ops.object.mode_set(mode='POSE')    
        pbone = ob.pose.bones['MBLabHead']  
        pbone.rotation_mode = 'XYZ'   
        axis = 'Z' 
        angle = random.uniform(-4, 4)
        pbone.rotation_euler.rotate_axis(axis, math.radians(angle))

        bpy.ops.object.mode_set(mode='OBJECT') 
        
                                                          # Applies random rotation to the 3 scene lights
        
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
        ob.rotation_mode = 'XYZ'                             # Set rotations to euler because quaternions are an alien technology
        axis = 'Z'  
        angle = random.uniform(0, 360)
        ob.rotation_euler.rotate_axis(axis, math.radians(angle))
        axis = 'Y' 
        angle = random.uniform(-40, 40)
        ob.rotation_euler.rotate_axis(axis, math.radians(angle))
        
              #   Background Randomization
        ob = bpy.data.objects['BG' + str(random.randint(1, 14))]
        ob.location[1] = -0.1

        
        
        ########    Blendshape Randomization    ########
    
        

        ob = bpy.data.objects[dest]
        
        #for shape in ob.data.shape_keys.key_blocks:
        selector = random.randint(0, 5)
        
        if selector == 0:
            combo1(ob, setShapes)
        if selector == 1:
            combo2(ob, setShapes)
        if selector == 2:
            combo3(ob, setShapes)  
        if selector == 3:
            combo4(ob, setShapes)
        if selector == 4:
            combo5(ob, setShapes)
        if selector == 5:
            combo6(ob, setShapes)
            
        return setShapes
            
            
        

#bpy.app.handlers.frame_change_post.append(main)
bpy.ops.wm.console_toggle()

print("Start Transfer")
dest = get_objs('MB_LAB_Character')
source = None
if dest == 'MBlab_CA_M':
    source = 'MBLabBase_CA_M'
if dest == 'MBlab_CA_F':
    source = 'MBLabBase_CA_F'
if dest == 'MBlab_AF_M':
    source = 'MBLabBase_AF_M'
if dest == 'MBlab_AF_F':
    source = 'MBLabBase_AF_F'
if dest == 'MBlab_AS_M':
    source = 'MBLabBase_AS_M'
if dest == 'MBlab_AS_F':
    source = 'MBLabBase_AS_F'
if dest == 'MBlab_LA_M':
    source = 'MBLabBase_LA_M'
if dest == 'MBlab_LA_F':
    source = 'MBLabBase_LA_F'
copy_all_shape_keys(source, dest)
print("End Transfer") 

for i in range(s.frame_start,s.frame_end):              # Rendering stuff
    
    path = "E:\\DIYSHIT\\FaceTracker\\Output\\"

#for i in range(1): 
    s.frame_current = i
    imagename = str(s.frame_current ).zfill(3)
    
    zero_camera() 
    zero_lights()
    zero_blendshapes(dest)
    filename = str(imagename + '.csv')
    img_filename = str(imagename + '.png')
    data = main(dest)
    data[33] = img_filename
    joined_string = ','.join(map(str, data)) 
    lables = ','.join(map(str, lables_name)) 
    with open(path + filename, 'w') as file:
        file.write('{}\n{}\n'.format(lables,joined_string))
        file.close()
    print(data)
    sleep(.300)


    s.render.filepath = (
                        #"C:\\temp\\" # some path
                        path
                        + imagename
                        )
    bpy.ops.render.render( #{'dict': "override"},
                          #'INVOKE_DEFAULT',  
                          False,            
                          animation=False, 
                          write_still=True
                         )


    # Do whatever you want that can't be done normally here (Changing resolution during animation, etc...)


    
    

