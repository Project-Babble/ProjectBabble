import bpy
import bmesh
from bpy_extras.object_utils import world_to_camera_view

depsgraph = bpy.context.evaluated_depsgraph_get()

obj = bpy.data.objects['BabbleCA_M']

bm = bmesh.new()

bm.from_object( obj, depsgraph )

bm.verts.ensure_lookup_table()

print( "----" )
count = 0
vertex_list = [19608, 33702, 41317, 7771, 40727, 2095, 26611, 2109, 54742, 7774, 68290, 16536, 19608, # Outer lips, Right Corner 
21682, 68677, 30443, 55157, 41480, 54744, 30167, 68292, # Inner Lips, Right corner
46891, 34154, 34281, 48584, 48515, 7803, 21396, 21630, 19288, 19164, 18185, # Jaw
16930, 16931, 16932, 16933, 16934, 19842, 20009, 19873, 19450, 38951, 34843, 32201, 35730, 35656, 32817, 33715, 26063, 44402, 26127, 23670, 46956, 23612, 30818, # Right Cheek
2503, 2504, 2505, 2506, 2507, 25550, 25681, 25813, 52707, 25585, 41180, 30676, 35188, 34994, 37629, 39633, 36976, 20088, 38266, 38968, 18141, 38730, 51128, # Left Cheek
16956, 18101, 7809, 25316, 2529, 45422, 2765, 44543, 7817, 35141, 17192, # Upper/LowerLips area
68913, 41470, 7767, 27227, 55410, # Nose
34334, 16148, 16117, 16120 # Tongue
]
vertices = []
for v in bm.verts:
    #print(count)
    if count in vertex_list:
        print( v.co )
        vertices.append(v.co)
    count += 1
print(vertices)

bm.free()

scene = bpy.context.scene
cam = bpy.data.objects['ViveCamera'] 
...
obj = bpy.data.objects['BabbleCA_M']
print("Working on object: %s" % obj.name)
landmarks = []
count = 0
for value in vertex_list:
    vert = obj.data.vertices[value]
    vert = vertices[count]
    count += 1
    vert.select = True
    # local to global coordinates
    co = obj.matrix_world @ vert.co
    print(co)
    #co = obj.evaluated_get(context.view_layer.depsgraph).data.vertices[0].co
    coords2d = world_to_camera_view(scene, cam, co) 
    coord = [coords2d.x, coords2d.y]
    for i in range(len(coord)):            # Clip values between 0 - 1
        coord[i] = max(min(coord[i], 1), 0) 
    landmarks.append(coord)
    #print(coord) 
    #print("coords2d: {},{}".format(coords2d.x, coords2d.y))
print(landmarks) 