import wx
from ihm import MainWindow

def main():

    app = wx.App()
    ex = MainWindow(None, title='STL Generator')
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()