import sys
from img_to_stl import ImgToStl
from progress import ConsoleProgress

def main(argv):
    filepath = argv[0]
    img_to_stl = ImgToStl()
    progress = ConsoleProgress(max=100)
    img_to_stl.loadImageAndGenerateMesh(filepath, progress)

if __name__ == '__main__':
    main(sys.argv[1:])