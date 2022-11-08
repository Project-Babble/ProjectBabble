# For use with the RenderSceneV2 Blender project

################################
# Blender will appear to hang when run
# That's just how blender runs scripts :shrug:
################################
import bpy
import math
import random
import socket
import pickle
import struct
from time import sleep
  
# Set path for enviroment
path = "C:\\Users\\epicm\\Documents\\GitHub\\ProjectBabble\\datageneration\\Output\\"

res_x = 800
res_y = 800


blendshape_list = (
'eyeLeftSqueeze',
'eyeRightSqueeze',
'Expressions_eyeSquintL_max',
'Expressions_eyeSquintR_max',
'Expressions_eyeClosedL_max',
'eyeLookInLeft',
'eyeLookOutLeft',
'eyeLookUpLeft',
'eyeLookDownLeft',
'Expressions_eyeClosedR_max',
'eyeLookOutRight',
'eyeLookInRight',
'eyeLookUpRight',
'eyeLookDownRight',
'Expressions_eyeClosedL_min',
'Expressions_eyeClosedR_min',
'eyesDilationLeft',
'eyesDilationRight',
'eyesConstrictLeft',
'eyesConstrictRight',
'browInnerUpLeft',
'browInnerUpRight',
'Expressions_browOutVertL_min',
'Expressions_browOutVertR_min',
'Expressions_browOutVertL_max',
'Expressions_browOutVertR_max',
'Expressions_eyeSquintL_max',
'Expressions_eyeSquintR_max',
'cheekPuffLeft',
'cheekPuffRight',
'Expressions_cheekSneerL_max',
'Expressions_cheekSneerR_max',
'Expressions_mouthInflated_min', 
'lipSuckLeftBottom',
'lipSuckLeftTop',
'lipSuckRightBottom',
'lipSuckRightTop',
'Expressions_mouthOpen_max',
'Expressions_jawHoriz_max',
'Expressions_jawHoriz_min',
'Expressions_jawOut_max',
'Expressions_mouthOpenO_min',
'Expressions_mouthOpenO_max',
'Expressions_mouthOpenLarge_min', 
'mouthClose', 
'mouthApeShape', 
'Expressions_mouthHoriz_max', 
'Expressions_mouthHoriz_min',
'Expressions_mouthSmileL_max',
'Expressions_mouthSmileR_max',
'mouthFrownLeft',
'mouthFrownRight',
'mouthDimpleLeft',
'mouthDimpleRight',
'mouthRollUpper',
'Expressions_mouthLowerOut_min',
'mouthShrugUpper',
'mouthLowerOverturn',
'mouthShrugLower',
'mouthUpperUpLeft',
'mouthUpperUpRight',
'mouthLowerDownLeft',
'mouthLowerDownRight',
'mouthPressLeft',
'mouthPressRight',
'mouthStretchLeft',
'mouthStretchRight',
'Expressions_tongueOut_max',
'Expressions_tongueVert_min',
'Expressions_tongueVert_max',
'Expressions_tongueHoriz_max',
'Expressions_tongueHoriz_min',
'tongueRoll'
)


def send_msg(sock, msg):                            
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def zero_blendshapes(ob):                       # Resets all Blendshapes to 0
    for shape in ob.data.shape_keys.key_blocks:
        shape.value=0

        
def get_set_values(ob, blendshape_list, set_list):  # Debug function to get the value of blendshapes
    for shape in ob.data.shape_keys.key_blocks:
        if shape.name in blendshape_list:
            set_list.append(shape.value)
          
def zero_bg():                  # Sets the Z position of all backgrounds to 0
    for i in range(14):
        ob = bpy.data.objects['BG' + str(i + 1)]
        ob.location[1] = 0
    
    
def randomize_bg():             # Moves a random background plane to be in view
    ob = bpy.data.objects['BG' + str(random.randint(1, 14))]
    ob.location[1] = -0.1
        
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
            
