from contextlib import redirect_stdout
from dataclasses import dataclass
import sys
from typing import Tuple
import sys, os
import numpy as np
from numpy import double
import cv2
import math
import bpy
from contextlib import contextmanager
from progress import Progress

#region ############################## Parameters ##############################

@dataclass(repr=False, eq=False)
class MeshGenerationParameters:
    """Parameters used during mesh generation.

    Args:
        outputMeshPath(str): The path towards the output mesh
        meshWidthMM(int): The width of the mesh, in mm
        meshHeightMM(int): The height of the mesh, in mm
        meshBaseThicknessMM(int): The thickness of the base of the mesh, in mm
        meshImageThicknessMM(int): The thickness of the carved part of the mesh, in mm
        saveSTL(bool): If True, an STL mesh will be generated
        saveBlendFile(bool): If True, the resulting Blender scene will be saved
        verticesPerPixel (int): The number of vertices that are mapped to one pixel of the source image
    """
    outputMeshPath: str = "mesh"
    
    meshWidthMM: int = 100
    meshHeightMM: int = 100
    meshBaseThicknessMM: int = 5
    meshImageThicknessMM: int = 3
    
    saveSTL : bool = True
    saveBlendFile : bool = True
    
    verticesPerPixel: int = 1

#endregion

#region ############################## Files ##############################

def generateNameResultingFile(inputFilepath : str, desiredFormat : str) -> str:
	"""
	Generate a filename from the inputFilepath.

	Args:
		inputFilepath(str): The path towards the original file
		desiredFormat(str): The format of the resulting file (WITHOUT the dot)
	"""
	return os.path.splitext(inputFilepath)[0] + "." + desiredFormat


def load_grayscale_image(image_path: str) -> np.ndarray:
    """Loads an image as a grayscale matrix

    Args:
        image_path (str): Path to the image to load

    Returns:
        np.ndarray: The grayscale data of the image
    """
    image = cv2.imread(image_path)
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return grayscale_image

#endregion

#region ############################## Mesh generation ##############################

