import wx
from set_env import set_blender_env

def main():
    # If the blender scripts are newt to the exe file, uses them
    # Useful for the exe version, making it truly portable
    with set_blender_env():
        # This imports bpy, and thus needs to happen after set_blender_env
        from ihm import MainWindow
        
        app = wx.App()
        ex = MainWindow(None, title='STL Generator')
        ex.Show()
        app.MainLoop()


if __name__ == '__main__':
    main()