from typing import List, Tuple
import os
import bpy
import bmesh
from numpy import double
from mathutils import Vector
       
class MeshMandatoryParameters:
	"""Represents the different mandatory parameters to generate a mesh"""
	def __init__(self, outputMeshPath:str, imageResolution: Tuple[int, int, int], numberOfPointsPerPixel: int = 8, desiredSize: Tuple[double, double, double] = (100., 100., 10.), desiredThickness: double = 0.05) -> None:
		"""Constructor of the MeshMandatoryParameters.

		Args:
			outputMeshPath(str): The path towards the output mesh
			imageResolution(int, int, int): The resoluion of the depth map
			numberOfPointsPerPixel (int): The number of mesh points that are mapped to one pixel of the source image
			desiredSize (tuple(double, double, double)): The desired dimensions (x, y, zmax), expressed in mm
			desiredThickness(double): The desired thickness of the plane, in mm
		"""
		self.outputMeshPath = outputMeshPath
		self.imageResolution = imageResolution
		self.numberOfPointsPerPixel = numberOfPointsPerPixel
		self.desiredSize = desiredSize
		self.desiredThickness = desiredThickness
		

def generateSTL(imagePath: str, meshMandatoryParameters: MeshMandatoryParameters, fnUpdateProgress):
	"""
	Generate the mesh under the stl format.

	Args:
		imagePath(str): The path towards the depth map image
		meshMandatoryParameters(MeshMandatoryParameters): The mandatory parameters to generate the mesh
	"""
	# ## Makes an empty scene
	for object in bpy.data.objects:
		if not(object.name == "Cube" or object.name == "Support"):
			bpy.data.objects.remove(object, do_unlink=True)
	for tex in bpy.data.textures:
		bpy.data.textures.remove(tex, do_unlink=True)
	  
	displaceEccentricity = 16; #Maximum excentricity of the texture : higher values reduces blur / at oblique angles but is slower
	displaceStrength = 1.; #Amount to displace the geometry
	smoothingNbRepeats = 5.; # Number of times the smooth modifier is applied
	smoothingFactor = 1.; # Lambda factor of the smooth modifier
	smoothingBorder = 0. # Lambda factor in border
	decimateAngleLimit = 0.1 # Maximum angle allowed, expressed in radians because it is the unit of Blender
	outputMesh = ""
	if (os.path.isdir(meshMandatoryParameters.outputMeshPath)):
		# Create a name for the output mesh
		outputMesh = os.path.join(meshMandatoryParameters.outputMeshPath, "result.stl")
	else:
		outputMesh = os.path.splitext(meshMandatoryParameters.outputMeshPath)[0] + "-resultingMesh.stl"

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
	support.scale = Vector((meshMandatoryParameters.desiredSize[0]/2., meshMandatoryParameters.desiredSize[1]/2.,meshMandatoryParameters.desiredSize[2]))

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
	bpy.ops.export_mesh.stl(filepath=outputMesh)
	pass