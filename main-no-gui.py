import sys
import threading
import time
from PIL import Image
from color_types import ColorType, ColorDefinition
from color_detection import findColorsAndMakeNewImage
from generate_greyscale_image import generateGreyScaleImage
from stl_generation import MeshMandatoryParameters, OperatorsOpionalParameters, generateSTL

def main(argv):
    filepath = argv[0]
    myMain = MainClass()
    myMain.open(filepath)

class MainClass():
    def __init__(self):
        self.colors = []
        self.colorTypeCB = {}
        self.colorParamSelect = {}
        self.pixel_list_labels = []
        self.relevant_label_to_color_hexes = {}
        self.image_width = 0
        self.image_width = 0
        self.max_height = 1000
        self.max_width = 1000
        self.minimum_step_btw_highest_lowest_points = 1.0 # The minimum step of height between the highest point of the object and the lowest point of the top surface.

    @staticmethod
    def callUpdateProgress(value, message=""):
        """Updates the status of the progress bar from a thread"""
        if value >= 100:
            message = "Done"
        if message != "":
            print(message)
        print(int(value), "%")
        
    def updateProgress(self, value, message=""):
        """Updates the status of the progress bar"""
        MainClass.callUpdateProgress(value, message)

    def open(self, filepath):
        try:
            # We try to open the file to check if it is accessible
            with open(filepath, 'r') as file:
                self.imagePath = filepath
                # The intensive stuff is done in a thread
                t=threading.Thread(target=self.onImageLoad)
                t.start()
        except IOError:
            print(f"Cannot open file '{filepath}'.")
            
    def onImageLoad(self):
        self.colors, self.flatImagePath, self.pixel_list_labels, self.relevant_label_to_color_hexes = findColorsAndMakeNewImage(self.imagePath, MainClass.callUpdateProgress)
        self.onGenerate()
    
    def onGenerate(self):
        """Behaviour of the 'generate' button"""
        # The intensive stuff is done in a thread
        threading.Thread(target=self.generate).start()
        
    def generate(self):
        """Generates the STL file. Runs in a thread."""
        saveBlendFile=True
        saveSTL=True
        
        img = Image.open(self.flatImagePath)
        dimensionXselect = 100
        dimensionYselect = int(dimensionXselect * img.height / img.width)
        
        dimensionZselect = 2 
        thicknessSelect = 2
        smoothingNbRepeats = 1
        smoothingFactor = .1
        smoothingBorder = 1
        decimateAngleLimit = 1

        if (not saveBlendFile and not saveSTL):
            print('Please, choose at least one file type to save')
        else:
            try:
                MainClass.callUpdateProgress(0, "Generating height map")
                colors = [ColorDefinition(color, ColorType.FLAT_SURFACE, i) for i, color in enumerate(self.colors)]
                grayscaleImagePath = generateGreyScaleImage(self.imagePath, colors, self.pixel_list_labels, self.relevant_label_to_color_hexes)
                desiredSize = (dimensionXselect, dimensionYselect, dimensionZselect)
                desiredThickness = thicknessSelect
                saveBlendFile=saveBlendFile
                saveSTL=saveSTL         
                meshMandatoryParams = MeshMandatoryParameters(self.imagePath, desiredSize=desiredSize, desiredThickness=desiredThickness, saveBlendFile=saveBlendFile, saveSTL=saveSTL)
                operatorsOpionalParameters = OperatorsOpionalParameters(smoothingNbRepeats = smoothingNbRepeats, smoothingFactor = smoothingFactor, smoothingBorder = smoothingBorder, decimateAngleLimit = decimateAngleLimit)
                MainClass.callUpdateProgress(50, "Generating STL file")
                startTime = time.time()
                stlUpdateProgress = lambda value, text : MainClass.callUpdateProgress(50+value/2, text)
                generateSTL(grayscaleImagePath, meshMandatoryParameters = meshMandatoryParams,operatorsOpionalParameters = operatorsOpionalParameters, fnUpdateProgress = stlUpdateProgress)
                endGenerationTime = time.time()
                MainClass.callUpdateProgress(100)
                message = 'STL generation successful ! Elapsed time : %.2f s' % (endGenerationTime - startTime)
                print(message)
            # TODO Better exception handling with specific exceptions
            except Exception as ex:
                MainClass.callUpdateProgress(0, "Unsuccessful")
                print('STL generation unsuccessful : '+str(ex))
                raise ex

if __name__ == '__main__':
    main(sys.argv[1:])