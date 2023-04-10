#import bpy
import copy
def get_objs(collection):                   # Returns all meshes in a collection
    collection = bpy.data.collections[collection]
    for obj in collection.all_objects:
        ob = bpy.data.objects[str(obj.name)]
        if ob.type == 'MESH':
            mesh_name = obj.name
            #shapekey_name = shapekey_name.split()
    return mesh_name 

class Defines():
    shape_defs = dict(              # 29 shapes
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

    shape_index = ["cheekPuff", "jawOpen", "jawForward", "jawLeft", "jawRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", 
    "mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthSmileLeft", 
    "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", 
    "mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthStretchLeft", 
    "mouthStretchRight", "tongueOut"]

    shape_bl = dict(  
        cheekPuff = ['cheekPuff', 'jawOpen', 'mouthFunnel', 'mouthShrugUpper', 'mouthShrugLower', 'mouthClose', 'mouthUpperUpLeft', 'mouthUpperUpRight', 'mouthLowerDownLeft', 'mouthLowerDownRight', 'tongueOut'],
        jawOpen = ['cheekPuff', 'jawOpen', 'mouthShrugLower', 'mouthShrugUpper'],
        jawForward = ['jawForward'],
        jawLeft = ['jawLeft', 'jawRight'],
        jawRight = ['jawRight', 'jawLeft'],
        mouthFunnel = ['mouthFunnel', 'cheekPuff', 'mouthPucker', 'mouthRollUpper', 'mouthRollLower', 'mouthClose'],
        mouthPucker = ['mouthPucker', 'jawLeft', 'jawRight', 'mouthFunnel', 'mouthRollUpper', 'mouthRollLower', 'mouthClose'],
        mouthLeft = ['mouthLeft', 'mouthRight'],
        mouthRight = ['mouthRight', 'mouthLeft'],
        mouthRollUpper = ['mouthRollUpper', 'jawOpen', 'mouthFunnel', 'mouthPucker', 'mouthClose', 'mouthUpperUpLeft', 'mouthUpperUpRight'],
        mouthRollLower = ['mouthRollLower', 'jawOpen', 'mouthFunnel', 'mouthPucker', 'mouthClose', 'mouthLowerDownLeft', 'mouthLowerDownRight'],
        mouthShrugUpper = ['mouthShrugUpper', 'jawOpen', 'mouthClose', 'tongueOut'],
        mouthShrugLower = ['mouthShrugLower', 'jawOpen', 'mouthClose', 'tongueOut'],
        mouthClose = ['mouthFunnel', 'mouthPucker', 'mouthClose', 'mouthShrugUpper', 'mouthShrugLower'],
        mouthSmileLeft = ['mouthSmileLeft', 'mouthFrownLeft', 'mouthDimpleLeft', 'mouthPressLeft', 'mouthStretchLeft'],
        mouthSmileRight = ['mouthSmileRight', 'mouthFrownRight', 'mouthDimpleRight', 'mouthPressRight', 'mouthStretchRight'],
        mouthFrownLeft = ['mouthSmileLeft', 'mouthFrownLeft', 'mouthDimpleLeft', 'mouthPressLeft', 'mouthStretchLeft'],
        mouthFrownRight = ['mouthSmileRight', 'mouthFrownRight', 'mouthDimpleRight', 'mouthPressRight', 'mouthStretchRight'],
        mouthDimpleLeft = ['mouthSmileLeft', 'mouthFrownLeft', 'mouthDimpleLeft', 'mouthPressLeft', 'mouthStretchLeft'],
        mouthDimpleRight = ['mouthSmileRight', 'mouthFrownRight', 'mouthDimpleRight', 'mouthPressRight', 'mouthStretchRight'],
        mouthUpperUpLeft = ['mouthUpperUpLeft', 'mouthRollUpper'],
        mouthUpperUpRight = ['mouthUpperUpRight', 'mouthRollUpper'],	
        mouthLowerDownLeft = ['mouthUpperUpLeft', 'mouthRollLower'],
        mouthLowerDownRight = ['mouthUpperUpRight', 'mouthRollLower'],		
        mouthPressLeft = ['mouthSmileLeft', 'mouthFrownLeft', 'mouthDimpleLeft', 'mouthPressLeft', 'mouthStretchLeft'],
        mouthPressRight = ['mouthSmileRight', 'mouthFrownRight', 'mouthDimpleRight', 'mouthPressRight', 'mouthStretchRight'],
        mouthStretchLeft = ['mouthSmileLeft', 'mouthFrownLeft', 'mouthDimpleLeft', 'mouthPressLeft', 'mouthStretchLeft'],
        mouthStretchRight = ['mouthSmileRight', 'mouthFrownRight', 'mouthDimpleRight', 'mouthPressRight', 'mouthStretchRight'],
        tongueOut = ['tongueOut']
        )

class ShapeSetter():
    def __init__(self):
        self.blacklist = []           
        self.randomized_shapes = []
        self.possible_shapes = []
        self.count = 0

    def reset(self, DefsClass):
        defs = DefsClass
        self.blacklist = []                  # Reset
        self.randomized_shapes = []
        self.possible_shapes = copy.copy(defs.shape_index)

    def get_avalible_shapes(self, DefsClass, classExample):
        defs = DefsClass
        if type(classExample) == int:               # Take either String or int
            classExample = defs.shape_index[classExample]
        if type(classExample) == str:
            classExample = defs.shape_index[defs.shape_index.index(classExample)]

        self.blacklist.append(defs.shape_bl[classExample])    # Add the class example's blacklist to start
        #print(shape)
        #print(f'Blacklist: {self.blacklist}')
        for i in range(len(self.possible_shapes)):   # Check Blacklist for every potential shape
            for j in range(len(self.blacklist)):
                for k in range(len(self.blacklist[j])):      # If there's a blacklisted item in potential shapes, remove it
                    if self.blacklist[j][k] in self.possible_shapes:
                        self.possible_shapes.pop(self.possible_shapes.index(self.blacklist[j][k]))
                        #print(f'Possible Shapes: {self.possible_shapes}')
        return(self.possible_shapes)
    
    def tick(self):
        self.count += 1
FRAME_START = 0
FRAME_END = 100

defines = Defines()
setter = ShapeSetter()

setter.reset(defines)
possible_shapes = setter.get_avalible_shapes(defines, "cheekPuff")
setter.reset(defines)
possible_shapes = setter.get_avalible_shapes(defines, 1)

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

    
    
    
    
    
    