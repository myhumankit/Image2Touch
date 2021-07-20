import bpy
from bpy import context
from mathutils import Vector

from reportlab.graphics import renderPM, renderPDF
from svglib.svglib import svg2rlg

 # Convert an svg image into a PNG image
def convertSVGtoPNG(svg_file, png_file, desiredResolution=(600,600)):
    drawing = svg2rlg(svg_file)
    scaleX = desiredResolution[0] / drawing.width;
    scaleY = desiredResolution[1] / drawing.height;
    drawing.scale(scaleX, scaleY)
    drawing.width *= scaleX
    drawing.height *= scaleY

    im =renderPM.drawToFile(drawing, png_file, fmt="PNG")
    return im


# Makes an empty scene
bpy.ops.wm.read_homefile(use_empty=True)


# Parameters that will come from a file for instance
imageSVGInPath = "D:/projets/data/MHK/testBlenderPNGtoOBJ/exemple-01.svg"
imagePNGPath = "D:/projets/data/MHK/testBlenderPNGtoOBJ/exemple-01.png"
desiredResolution = (500, 500); # Desired resolution of the svg transformed into png
numberOfPointsPerPixel = 2; #Number of mesh points per pixel
desiredSize = (100,100,10.); # Desired dimensions (x, y, zmax), in mm
desiredThickness = 0.05; # Desired thickness of the plane, in mm
displaceEccentricity = 16; #Maximum excentricity of the texture : higher values reduces blur / at oblique angles but is slower
smoothingNbRepeats = 10; # Number of times the smooth modifier is applied
smoothingFactor = 0.75; # Lambda factor of the smooth modifier
outputMesh = "D:/projets/data/MHK/testBlenderPNGtoOBJ/result_NbPoint=" + str(numberOfPointsPerPixel) + "_SmoothFactor=" + str(smoothingFactor).replace(".","_") + "SmoothRepeats=" + str(smoothingNbRepeats) + "_displaceEccentricity=" + str(displaceEccentricity) + ".stl";

# Convertion of the SVG file into PNG file
im = convertSVGtoPNG(imageSVGInPath, imagePNGPath, desiredResolution)

#Creation of the object
bpy.ops.mesh.primitive_grid_add(x_subdivisions=desiredResolution[0]*numberOfPointsPerPixel-1, y_subdivisions=desiredResolution[1]*numberOfPointsPerPixel-1, scale=(desiredSize[0],desiredSize[1],1));
grid = bpy.data.objects['Grid']
grid.name = 'Support Grid'

# Scaling the object
grid.scale = Vector((desiredSize[0]/2., desiredSize[1]/2.,desiredSize[2]))

#Creating the displace modifier
tex = bpy.data.textures.new("SourceImage", type = 'IMAGE')
tex.image = bpy.data.images.load(imagePNGPath)
tex.filter_eccentricity = displaceEccentricity;
tex.extension = "EXTEND"; # To avoid the repetition of the texture, creating unwanted borders

modifier = grid.modifiers.new(name="Displace", type='DISPLACE')
modifier.texture = bpy.data.textures['SourceImage']
modifier.strength = 1.;

# Creating the smoother modifier
smootherModifier = grid.modifiers.new(name="Smoother", type='SMOOTH')
smootherModifier.factor = smoothingFactor;
smootherModifier.iterations = smoothingNbRepeats;

# Creating the solidify modifier
solidifyModifier = grid.modifiers.new(name="Solidify", type='SOLIDIFY')
solidifyModifier.offset = 0.;
solidifyModifier.thickness = desiredThickness;

# Creating the smoother modifier
smootherModifier = grid.modifiers.new(name="PostProcessSmoother", type='SMOOTH')
smootherModifier.factor = smoothingFactor;
smootherModifier.iterations = smoothingNbRepeats;

#Exporting the mesh in stl format
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.export_mesh.stl(filepath=outputMesh)