def generate_vertices_top(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    """Generates the vertices corresponding to the pixels in the source image

    Args:
        grayscale_image (np.ndarray): Source image as a grayscale matrix
        pts_par_px (int, optional): Amount of vertices per pixel. Defaults to 1. Unitl now no reason was found to increase it.

    Returns:
        np.ndarray: The generated vertices
    """
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    vertices_top = np.array([(x, y, grayscale_image[x,y]) for y in range(nb_pts_y) for x in range(nb_pts_x)])
    vertices_top = vertices_top / (nb_pts_x-1, nb_pts_y-1, 255)
    return vertices_top

def generate_vertices_border(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    """For each of the vertices placed on the sides of the object, creates a vertex under it
    This is necessary to prevent artifacts, where the side faces exceed the top boundary of the object

    Args:
        grayscale_image (np.ndarray): Source image as a grayscale matrix
        pts_par_px (int, optional): Amount of vertices per pixel. Defaults to 1.

    Returns:
        np.ndarray: The generated vertices
    """
    nb_pts_x = grayscale_image.shape[0]*pts_par_px
    nb_pts_y = grayscale_image.shape[1]*pts_par_px
    vertices_border = np.array([(x, y, -1) for y in range(nb_pts_y) for x in range(nb_pts_x) if x == 0 or y == 0 or x == nb_pts_x-1 or y == nb_pts_y-1])
    vertices_border = vertices_border / (nb_pts_x-1, nb_pts_y-1, 2)
    return vertices_border

def generate_vertices_bottom() -> np.ndarray:
    """Generates the four vertices on the bottom of the object

    Returns:
        np.ndarray: The generated vertices
    """
    vertices_bottom = np.array([(0,0,-1),
                                (1,0,-1),
                                (0,1,-1),
                                (1,1,-1)])
    return vertices_bottom

def scale_vertices(vertices: np.ndarray, scale: Tuple[double, double, double]) -> np.ndarray:
    """Scales vertices on each axis

    Args:
        vertices (np.ndarray): The vertices to scale
        scale (Tuple[double, double, double]): The scaling factors for each axis

    Returns:
        np.ndarray: The scaled vertices
    """
    return vertices * scale

def generate_faces_top(grayscale_image: np.ndarray, pts_par_px: int = 1) -> np.ndarray:
    """Generates the faces for the top part of the object

    Args:
        grayscale_image (np.ndarray): Source image as a grayscale matrix
        pts_par_px (int, optional): Amount of vertices per pixel. Defaults to 1.

    Returns:
        np.ndarray: The generated faces
    """
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
    """Generates the faces for the upper sides of the object

    Args:
        grayscale_image (np.ndarray): Source image as a grayscale matrix
        pts_par_px (int, optional): Amount of vertices per pixel. Defaults to 1.

    Returns:
        np.ndarray: The generated faces
    """
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
    """Generates the faces for the lower sides of the object

    Args:
        grayscale_image (np.ndarray): Source image as a grayscale matrix
        pts_par_px (int, optional): Amount of vertices per pixel. Defaults to 1.

    Returns:
        np.ndarray: The generated faces
    """
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
    """Generates the faces for the bottom part of the object

    Args:
        grayscale_image (np.ndarray): Source image as a grayscale matrix
        pts_par_px (int, optional): Amount of vertices per pixel. Defaults to 1.

    Returns:
        np.ndarray: The generated faces
    """
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

def generate_mesh(image_path: str, parameters: MeshGenerationParameters) -> Tuple[np.ndarray, np.ndarray]:
    """Generates a mesh from a grayscale image

    Args:
        image_path (str): Path to the grayscale image to be used
        parameters(MeshGenerationParameters): Mesh generation parameters

    Returns:
        Tuple[np.ndarray, np.ndarray]: Vertices and faces of the generated mesh
    """
    widthMM = parameters.meshWidthMM
    heightMM = parameters.meshHeightMM
    imageThicknessMM = parameters.meshImageThicknessMM
    baseThicknessMM = parameters.meshBaseThicknessMM
    pts_par_px = parameters.verticesPerPixel
    
    grayscale_image = load_grayscale_image(image_path)
    
    vertices_top = generate_vertices_top(grayscale_image, pts_par_px)
    vertices_border = generate_vertices_border(grayscale_image, pts_par_px)
    vertices_bottom = generate_vertices_bottom()
    
    # OpenCV uses x for rows and y for columns, such as [0,1] is top right and [1,0] botttom left
    # We want to use the opposite, so width and height are reversed in the following lines
    vertices_top = scale_vertices(vertices_top, (heightMM, widthMM, imageThicknessMM))
    vertices_border = scale_vertices(vertices_border, (heightMM, widthMM, baseThicknessMM))
    vertices_bottom = scale_vertices(vertices_bottom, (heightMM, widthMM, baseThicknessMM))
    
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
    """Empties the Blender scene before use
    """
    scene = bpy.context.scene
    for obj in scene.objects:
        bpy.data.objects.remove(obj)

    for tex in bpy.data.textures:
        bpy.data.textures.remove(tex, do_unlink=True)


def blender_new_object(vertices: np.ndarray, faces: np.ndarray, object_name: str = "object", mesh_name: str = "mesh") -> bpy.types.Object:
    """Creates a new object in the scene using mesh data

    Args:
        vertices (np.ndarray): The vertices of the mesh to use
        faces (np.ndarray): The faces of the mesh to use
        object_name (str, optional): The name given to the new object. Defaults to "object".
        mesh_name (str, optional): The name given to the mesh in Blender. Defaults to "mesh".

    Returns:
        bpy.types.Object: The newly created object
    """
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
    """Makes two vertex groups for the object : one for the upper face and one for the sides

    Args:
        object (bpy.types.Object): The object to edit
        vertices (np.ndarray): The vertices of the object's mesh
    """
    max_x = max(vertices ,key=lambda item:item[0])[0]
    max_y = max(vertices ,key=lambda item:item[1])[1]
    indices_of_face_vertices = [i for i,(x,y,_) in enumerate(vertices) if x != 0 and y != 0 and x != max_x and y != max_y]
    indices_of_side_vertices = [i for i,(x,y,_) in enumerate(vertices) if x == 0 or y == 0 or x == max_x or y == max_y]
    
    face_vertex_group = object.vertex_groups.new(name='Face')
    face_vertex_group.add(indices_of_face_vertices, 1.0, 'ADD')
    
    side_vertex_group = object.vertex_groups.new(name='Sides')
    side_vertex_group.add(indices_of_side_vertices, 1.0, 'ADD')
    

def blender_select_object(object: bpy.types.Object) -> None:
    """Has Blender select a given object

    Args:
        object (bpy.types.Object): The object to select
    """
    bpy.context.view_layer.objects.active = object


def blender_add_decimate_modifier(object: bpy.types.Object, ratio: float, apply: bool = False) -> None:
    """Adds a decimate modifier to an object.
    This modifier reduces the amount of vertices of the object

    Args:
        object (bpy.types.Object): The target object
        ratio (float): The ratio of vertices to keep
        apply (bool, optional): Applies the modifier to the object. Defaults to False.
    """
    decimateModifier = object.modifiers.new(name="Decimator", type='DECIMATE')
    decimateModifier.ratio = ratio
    
    if(apply):
        bpy.ops.object.modifier_apply(modifier="Decimator")

def approximation_decimate_ratio(vertices: np.ndarray) -> double:
    """Empirical calculation of the decimation ratio
    We want to keep twice the amount of vertices corresponding to the perimeter of the image
    We approximate that the image is a square of dimentions sqrt(n)*sqrt(n) where n is the amount of vertices
    With this approximation, we have the perimeter p = 4s-4, appoximated to 4s
    So we want to keep 4s vertices, which is 4s/n % of vertices

    Args:
        vertices (np.ndarray): The vertices of the target object

    Returns:
        double: The computed decimate ratio
    """
    
    return 4*math.sqrt(len(vertices))/len(vertices)

def blender_add_planar_decimate_modifier(object: bpy.types.Object, angle_limit_deg: float, apply: bool = False) -> None:
    """Adds a planar decimate modifier to an object.
    This modifier removes vertices if the difference it makes is an angle lower than a given limit

    Args:
        object (bpy.types.Object): The target object
        angle_limit_deg (float): Any angle greater than this limit will not be affected
        apply (bool, optional): Applies the modifier to the object. Defaults to False.
    """
    decimateModifier = object.modifiers.new(name="Planar Decimator", type='DECIMATE')
    decimateModifier.decimate_type = 'DISSOLVE'
    decimateModifier.angle_limit = math.radians(angle_limit_deg)
    
    if(apply):
        bpy.ops.object.modifier_apply(modifier="Planar Decimator")

def blender_add_weld_modifier(object: bpy.types.Object, merge_threshold: float, vertex_group: str = "Face", invert_vertex_group: bool = False, apply: bool = False) -> None:
    """Adds a weld modifier to an object.
    This modifier merges vertices that are closer than a given threshold

    Args:
        object (bpy.types.Object): The target object
        merge_threshold (float): Any vertices closer than this thershold are merged
        vertex_group (str, optional): Only merges vertices from (or not from, see invert_vertex_group) this vertex group. Defaults to "Face".
        invert_vertex_group (bool, optional): If true, inverts the vertex group (only merges vertices not in the vertex group). Defaults to False.
        apply (bool, optional): Applies the modifier to the object. Defaults to False.
    """
    weldModifier = object.modifiers.new(name="Weld", type='WELD')
    weldModifier.mode = 'CONNECTED'
    weldModifier.merge_threshold = merge_threshold
    weldModifier.vertex_group = vertex_group
    weldModifier.invert_vertex_group = invert_vertex_group

    if(apply):
        bpy.ops.object.modifier_apply(modifier="Decimator")

def blender_add_triangulate_modifier(object: bpy.types.Object, apply: bool = False) -> None:
    """Adds a triangulate modifier to an object.
    This modifier makes all faces into triangles (which isn't done by default in Blender)

    Args:
        object (bpy.types.Object): The target object
        apply (bool, optional): Applies the modifier to the object. Defaults to False.
    """
    object.modifiers.new(name="Triangulate", type='TRIANGULATE')

    if(apply):
        bpy.ops.object.modifier_apply(modifier="Triangulate")

def approximation_weld_threshold(vertices: np.ndarray, merge_radius: double = 3) -> double:
    """Empirical calculation of the weld threshold

    This thershold will merge together pixels that are close together
    This should only apply to pixels in the same plane, unless planes are very close together
    The distance between two neighbour vertices of the same plane is equal to the first vertex's x coordinate
    We multiply this value by 1.5 (> sqrt(2)) to allow merging of diagonal vertices
    We then multiply by merge_radius in order to merge vertices that are n spaces away

    As a safegard, we don't allow the thresold to be greater than the z distance between two nearby points
    A greater threshold might merge together different planes
    (even if the real distance is graeter than the distance along z, in practice with a higher thershold Blender merges vertices)
    
    Args:
        vertices (np.ndarray): The vertices of the target object
        merge_radius (double, optional): Maximum distance between merged vertices, in pixels of the source image. Defaults to 3.

    Returns:
        double: The computed thershold
    """
    
    # Ideal thershold, ignoring problems with the Z axis
    step_size = vertices[1][0]
    desired_threshold = 1.5*merge_radius*step_size

    # Reducing the thershold if necessary in order to avoid merging points along the Z axis
    sorted_z = sorted(set([z for _,_,z in vertices]))
    min_diff_z = min([sorted_z[i + 1] - sorted_z[i] for i in range(len(sorted_z)-1)])
    maximum_threshold = .99*min_diff_z
    
    return min([desired_threshold, maximum_threshold])


def blender_export(filepath: str, stl: bool = True, blend: bool = False) -> None:
    """Exports the Blender scene as a STL file and/or a BLEND file
    Modifiers will be applied during STL export

    Args:
        filepath (str): Path to the output files, without the extension
        stl (bool, optional): If true, generates a STL file. Defaults to True.
        blend (bool, optional): If true, generates a BLEND file. Defaults to False.
    """
    with suppress_stdout():
        if stl:
            bpy.ops.export_mesh.stl(filepath=generateNameResultingFile(filepath, "stl"), use_mesh_modifiers=True)
        if blend:
            bpy.ops.wm.save_as_mainfile(filepath=generateNameResultingFile(filepath, "blend"))

def blender_generate_stl(vertices: np.ndarray, faces: np.ndarray, parameters: MeshGenerationParameters, progress: Progress):
    """Generates and exports a Blender mesh from sets of vertices and faces
    Modifiers are added to this mesh, and will be applied during STL export

    Args:
        vertices (np.ndarray): Vertices of the mesh to generate
        faces (np.ndarray): Faces of the mesh to generate
        parameters(MeshGenerationParameters): Mesh generation parameters
        progress (Progress): Object used to notify the program when progress is made
    """
    
    progress.update_progress(0, "Creation of the blender object")
    blender_new_empty_scene()
    object = blender_new_object(vertices, faces)
    blender_select_object(object)
    blender_create_vertex_groups(object, vertices)
    
    progress.update_progress(10, "Adding the decimate modifier")
    blender_add_decimate_modifier(object, approximation_decimate_ratio(vertices), apply=False)
    
    progress.update_progress(20, "Adding the weld modifier")
    blender_add_weld_modifier(object, approximation_weld_threshold(vertices), vertex_group="Sides", invert_vertex_group=True, apply=False)
    
    progress.update_progress(30, "Adding the planar decimate modifier")
    blender_add_planar_decimate_modifier(object, angle_limit_deg=5, apply=False)
    
    progress.update_progress(40, "Adding the triangulate modifier")
    blender_add_triangulate_modifier(object, apply=False)
    
    progress.update_progress(50, "Exporting")
    blender_export(parameters.outputMeshPath, stl=parameters.saveSTL, blend=parameters.saveBlendFile)

#endregion

#region ############################## Output ##############################

@contextmanager
def suppress_stdout():
    """Suppresses stdout output for python and C code"""
    # /dev/null is used just to discard what is being printed
    with open(os.devnull, "w") as devnull:
        sys.stdout.flush() # <--- important when redirecting to files

        # Duplicate stdout (file descriptor 1) to a different file descriptor number
        newstdout = os.dup(1)

        # Duplicate the file descriptor for /dev/null and overwrite the value for stdout (file descriptor 1)
        os.dup2(devnull.fileno(), 1)

        # Use the original stdout to still be able to print to stdout within python
        sys.stdout = os.fdopen(newstdout, 'w')
    
        # This next line is the only one needed for python output
        with redirect_stdout(devnull):
            try:
                # The code inside the "with" block will be called here
                yield
            finally:
                # Restore the original stdout at the end
                os.dup2(newstdout, 1)

#endregion

#region ############################## Main method ##############################

def generateSTL(imagePath: str, parameters: MeshGenerationParameters, progress: Progress):
	"""
	Generate the mesh under the stl format.

	Args:
		imagePath(str): The path towards the depth map image
		parameters(MeshMandatoryParameters): The mandatory parameters to generate the mesh
        operatorsOpionalParameters(OperatorsOpionalParameters): Optional parameters for more fine tuning of the mesh generation 
        progress (Progress): Object used to notify the program when progress is made
	"""
	# ## Check if the result of the generation will be saved in at least one format, otherwise raise an exception
	if not(parameters.saveBlendFile or parameters.saveSTL):
		raise("No output format detected, doing nothing")
 
	progress.update_progress(0, "Generation of the base mesh")
	vertices, faces = generate_mesh(imagePath, parameters)
 
	progress.update_progress(50, "Applying modifiers and exporting")
	blender_generate_stl(vertices, faces, parameters, progress=progress.make_child(50,100))
 
	progress.update_progress(100, "Done")

#endregion