import argparse
from set_env import set_blender_env

def main():
    args = parseArgs()
    if args.silent:
        main_no_gui(args)
    else:
        main_gui(args)
    
def main_gui(args):
    # If the blender scripts are newt to the exe file, uses them
    # Useful for the exe version, making it truly portable
    with set_blender_env():
        import wx
        # This imports bpy, and thus needs to happen after set_blender_env
        from ihm import MainWindow
        
        app = wx.App()
        ex = MainWindow(None, title='Image2Touch')
        ex.Show()
        app.MainLoop()

def main_no_gui(args):
    with set_blender_env():
        from progress import ConsoleProgress
        # This imports bpy, and thus needs to happen after set_blender_env
        from img_to_stl import ImgToStl
        
        filepath = args.file
        img_to_stl = ImgToStl()
        progress = ConsoleProgress(max=100)
        img_to_stl.loadImageAndGenerateMesh(filepath, progress)

def parseArgs():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-f", "--file", help="Path to the image file to convert")
    argParser.add_argument("-s", "--silent", "--no-gui", action='store_true', help="Launch the program in console only mode")
    return argParser.parse_args()

if __name__ == '__main__':
    main()