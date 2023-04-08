import bpy

def get_objs(collection):                   # Returns all meshes in a collection
    collection = bpy.data.collections[collection]
    for obj in collection.all_objects:
        ob = bpy.data.objects[str(obj.name)]
        if ob.type == 'MESH':
            mesh_name = obj.name
            #shapekey_name = shapekey_name.split()
    return mesh_name 
# Get the currently selected object
shape_defs = dict(
    cheekPuff = 'mouthInflate',
    jawOpen = 'Expressions_mouthOpen_max',
    jawForward = 'Expressions_jawOut_max',     # added
    jawLeft = 'jawLeft',     # added
    jawRight = 'jawRight',     # added
    mouthFunnel = 'mouthFunnel',     # added
    mouthPucker = 'mouthPucker', # fixed in vrcft master
    mouthLeft = 'mouthLeft',     # added
    mouthRight = 'mouthRight',     # added
    mouthRollUpper = 'mouthRollUpper',     # fixed in vrcft master
    mouthRollLower = 'mouthRollLower',     # fixed in vrcft master
    mouthShrugUpper = 'mouthShrugUpper',     # added
    mouthShrugLower = 'mouthShrugLower',     # added
    mouthClose = 'mouthClose',             # MUST BE EQUAL TO jawOpen
    mouthSmileLeft = 'mouthSmileL',     # added
    mouthSmileLeft_bl = ['mouthSmileLeft', 'mouthFrownLeft', ]
    mouthSmileRight = 'mouthSmileR',    # added
    mouthFrownLeft = 'mouthFrownLeft',     # added
    mouthFrownRight = 'mouthFrownRight',     # added
    mouthDimpleLeft = 'mouthDimple_L',   # added
    mouthDimpleRight = 'mouthDimple_R',      # added
    mouthUpperUpLeft = 'mouthUpperUp_L',      # added				
    mouthUpperUpRight = 'mouthUpperUp_R',      # added
    mouthLowerDownLeft = 'mouthLowerDown_L', 	 # added	
    mouthLowerDownRight = 'mouthLowerDown_R',      # added
    mouthPressLeft = 'mouthPress_L',      # added
    mouthPressRight = 'mouthPress_R',      # added
    mouthStretchLeft = 'mouthStretch_L',     # added
    mouthStretchRight = 'mouthStretch_R',    # added
    tongueOut = 'tongueOut'
)

shapes_index = ["cheekPuff", "jawOpen", "jawForward", "jawLeft", "jawRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", 
"mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmileLeft", 
"mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", 
"mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthStretchLeft", 
"mouthStretchRight", "tongueOut"]

cheekPuff_bl = ['cheekPuff', 'jawOpen', 'mouthFunnel', 'mouthShrugUpper', 'mouthShrugLower', 'mouthClose', 'mouthUpperUpLeft', 'mouthUpperUpRight', 'mouthLowerDownLeft', 'mouthLowerDownRight', 'tongueOut']
jawOpen_bl = ['cheekPuff', 'jawOpen', 'mouthShrugLower', 'mouthShrugUpper']
jawForward_bl = ['jawForward']
jawLeft_bl = ['jawLeft', 'jawRight']
jawRight_bl = ['jawRight', 'jawLeft']
mouthFunnel_bl = ['mouthFunnel', 'cheekPuff', 'mouthPucker', 'mouthRollUpper', 'mouthRollLower', 'mouthClose']
mouthPucker_bl = ['mouthPucker', 'jawLeft', 'jawRight', 'mouthFunnel', 'mouthRollUpper', 'mouthRollLower', 'mouthClose']
mouthLeft_bl = ['mouthLeft', 'mouthRight']
mouthRight_bl = ['mouthRight', 'mouthLeft']
mouthRollUpper_bl = ['mouthRollUpper', 'jawOpen', 'mouthFunnel', 'mouthPucker', 'mouthClose', 'mouthUpperUpLeft', 'mouthUpperUpRight']
mouthRollLower_bl = ['mouthRollLower', 'jawOpen', 'mouthFunnel', 'mouthPucker', 'mouthClose', 'mouthLowerDownLeft', 'mouthLowerDownRight']
mouthShrugUpper_bl = ['mouthShrugUpper', 'jawOpen', 'mouthClose', 'tongueOut']
mouthShrugLower_bl = ['mouthShrugLower', 'jawOpen', 'mouthClose', 'tongueOut']
mouthClose_bl = ['mouthFunnel', 'mouthPucker', 'mouthClose', 'mouthShrugUpper', 'mouthShrugLower']
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

obj = bpy.context.object
start_kf = bpy.context.scene.frame_start
end_kf = bpy.context.scene.frame_end


'''
counter = 0
for frameNumber in range(0, bpy.context.scene.frame_end):
    for shapekey in range(0, bpy.context.scene.frame_end):
        obj.data.shape_keys.key_blocks[shapekey].value = 1.0 if (frameNumber == counter) else 0.0
        obj.data.shape_keys.key_blocks[shapekey].keyframe_insert(data_path="value", frame=frameNumber)
        counter += 1
    obj.data.shape_keys.key_blocks[counter - 1].value = 0.0
    counter = 0
'''

# Selector Algo

'''
select class example
roll shape value
add blacklist to interation blacklist
select shape not in blacklist
roll shape value 
add blacklist to iteration blacklist
'''
        # LowRange
count_inner = 0
count_outer = 0
iter_blacklist = []
class_exmaple = shapes_index[i]
iter_blacklist = blacklist_index[i]

count_inner += 1
if count_inner == len(shapes_index):
    count_inner = 0
    count_outer = 1
    
    
    
    
    
    