def randomize_scene():              # Randomizes various scene parameters like lighting and camera focal length
    ob = bpy.data.cameras['Camera']  
    ob.lens = round(random.uniform(22, 30), 2)
    
    ob = bpy.data.scenes["Scene"].node_tree.nodes["Lens Distortion"].inputs[1]           # Compositer Lens Distortion
    ob.default_value = random.uniform(0.01, 0.27)                
    # Camera 
    ob = bpy.data.objects['CameraRig']  # The thing we're talking about
    bpy.context.view_layer.objects.active = ob   # Click it (make it the active selection)
    bpy.ops.object.mode_set(mode='POSE')    # Go into pose mode
    pbone = ob.pose.bones['Camera']   # Select the bone to rotate
    pbone.rotation_mode = 'XYZ'     # Set rotations to euler because quaternions are an alien technology
    axis = 'Z'  # Select rotaion axis (local)
    angle = random.uniform(-2, 3)
    pbone.rotation_euler.rotate_axis(axis, math.radians(angle))             # Do the rotation
    
    # Camera Arm
    bpy.ops.object.mode_set(mode='POSE')   
    pbone = ob.pose.bones['CameraArm']  
    pbone.rotation_mode = 'XYZ'   
    axis = 'Z' 
    angle = random.uniform(-2, 2)
    pbone.rotation_euler.rotate_axis(axis, math.radians(angle))
    
    # MLabHead    
    bpy.ops.object.mode_set(mode='POSE')   
    pbone = ob.pose.bones['MBLabHead'] 
    pbone.rotation_mode = 'XYZ'    
    axis = 'Y' 
    angle = random.uniform(-3, 3)
    pbone.rotation_euler.rotate_axis(axis, math.radians(angle))
    
    bpy.ops.object.mode_set(mode='POSE')    
    pbone = ob.pose.bones['MBLabHead']  
    pbone.rotation_mode = 'XYZ'   
    axis = 'Z' 
    angle = random.uniform(-3, 3)
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
    ob.rotation_mode = 'XYZ'                
    axis = 'Z'  
    angle = random.uniform(0, 360)
    ob.rotation_euler.rotate_axis(axis, math.radians(angle))
    axis = 'Y' 
    angle = random.uniform(-40, 40)
    ob.rotation_euler.rotate_axis(axis, math.radians(angle))
            
        



def set_shape(shapekey_name, ob, value):  # Set a value to a blendshape
            ob.data.shape_keys.key_blocks[shapekey_name].value = value

bpy.ops.wm.console_toggle()     # Toggle the system console 

                                   # Setup Connection
HOST = 'localhost'
PORT = 50000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

scene=bpy.context.scene

scene.render.resolution_x = res_x
scene.render.resolution_y = res_y


try: 
    while True:                                # Recieve Blendshape List
        conn, (address, port) = s.accept()
        data = recv_msg(conn)
        render_job = pickle.loads(data)
        print(f'Got Blendshapes containing {render_job}')
                                                        # Acknowledge blendshape list
        ack_msg = pickle.dumps('Got Blendshape Lists')
        send_msg(conn, ack_msg)
        
        ob = bpy.data.objects['MBLab_CA_M']
        print('Set Object')
        set_list = []
        if render_job:
            print('Starting Render')
            image_count = 0
            for i in render_job:
                c = 0
                zero_camera()
                zero_blendshapes(ob)
                zero_bg()
                for value in i:
                    #print(f'Setting Blendshape of: {blendshape_list[c]}')
                    set_shape(blendshape_list[c], ob, value)
                    c += 1
                get_set_values(ob, blendshape_list, set_list)
                print('Started Blender Render Process')
                randomize_bg()
                randomize_scene()
                                                        # Blender render stuff
                imagename = str(image_count).zfill(3)    
                img_filename = str(imagename + '.png')
                scene.render.filepath = (
                            path
                            + imagename
                            )
                bpy.ops.render.render( #{'dict': "override"},
                            #'INVOKE_DEFAULT',  
                            False,            
                            animation=False, 
                            write_still=True
                            )
                image_count += 1
            render_job = None
        else:
            print('No renderjob')

        fin_msg = pickle.dumps("Fin")
        send_msg(conn, fin_msg)

        
except: 
    print('Failed, Closing socket')
    s.close()
    



