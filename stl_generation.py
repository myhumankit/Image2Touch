from typing import List, Tuple
import os
import bpy
import bmesh
from numpy import double
from mathutils import Vector
       
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

	# ## Makes an empty scene
	for object in bpy.data.objects:
		if not(object.name == "Cube" or object.name == "Support"):
			bpy.data.objects.remove(object, do_unlink=True)
	for tex in bpy.data.textures:
		bpy.data.textures.remove(tex, do_unlink=True)
	  
	displaceEccentricity = operatorsOpionalParameters.displaceEccentricity #Maximum excentricity of the texture : higher values reduces blur / at oblique angles but is slower
	displaceStrength = 2. * (1. - meshMandatoryParameters.desiredThickness / meshMandatoryParameters.desiredSize[2]) #Amount to displace the geometry : 1. induces that a black color is equal to one half the height of the object so strength = 2. *(1-thickness/height)
	smoothingNbRepeats = operatorsOpionalParameters.smoothingNbRepeats # Number of times the smooth modifier is applied
	smoothingFactor = operatorsOpionalParameters.smoothingFactor # Lambda factor of the smooth modifier
	smoothingBorder = operatorsOpionalParameters.smoothingBorder # Lambda factor in border
	decimateAngleLimit = operatorsOpionalParameters.decimateAngleLimit # Maximum angle allowed, expressed in radians because it is the unit of Blender
	outputMesh = generateNameResultingFile(meshMandatoryParameters.outputMeshPath, "stl")
	outputBlenderScene = generateNameResultingFile(meshMandatoryParameters.outputMeshPath, "blend")

	# ## Removing potential old vertex groups / modifiers of the support
	support = bpy.data.objects[0]
	for v_group in support.vertex_groups:
		support.vertex_groups.remove(v_group)

	for modifier in support.modifiers:
		support.modifiers.remove(modifier)
	
	# ## Subdividing the upper face until reaching the desired resolution
	nbIter = 0
	meshReso = meshMandatoryParameters.desiredSize[0] * meshMandatoryParameters.desiredSize[1] * meshMandatoryParameters.numberOfPointsPerPixel
	while len(support.data.vertices) < meshReso and nbIter <100:
		nbIter = nbIter + 1
		me = support.data
		# object mode bmesh
		bm = bmesh.new()
		bm.from_mesh(me)
		faces = [f for f in bm.faces if f.calc_center_median()[2] >= 1.]
		edges = set(e for f in faces for e in f.edges)

		bmesh.ops.subdivide_edges(bm,
			edges=list(edges),
			cuts=1,
			use_grid_fill=True,
			)
		bm.to_mesh(me) 
		me.update()
	
	# ## Creating the vertex groups
	upperface_vertex_group = support.vertex_groups.new(name='UpperFaceGroup')
	upperface_group_data = [v.index for v in support.data.vertices if v.co[2] >=1.]
	upperface_vertex_group.add(upperface_group_data, 1.0, 'ADD')

	innerupperface_vertex_group = support.vertex_groups.new(name='InnerUpperFaceGroup')
	innerupperface_group_data = [v.index for v in support.data.vertices if (v.co[2] >=1. and abs(v.co[0]) < 1. and abs(v.co[1]) <1.)]
	innerupperface_vertex_group.add(innerupperface_group_data, 1.0, 'ADD')
	
	# ## Scaling the object
	support.scale = Vector((meshMandatoryParameters.desiredSize[0]/2., meshMandatoryParameters.desiredSize[1]/2.,meshMandatoryParameters.desiredSize[2]/2.))

	# ## Creating the displace modifier
	fnUpdateProgress(25, "Applying the depth map")
	tex = bpy.data.textures.new("SourceImage", type = 'IMAGE')
	tex.image = bpy.data.images.load(imagePath)
	tex.filter_eccentricity = displaceEccentricity
	tex.extension = "EXTEND"; # To avoid the repetition of the texture, creating unwanted borders

	modifier = support.modifiers.new(name="Displace", type='DISPLACE')
	modifier.texture = bpy.data.textures['SourceImage']
	modifier.vertex_group = 'UpperFaceGroup'
	modifier.direction = "Z"
	modifier.strength = displaceStrength
	modifier.mid_level = 1. #Ensure that the final thickness of the object respects the user choice

	# ## Creating the smoother modifier
	fnUpdateProgress(50, "Smoothing the resulting mesh")
	smootherModifier = support.modifiers.new(name="Smoother", type='LAPLACIANSMOOTH')
	smootherModifier.use_x = True
	smootherModifier.use_y = True
	smootherModifier.use_z = False
	smootherModifier.lambda_factor = smoothingFactor
	smootherModifier.lambda_border = smoothingBorder
	smootherModifier.iterations = smoothingNbRepeats
	smootherModifier.vertex_group = 'InnerUpperFaceGroup'
	smootherModifier.use_volume_preserve = True
	smootherModifier.use_normalized = True

	# ## Creating the decimating modifier
	fnUpdateProgress(75, "Removing useless vertices")
	decimateModifier = support.modifiers.new(name="Decimator", type='DECIMATE')
	decimateModifier.decimate_type = "DISSOLVE" 
	decimateModifier.angle_limit = decimateAngleLimit

	# # Create the triangulate modifier
	triangulateModifier = support.modifiers.new(name="Triangulator", type='TRIANGULATE')

	## Exporting the mesh in stl format
	fnUpdateProgress(90, "Exporting the mesh")
	if meshMandatoryParameters.saveSTL:
		bpy.ops.export_mesh.stl(filepath=outputMesh)
	
	if meshMandatoryParameters.saveBlendFile:
		bpy.ops.wm.save_as_mainfile(filepath=outputBlenderScene)
	pass