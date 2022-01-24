import math
import numpy as np
import cv2
import os
from tempfile import mkstemp
from color_types import ColorDefinition
from typing import List
from typing import Dict

def generateGreyScaleImage(imagePath, colors: List[ColorDefinition], pixelListLabels : List[int], labelsToColorIndices : Dict[int, int]):
    """Generates a grey scale image based on the results of the classification and the user parameters

    Args:
        imagePath (string): The path to the original image
        colors (List[colors]): The list of different colors that exist in the image and their parameters value
        pixelListLabels(List[int]): The list of the color labels the pixels of the image correspond to
        labelsToColorIndices(Dict[int, int]): The dictionnary that relates the labels to the indices of the colors list.
    Returns:
        outputImagePath(str): The path towards the grey scale image
        grayscaleImgReso(tuple(int, int, int)): The shape of the image (rows, columns, channels)
    """
        
    # ## Part 1 : computing the grey scale step to which correspond 1 unit of parameter value
    step = 0
    upperLimit = -100000
    lowerLimit = 1000000
    for c in colors:
        upperLimit = max(upperLimit, c.parameter)
        lowerLimit = min(lowerLimit, c.parameter)
    step = 255/(upperLimit - lowerLimit)

    # ## Part 2 : modifying the image
    # # Reads the image and converts to RGB
    img = cv2.cvtColor(cv2.imread(imagePath), cv2.COLOR_BGR2RGB)
    # # Flattened list of the pixel values
    pixel_list = np.reshape(img, [img.shape[0]*img.shape[1], 3])

    # # Change the RGB values to grayscale values
    for i in range(min(len(pixel_list), len(pixelListLabels))):
        greyScaleValue = math.floor(colors[labelsToColorIndices[pixelListLabels[i]]].parameter * step)
        pixel_list[i] = (greyScaleValue, greyScaleValue, greyScaleValue)
    
    # # Save the resulting image
    img_2 = np.reshape(pixel_list, img.shape).astype(np.uint8)
    grayscaleImgReso = img_2.shape
    img_2_bgr = cv2.cvtColor(img_2, cv2.COLOR_RGB2BGR)
    _, outputImagePath = mkstemp(suffix=".png")
    cv2.imwrite(outputImagePath, img_2_bgr)
    return outputImagePath, grayscaleImgReso