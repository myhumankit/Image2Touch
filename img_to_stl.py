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
    """
    This class defines the behaviour of the program, independent of whether the GUI is used or not
    """
    
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
        """Asynchronous preprocessing of a source image
        At the end of this step, a new image will be generated, using only flat colouring
        This is necessary to reduce the amount of slightly different colors that might be in the image
        Without it, we would risk making the height selection for each color impractical

        Args:
            filepath (str): Path to the image to process
            progress (Progress): Object used to notify the program when progress is made
        """
        # loadImageSync is called in a separate thread
        threading.Thread(target=self.loadImageSync, args=[filepath, progress]).start()
    
    def generateMesh(self, progress: Progress):
        """Asynchronous Generation of a mesh from a preprocessed image
        (Behaviour of the 'generate' button)
        Note that the image must have been preprocessed before we get to this step
        
        Args:
            progress (Progress): Object used to notify the program when progress is made
        """
        # generateMeshSync is called in a separate thread
        threading.Thread(target=self.generateMeshSync, args=[progress]).start()
        
    def loadImageAndGenerateMesh(self, filepath: str, progress: Progress):
        """Asynchronous Preprocessing and conversion of a source image
        This is the equivalent of calling loadImage, waiting for it to finish and then calling generateMesh

        Args:
            filepath (str): Path to the image to process
            progress (Progress): Object used to notify the program when progress is made
        """
        # loadImageSync and generateMeshSync are called in a separate thread
        threading.Thread(target=lambda f, p : self.loadImageSync(f, p.make_child(0,50)) and self.generateMeshSync(p.make_child(50,100)), 
                         args=[filepath, progress]).start()
            
    def loadImageSync(self, filepath, progress: Progress) -> bool:
        """Synchronous version of loadImage

        Args:
            filepath (str): Path to the image to process
            progress (Progress): Object used to notify the program when progress is made
            
        Returns:
            true if the operation is successful
        """
        try:
            # We try to open the file to check if it is accessible
            with open(filepath, 'r') as file:
                # We save the path to the current file for context
                self.imagePath = filepath
                # Preprocessing of the image
                self.colors, self.flatImagePath, self.pixel_list_labels, self.relevant_label_to_color_hexes = findColorsAndMakeNewImage(self.imagePath, progress)
                return True
        except IOError:
            # Error during preprocessing
            progress.fatal_error(f"Cannot open file '{filepath}'.")
            return False
        
    def generateMeshSync(self, progress: Progress) -> bool:
        """Synchronous version of generateMesh

        Args:
            progress (Progress): Object used to notify the program when progress is made
            
        Returns:
            true if the operation is successful
        """
        
        # If no output was selected, it is useless to continue
        if (not self.saveBlendFile and not self.saveSTL):
            print('Please, choose at least one file type to save')
            return False
        
        # We make sure to preserve the aspect ratio if needed
        if (self.preserveAspectRatio): 
            img = Image.open(self.flatImagePath)
            self.dimensionYselect = int(self.dimensionXselect * img.height / img.width)
        
        try:
            # Generation of the grayscale version of the image, which will be used as a height map
            progress.update_progress(0, "Generating height map")
            if self.colors_definitions is None or len(self.colors_definitions) == 0:
                self.colors_definitions = [ColorDefinition(color, i) for i, color in enumerate(self.colors)]
            grayscaleImagePath = generateGreyScaleImage(self.imagePath, self.colors_definitions, self.pixel_list_labels, self.relevant_label_to_color_hexes)
            
            # Gathering the parameters
            desiredSize = (self.dimensionXselect, self.dimensionYselect, self.dimensionZselect)
            meshMandatoryParams = MeshMandatoryParameters(self.imagePath, desiredSize=desiredSize, desiredThickness=self.desiredThickness, saveBlendFile=self.saveBlendFile, saveSTL=self.saveSTL)
            operatorsOpionalParameters = OperatorsOpionalParameters(smoothingNbRepeats = self.smoothingNbRepeats, smoothingFactor = self.smoothingFactor, smoothingBorder = self.smoothingBorder, decimateAngleLimit = self.decimateAngleLimit)
            
            # Generating the mesh
            progress.update_progress(50, "Generating STL file")
            startTime = time.time()
            generateSTL(grayscaleImagePath, meshMandatoryParameters = meshMandatoryParams,operatorsOpionalParameters = operatorsOpionalParameters, progress = progress.make_child(50,100))
            endGenerationTime = time.time()
            
            # Generation successful
            message = 'STL generation successful ! Elapsed time : %.2f s' % (endGenerationTime - startTime)
            progress.update_progress(100, message)
            return True
            
        # TODO Better exception handling with specific exceptions
        except Exception as ex:
            # Generation failed
            progress.fatal_error(message=f'STL generation unsuccessful : {str(ex)}', exception=ex)
            return False
