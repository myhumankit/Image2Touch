import threading
import time
from PIL import Image
from color_types import ColorDefinition
from color_detection import findColorsAndMakeNewImage
from generate_greyscale_image import generateGreyScaleImage
from stl_generation import MeshMandatoryParameters, OperatorsOpionalParameters, generateSTL
from dataclasses import dataclass, field
from typing import List
from progress import Progress

@dataclass(repr=False, eq=False)
class ImgToStl:
    imagePath: str = None
    flatImagePath: str = None
    
    colors: List[str] = field(default_factory=list) 
    colors_definitions: List[ColorDefinition] = field(default_factory=list) 
    pixel_list_labels: List[int] = field(default_factory=list) 
    relevant_label_to_color_hexes: dict = field(default_factory=dict) 
    
    saveSTL: bool = True
    saveBlendFile: bool = True
    
    preserveAspectRatio: bool = True
    dimensionXselect: int = 100
    dimensionYselect: int = 100
    dimensionZselect: int = 2 
    desiredThickness: int = 2
    
    smoothingNbRepeats = 1
    smoothingFactor = .1
    smoothingBorder = 1
    decimateAngleLimit = 1

    def loadImage(self, filepath: str, progress: Progress):
        # The intensive stuff is done in a thread
        threading.Thread(target=self.loadImageSync, args=[filepath, progress]).start()
    
    def generateMesh(self, progress: Progress):
        """Behaviour of the 'generate' button"""
        # The intensive stuff is done in a thread
        threading.Thread(target=self.generateMeshSync, args=[progress]).start()
        
    def loadImageAndGenerateMesh(self, filepath: str, progress: Progress):
        threading.Thread(target=lambda f, p : self.loadImageSync(f, p.make_child(0,50)) and self.generateMeshSync(p.make_child(50,100)), 
                         args=[filepath, progress]).start()
            
    def loadImageSync(self, filepath, progress: Progress):
        try:
            # We try to open the file to check if it is accessible
            with open(filepath, 'r') as file:
                self.imagePath = filepath
                self.colors, self.flatImagePath, self.pixel_list_labels, self.relevant_label_to_color_hexes = findColorsAndMakeNewImage(self.imagePath, progress.update_progress)
                return True
        except IOError:
            progress.fatal_error(f"Cannot open file '{filepath}'.")
            return False
        
    def generateMeshSync(self, progress: Progress):
        """Generates the STL file. Runs in a thread."""
        
        if (self.preserveAspectRatio): 
            img = Image.open(self.flatImagePath)
            self.dimensionYselect = int(self.dimensionXselect * img.height / img.width)
        
        if (not self.saveBlendFile and not self.saveSTL):
            print('Please, choose at least one file type to save')
            return False
        
        try:
            progress.update_progress(0, "Generating height map")
            if self.colors_definitions is None or len(self.colors_definitions) == 0:
                self.colors_definitions = [ColorDefinition(color, i) for i, color in enumerate(self.colors)]
            grayscaleImagePath = generateGreyScaleImage(self.imagePath, self.colors_definitions, self.pixel_list_labels, self.relevant_label_to_color_hexes)
            
            desiredSize = (self.dimensionXselect, self.dimensionYselect, self.dimensionZselect)
            meshMandatoryParams = MeshMandatoryParameters(self.imagePath, desiredSize=desiredSize, desiredThickness=self.desiredThickness, saveBlendFile=self.saveBlendFile, saveSTL=self.saveSTL)
            operatorsOpionalParameters = OperatorsOpionalParameters(smoothingNbRepeats = self.smoothingNbRepeats, smoothingFactor = self.smoothingFactor, smoothingBorder = self.smoothingBorder, decimateAngleLimit = self.decimateAngleLimit)
            
            progress.update_progress(50, "Generating STL file")
            startTime = time.time()
            generateSTL(grayscaleImagePath, meshMandatoryParameters = meshMandatoryParams,operatorsOpionalParameters = operatorsOpionalParameters, progress = progress.make_child(50,100))
            endGenerationTime = time.time()
            
            message = 'STL generation successful ! Elapsed time : %.2f s' % (endGenerationTime - startTime)
            progress.update_progress(100, message)
            return True
            
        # TODO Better exception handling with specific exceptions
        except Exception as ex:
            progress.fatal_error(message=f'STL generation unsuccessful : {str(ex)}', exception=ex)
            return False
