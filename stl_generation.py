from typing import List, Tuple
import os
import numpy as np
from numpy import double
import cv2
import math
import bpy
import bmesh

#region ############################## Parameters ##############################

class MeshMandatoryParameters:
	"""Represents the different mandatory parameters to generate a mesh"""
	def __init__(self, outputMeshPath:str, numberOfPointsPerPixel: int = 1, desiredSize: Tuple[double, double, double] = (100., 100., 10.), desiredThickness: double = 5., saveSTL : bool = True, saveBlendFile : bool = True) -> None:
		"""Constructor of the MeshMandatoryParameters.

		Args:
			outputMeshPath(str): The path towards the output mesh
			numberOfPointsPerPixel (int): The number of mesh points that are mapped to one pixel of the source image
			desiredSize (tuple(double, double, double)): The desired dimensions (x, y, zmax), expressed in mm
			desiredThickness(double): The minimum desired thickness of the plane, in mm
			saveSTL(bool): If True, an STL mesh will be generated
			saveBlendFile(bool): If True, the resulting Blender scene will be saved
		"""
		self.outputMeshPath = outputMeshPath
		self.numberOfPointsPerPixel = numberOfPointsPerPixel
		self.desiredSize = desiredSize
		self.desiredThickness = desiredThickness
		self.saveSTL = saveSTL
		self.saveBlendFile = saveBlendFile

class OperatorsOpionalParameters:
	"""Represents the different optional parameters used by the operators to generate a mesh"""
	def __init__(self, displaceEccentricity: int = 16, smoothingNbRepeats: int = 5, smoothingFactor : double = 1., smoothingBorder : double = 0., decimateAngleLimit : double = 0.1) -> None:
		"""Constructor of the MeshMandatoryParameters.

		Args:
			displaceEccentricity (int): Maximum excentricity of the texture : higher values reduces blur / at oblique angles but is slower
			smoothingNbRepeats (int): Number of times the smooth modifier is applied
			smoothingFactor (double): Lambda factor of the smooth modifier
			smoothingBorder (double): Lambda factor in border
			decimateAngleLimit (double): Maximum angle allowed, expressed in radians because it is the unit of Blender
		"""
		self.displaceEccentricity = displaceEccentricity 
		self.smoothingNbRepeats = smoothingNbRepeats 
		self.smoothingFactor = smoothingFactor 
		self.smoothingBorder = smoothingBorder 
		self.decimateAngleLimit = decimateAngleLimit
	
#endregion

#region ############################## Files ##############################

def generateNameResultingFile(inputFilepath : str, desiredFormat : str):
	"""
	Generate a filename from the inputFilepath.

	Args:
		inputFilepath(str): The path towards the original file
		desiredFormat(str): The format of the resulting file (WITHOUT the dot)
	"""
	resultingName = ""
	if (os.path.isdir(inputFilepath)):
		# Create a name for the output mesh
		resultingName = os.path.join(inputFilepath, "result." + desiredFormat)
	else:
		resultingName = os.path.splitext(inputFilepath)[0] + "_result." + desiredFormat
	return resultingName


def load_grayscale_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return grayscale_image

#endregion

#region ############################## Mesh generation ##############################

