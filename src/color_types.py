class ColorDefinition:
    """Represents a color, and info on how it will be handled when generating a mesh"""
    def __init__(self, colorString: str, colorHeight: int) -> None:
        self.colorString = colorString
        self.colorHeight = colorHeight