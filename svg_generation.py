from enum import Enum, auto
from typing import List


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
        
        
def generateSVG(imagePath: str, colors: List[ColorDefinition]):
    # TODO add model generation
    pass