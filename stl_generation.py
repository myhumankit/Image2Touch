from typing import List, Tuple
import os
import bpy
from bpy import context
from numpy import double
from mathutils import Vector
       

class MeshMandatoryParameters:
    """Represents the different mandatory parameters to generate a mesh"""
    def __init__(self, outputMeshPath:str, imageResolution: Tuple[int, int, int], numberOfPointsPerPixel: int = 2, desiredSize: Tuple[double, double, double] = (100., 100., 10.), desiredThickness: double = 0.05) -> None:
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
        

def generateSTL(imagePath: str, meshMandatoryParameters: MeshMandatoryParameters):
    """
    Generate the mesh under the stl format.

    Args:
        imagePath(str): The path towards the depth map image
        meshMandatoryParameters(MeshMandatoryParameters): The mandatory parameters to generate the mesh
    """
    ## Makes an empty scene
    bpy.ops.wm.read_homefile(use_empty=True)
   
    displaceEccentricity = 16; #Maximum excentricity of the texture : higher values reduces blur / at oblique angles but is slower
    smoothingNbRepeats = 10; # Number of times the smooth modifier is applied
    smoothingFactor = 0.75; # Lambda factor of the smooth modifier
    outputMesh = ""
    if (os.path.isdir(meshMandatoryParameters.outputMeshPath)):
        # Create a name for the output mesh
        outputMesh = os.path.join(meshMandatoryParameters.outputMeshPath, "result.stl")
    else:
        outputMesh = os.path.splitext(meshMandatoryParameters.outputMeshPath)[0] + "-resultingMesh.stl"

    ## Creation of the object
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=meshMandatoryParameters.imageResolution[1]*meshMandatoryParameters.numberOfPointsPerPixel-1, y_subdivisions=meshMandatoryParameters.imageResolution[0]*meshMandatoryParameters.numberOfPointsPerPixel-1)
    grid = bpy.data.objects['Grid']
    grid.name = 'Support Grid'

    ## Scaling the object
    grid.scale = Vector((meshMandatoryParameters.desiredSize[0]/2., meshMandatoryParameters.desiredSize[1]/2.,meshMandatoryParameters.desiredSize[2]))

    ## Creating the displace modifier
    tex = bpy.data.textures.new("SourceImage", type = 'IMAGE')
    tex.image = bpy.data.images.load(imagePath)
    tex.filter_eccentricity = displaceEccentricity
    tex.extension = "EXTEND"; # To avoid the repetition of the texture, creating unwanted borders

    modifier = grid.modifiers.new(name="Displace", type='DISPLACE')
    modifier.texture = bpy.data.textures['SourceImage']
    modifier.strength = 1.

    ## Creating the smoother modifier
    smootherModifier = grid.modifiers.new(name="Smoother", type='SMOOTH')
    smootherModifier.factor = smoothingFactor
    smootherModifier.iterations = smoothingNbRepeats

    ## Creating the solidify modifier
    solidifyModifier = grid.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidifyModifier.offset = 0.
    solidifyModifier.thickness = meshMandatoryParameters.desiredThickness

    ## Creating the smoother modifier
    smootherModifier = grid.modifiers.new(name="PostProcessSmoother", type='SMOOTH')
    smootherModifier.factor = smoothingFactor
    smootherModifier.iterations = smoothingNbRepeats

    ## Creating the triangulating modifier
    triangulateModifier = grid.modifiers.new(name="Triangulator", type='TRIANGULATE')

    ## Creating the decimating modifier
    decimateModifier = grid.modifiers.new(name="Decimator", type='DECIMATE')
    decimateModifier.ratio = 0.1; # Divide the number of faces by 10.
    #decimateModifier.decimate_type = "DISSOLVE"
    #decimateModifier.iterations = smoothingNbRepeats;

    ## Exporting the mesh in stl format
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.export_mesh.stl(filepath=outputMesh)
    pass