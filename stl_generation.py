from enum import Enum, auto
from typing import List
import os
import bpy
from bpy import context
from mathutils import Vector

class ColorType(Enum):
    """Represents different ways to handle color when generating a mesh"""
    FLAT_SURFACE = auto()
    TEXTURED = auto()
    BORDER = auto()
    
    def all():
        return [ColorType.FLAT_SURFACE, ColorType.TEXTURED, ColorType.BORDER]
        
    def __ref__(self):
        return self.__str__()
    
    def __str__(self):
        if self == ColorType.FLAT_SURFACE:
            return "Flat surface"
        elif self == ColorType.TEXTURED:
            return "Textured"
        elif self == ColorType.BORDER:
            return "Border"
        else:
            return "Error"


class ColorDefinition:
    """Represents a color, and info on how it will be handled when generating a mesh"""
    def __init__(self, colorString: str, colorType: ColorType, parameter: int) -> None:
        self.colorString = colorString
        self.colorType = colorType
        self.parameter = parameter
        
        
def generateSTL(imagePath: str, colors: List[ColorDefinition]):
    # TODO add model generation
    ## Makes an empty scene
    bpy.ops.wm.read_homefile(use_empty=True)

    desiredResolution = (500, 500); # Desired resolution of the svg transformed into png
    numberOfPointsPerPixel = 2; #Number of mesh points per pixel
    desiredSize = (100,100,10.); # Desired dimensions (x, y, zmax), in mm
    desiredThickness = 0.05; # Desired thickness of the plane, in mm
    displaceEccentricity = 16; #Maximum excentricity of the texture : higher values reduces blur / at oblique angles but is slower
    smoothingNbRepeats = 10; # Number of times the smooth modifier is applied
    smoothingFactor = 0.75; # Lambda factor of the smooth modifier
    outputMesh = os.path.splitext(imagePath)[0] + ".stl"

    ## Creation of the object
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=desiredResolution[0]*numberOfPointsPerPixel-1, y_subdivisions=desiredResolution[1]*numberOfPointsPerPixel-1)
    grid = bpy.data.objects['Grid']
    grid.name = 'Support Grid'

    ## Scaling the object
    grid.scale = Vector((desiredSize[0]/2., desiredSize[1]/2.,desiredSize[2]))

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
    solidifyModifier.thickness = desiredThickness

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