def generate_vertices_top(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    vertices_top = np.array([(x, y, grayscale_image[x,y]) for y in range(nb_pts_y) for x in range(nb_pts_x)])
    vertices_top = vertices_top / (nb_pts_x-1, nb_pts_y-1, 255)
    return vertices_top

def generate_vertices_border(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    vertices_border = np.array([(x, y, -1) for y in range(nb_pts_y) for x in range(nb_pts_x) if x == 0 or y == 0 or x == nb_pts_x-1 or y == nb_pts_y-1])
    vertices_border = vertices_border / (nb_pts_x-1, nb_pts_y-1, 10)
    return vertices_border

def generate_vertices_bottom() -> np.ndarray:
    vertices_bottom = np.array([(0,0,-1),
                                (1,0,-1),
                                (0,1,-1),
                                (1,1,-1)])
    return vertices_bottom

def scale_vertices(vertices: np.ndarray, scale: Tuple[double, double, double]) -> np.ndarray:
    return vertices * scale

def generate_faces_top(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    
    def index(x, y):
        return x+nb_pts_x*y
    
    list_index = np.array([index(x,y) for x in range(nb_pts_x-1) for y in range(nb_pts_y-1)])
    faces_first_half = list(zip(list_index, list_index+1, list_index+nb_pts_x))
    faces_second_half = list(zip(list_index+1, list_index+1+nb_pts_x, list_index+nb_pts_x))
    faces_top = np.vstack((faces_first_half, faces_second_half))
    return faces_top

def generate_faces_border(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    nb_vert_top = nb_pts_x*nb_pts_y
    nb_vert_bords = 2*(nb_pts_x + nb_pts_y) - 4
    
    def index(x, y):
        return x+nb_pts_x*y
    
    def index_bord(x,y):
        if y == 0:
            return nb_vert_top + x
        if y == nb_pts_y-1:
            return nb_vert_top + nb_vert_bords - (nb_pts_x - x)
        if x == 0:
            return nb_vert_top + nb_pts_x + 2*(y-1)
        if x == nb_pts_x-1:
            return nb_vert_top + nb_pts_x + 2*(y-1) + 1
        return -1
    
    faces_border = np.vstack((
        [(index(x,y-1),index(x,y),index_bord(x,y)) for y in range(1, nb_pts_y) for x in [0] ], # bord haut premier triangle
        [(index(x,y),index_bord(x,y+1),index_bord(x,y)) for y in range(0, nb_pts_y-1) for x in [0] ], # bord haut deuxième triangle
        [(index(x,y),index(x,y-1),index_bord(x,y)) for y in range(1, nb_pts_y) for x in [nb_pts_x-1] ], # bord bas premier triangle
        [(index_bord(x,y+1),index(x,y),index_bord(x,y)) for y in range(0, nb_pts_y-1) for x in [nb_pts_x-1] ], # bord bas deuxième triangle
        [(index(x,0),index(x-1,0),index_bord(x,y)) for x in range(1, nb_pts_x) for y in [0] ], # bord gauche premier triangle
        [(index_bord(x+1,0),index(x,0),index_bord(x,y)) for x in range(0, nb_pts_x-1) for y in [0] ], # bord gauche deuxième triangle
        [(index(x-1,y),index(x,y),index_bord(x,y)) for x in range(1, nb_pts_x) for y in [nb_pts_y-1] ], # bord droit premier triangle
        [(index(x,y),index_bord(x+1,y),index_bord(x,y)) for x in range(0, nb_pts_x-1) for y in [nb_pts_y-1] ], # bord droit deuxième triangle
    ))
    return faces_border

def generate_faces_side(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    nb_vert_top = nb_pts_x*nb_pts_y
    nb_vert_bords = 2*(nb_pts_x + nb_pts_y) - 4
    nb_vert = nb_vert_top + nb_vert_bords + 4
    idx_sol_00 = nb_vert -4
    idx_sol_n0 = nb_vert -3
    idx_sol_0n = nb_vert -2
    idx_sol_nn = nb_vert -1
    
    def index_bord(x,y):
        if y == 0:
            return nb_vert_top + x
        if y == nb_pts_y-1:
            return nb_vert_top + nb_vert_bords - (nb_pts_x - x)
        if x == 0:
            return nb_vert_top + nb_pts_x + 2*(y-1)
        if x == nb_pts_x-1:
            return nb_vert_top + nb_pts_x + 2*(y-1) + 1
        return -1

    faces_side = np.vstack((
        [[idx_sol_00, index_bord(x+1, 0), index_bord(x, 0)] for x in range(nb_pts_x-1)],
        [[idx_sol_n0, index_bord(nb_pts_x-1, 0), idx_sol_00]],
        [[idx_sol_00, index_bord(0, y), index_bord(0, y+1)] for y in range(nb_pts_y-1)],
        [[idx_sol_0n, idx_sol_00, index_bord(0, nb_pts_y-1)]],
        [[idx_sol_nn, index_bord(x, nb_pts_y-1), index_bord(x+1, nb_pts_y-1)] for x in range(nb_pts_x-1)],
        [[idx_sol_nn, idx_sol_0n, index_bord(0, nb_pts_y-1)]],
        [[idx_sol_nn, index_bord(nb_pts_x-1, y+1), index_bord(nb_pts_x-1, y)] for y in range(nb_pts_y-1)],
        [[idx_sol_nn, index_bord(nb_pts_x-1, 0), idx_sol_n0]]
    ))
    return faces_side

def generate_faces_bottom(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    nb_vert_top = nb_pts_x*nb_pts_y
    nb_vert_bords = 2*(nb_pts_x + nb_pts_y) - 4
    nb_vert = nb_vert_top + nb_vert_bords + 4
    idx_sol_00 = nb_vert -4
    idx_sol_n0 = nb_vert -3
    idx_sol_0n = nb_vert -2
    idx_sol_nn = nb_vert -1
    faces_bottom = np.array([[idx_sol_00, idx_sol_0n, idx_sol_n0],
                    [idx_sol_nn, idx_sol_n0, idx_sol_0n]])
    return faces_bottom

def generate_mesh(image_path: str, desired_width: float, desired_height: float, desired_thikness_top: float, desired_thikness_base: float, pts_par_px: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    grayscale_image = load_grayscale_image(image_path)
    
    vertices_top = generate_vertices_top(grayscale_image, pts_par_px)
    vertices_border = generate_vertices_border(grayscale_image, pts_par_px)
    vertices_bottom = generate_vertices_bottom()
    
    # OpenCV uses x for rows and y for columns, such as [0,1] is top right and [1,0] botttom left
    # We want to use the opposite, so width and height are reversed in the following lines
    vertices_top = scale_vertices(vertices_top, (desired_height, desired_width, desired_thikness_top))
    vertices_border = scale_vertices(vertices_border, (desired_height, desired_width, desired_thikness_base))
    vertices_bottom = scale_vertices(vertices_bottom, (desired_height, desired_width, desired_thikness_base))
    
    all_vertices = np.vstack((vertices_top, vertices_border, vertices_bottom))
    
    faces_top = generate_faces_top(grayscale_image, pts_par_px)
    faces_border = generate_faces_border(grayscale_image, pts_par_px)
    faces_side = generate_faces_side(grayscale_image, pts_par_px)
    faces_bottom = generate_faces_bottom(grayscale_image, pts_par_px)
    
    all_faces = np.vstack((faces_top, faces_border, faces_side, faces_bottom))
    
    return all_vertices, all_faces

#endregion

#region ############################## Blender ##############################

def blender_new_empty_scene() -> None:
	scene = bpy.context.scene
	for obj in scene.objects:
		bpy.data.objects.remove(obj)

	for tex in bpy.data.textures:
		bpy.data.textures.remove(tex, do_unlink=True)


def blender_new_object(vertices: np.ndarray, faces: np.ndarray, object_name: str = "object", mesh_name: str = "mesh") -> bpy.types.Object:
    vertices = list(vertices)
    edges = []
    faces = list(faces)
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()

    object = bpy.data.objects.new(object_name, mesh)
    bpy.context.collection.objects.link(object)
    return object
    
def blender_create_vertex_groups(object: bpy.types.Object, vertices: np.ndarray) -> None:
    max_x = max(vertices ,key=lambda item:item[0])[0]
    max_y = max(vertices ,key=lambda item:item[1])[1]
    indices_of_face_vertices = [i for i,(x,y,_) in enumerate(vertices) if x != 0 and y != 0 and x != max_x and y != max_y]
    indices_of_side_vertices = [i for i,(x,y,_) in enumerate(vertices) if x == 0 or y == 0 or x == max_x or y == max_y]
    
    face_vertex_group = object.vertex_groups.new(name='Face')
    face_vertex_group.add(indices_of_face_vertices, 1.0, 'ADD')
    
    side_vertex_group = object.vertex_groups.new(name='Sides')
    side_vertex_group.add(indices_of_side_vertices, 1.0, 'ADD')
    

def blender_select_object(object: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = object


def blender_add_decimate_modifier(object: bpy.types.Object, ratio: float, apply: bool = False) -> None:
    decimateModifier = object.modifiers.new(name="Decimator", type='DECIMATE')
    decimateModifier.ratio = ratio
    
    if(apply):
        bpy.ops.object.modifier_apply(modifier="Decimator")

def approximation_decimate_ratio(vertices: np.ndarray) -> double:
    # Empirical calculation of the decimation ratio
    # We want to keep twice the amount of vertices corresponding to the perimeter of the image
    # We approximate that the image is a square of dimentions sqrt(n)*sqrt(n) where n is the amount of vertices
    # With this approximation, we have the perimeter p = 4s-4, appoximated to 4s
    # So we want to keep 4s vertices, which is 4s/n % of vertices
    return 4*math.sqrt(len(vertices))/len(vertices)

def blender_add_planar_decimate_modifier(object: bpy.types.Object, angle_limit_deg: float, apply: bool = False) -> None:
    decimateModifier = object.modifiers.new(name="Planar Decimator", type='DECIMATE')
    decimateModifier.decimate_type = 'DISSOLVE'
    decimateModifier.angle_limit = math.radians(angle_limit_deg)
    
    if(apply):
        bpy.ops.object.modifier_apply(modifier="Planar Decimator")

def blender_add_weld_modifier(object: bpy.types.Object, merge_threshold: float, vertex_group: str = "Face", apply: bool = False) -> None:
    weldModifier = object.modifiers.new(name="Weld", type='WELD')
    weldModifier.mode = 'CONNECTED'
    weldModifier.merge_threshold = merge_threshold
    weldModifier.vertex_group = vertex_group
    
    if(apply):
        bpy.ops.object.modifier_apply(modifier="Decimator")

def blender_add_triangulate_modifier(object: bpy.types.Object, apply: bool = False) -> None:
    object.modifiers.new(name="Triangulate", type='TRIANGULATE')

    if(apply):
        bpy.ops.object.modifier_apply(modifier="Triangulate")

def approximation_weld_threshold(vertices: np.ndarray, merge_radius: double = 3) -> double:
    # This thershold will merge together pixels that are close together
    # This should only apply to pixels in the same plane, unless planes are very close together
    # The distance between two neighbour vertices of the same plane is equal to the first vertex's x coordinate
    # We multiply this value by 1.5 (> sqrt(2)) to allow merging of diagonal vertices
    # We then multiply by merge_radius in order to merge vertices that are n spaces away
    return 1.5*merge_radius*vertices[1][0]

def blender_export(filepath: str, stl: bool = True, blend: bool = False) -> None:
    if stl:
        bpy.ops.export_mesh.stl(filepath=f"{filepath}.stl", use_mesh_modifiers=True)
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=f"{filepath}.blend")

def blender_generate_stl(filepath: str, vertices: np.ndarray, faces: np.ndarray, stl: bool = True, blend: bool = False):
    blender_new_empty_scene()
    object = blender_new_object(vertices, faces)
    blender_select_object(object)
    blender_create_vertex_groups(object, vertices)
    blender_add_decimate_modifier(object, approximation_decimate_ratio(vertices), apply=False)
    blender_add_weld_modifier(object, approximation_weld_threshold(vertices), vertex_group="Face", apply=False)
    blender_add_planar_decimate_modifier(object, angle_limit_deg=5, apply=False)
    blender_add_triangulate_modifier(object, apply=False)
    blender_export(filepath, stl=stl, blend=blend)

#endregion

#region ############################## Main method ##############################

def generateSTL(imagePath: str, meshMandatoryParameters: MeshMandatoryParameters, operatorsOpionalParameters: OperatorsOpionalParameters, fnUpdateProgress):
	"""
	Generate the mesh under the stl format.

	Args:
		imagePath(str): The path towards the depth map image
		meshMandatoryParameters(MeshMandatoryParameters): The mandatory parameters to generate the mesh
	"""
	# ## Check if the result of the generation will be saved in at least one format, otherwise raise an exception
	if not(meshMandatoryParameters.saveBlendFile or meshMandatoryParameters.saveSTL):
		raise("No output format detected, doing nothing")

	desired_width = meshMandatoryParameters.desiredSize[0]
	desired_height = meshMandatoryParameters.desiredSize[1]
	desired_thickness_top = meshMandatoryParameters.desiredThickness
	desired_thickness_bottom = meshMandatoryParameters.desiredSize[2]
 
	fnUpdateProgress(0, "Generation of the base mesh")
	vertices, faces = generate_mesh(imagePath, desired_width, desired_height, desired_thickness_top, desired_thickness_bottom)
	fnUpdateProgress(50, "Applying modifiers and exporting")
	blender_generate_stl(meshMandatoryParameters.outputMeshPath, vertices, faces, stl=meshMandatoryParameters.saveSTL, blend=meshMandatoryParameters.saveBlendFile)
	fnUpdateProgress(1000, "Done")

#endregion