import wx
from color_detection import findColorsAndMakeNewImage
from stl_generation import ColorType, ColorDefinition, generateSTL
import os

class MainWindow(wx.Frame):
    """The main window of the application"""
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title)
        
        self.colors = []
        self.colorTypeCB = {}
        self.colorParamSelect = {}

        self.initUI()
        self.Centre()


    def initUI(self):
        """Builds and displays all the UI elements of the window"""
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(3, 4)

        self.panel = panel
        self.sizer = sizer
        
        self.imagePathText = wx.StaticText(panel, label="Select a file")
        sizer.Add(self.imagePathText, pos=(0, 0))
        
        buttonOpen = wx.Button(panel, label="...", size=(90, 28))
        buttonOpen.Bind(wx.EVT_BUTTON,self.onOpen)
        sizer.Add(buttonOpen, pos=(0, 1))
        
        self.colorSizer = wx.FlexGridSizer(cols=4, vgap=2, hgap=5)
        sizer.Add(self.colorSizer, pos=(1, 0), span=(1,2), flag=wx.EXPAND)
        
        buttonGenerate = wx.Button(panel, label="Generate", size=(90, 28))
        buttonGenerate.Bind(wx.EVT_BUTTON,self.onGenerate)
        sizer.Add(buttonGenerate, pos=(2, 0), span=(1,2), flag=wx.EXPAND)
        
        self.PhotoMaxSize = 100
        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, 
                                         wx.BitmapFromImage(wx.EmptyImage(self.PhotoMaxSize,self.PhotoMaxSize)))
        sizer.Add(self.imageCtrl, pos=(0, 3), span=(4,1), flag=wx.EXPAND)
        
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)
        
        panel.SetSizer(sizer)
        sizer.Fit(self)
        
        
    def refresh(self):
        """Refreshes the layout of the window (this needs to happen if elements change size)"""
        self.panel.Refresh()
        self.sizer.Fit(self)
        
        
    def onOpen(self, event):
        """Behaviour for the '...' button. An image file can be selected for processing"""
        with wx.FileDialog(self, "Load an image file to process", wildcard="Image files (*.bmp;*.gif;*.png) |*.bmp;*.gif;*.png",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            try:
                # We try to open the file to check if it is accessible
                with open(pathname, 'r') as file:
                    self.imagePath = pathname
                self.onImageLoad()
            except IOError:
                wx.LogError(f"Cannot open file '{pathname}'.")
        
    
    def setImage(self, imageCtrl, imagePath):
        # scale the image, preserving the aspect ratio
        img = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
        W = img.GetWidth()
        H = img.GetHeight()
        if W > H:
            NewW = self.PhotoMaxSize
            NewH = self.PhotoMaxSize * H / W
        else:
            NewH = self.PhotoMaxSize
            NewW = self.PhotoMaxSize * W / H
        img = img.Scale(NewW,NewH)
        # Update the image preview
        imageCtrl.SetBitmap(wx.BitmapFromImage(img))
    
    def onImageLoad(self):
        """Behaviour for loading an image to be processed"""
        # Update the text containing the path
        self.imagePathText.SetLabel(os.path.basename(self.imagePath))
        # Original image preview
        #self.setImage(self.imageCtrl, self.imagePath)
        
        # Find the colors in the image
        self.colors, self.flatImagePath = findColorsAndMakeNewImage(self.imagePath)
        # Flattened image preview
        self.setImage(self.imageCtrl, self.flatImagePath)
        
        # MAJ UI
        self.refresh()
        
        # Triggers the appearance of the color UI
        self.onColorsChanged()
        
    
    def makeCB(self, color):
        """Makes a combobox (dropdown) for selecting a ColorType"""
        cb = wx.ComboBox(self.panel)
        for obj in ColorType.all():
            cb.Append(obj.__str__(), obj)
        cb.SetSelection(0)
        # TODO handle selection
        #cb.Bind(wx.EVT_COMBOBOX, self.onSelect)
        self.colorTypeCB[color] = cb
        return cb
    
    
    def makeColorSquare(self, color):
        """Makes a color square with the given color"""
        square = wx.StaticText(self.panel, label=" ")
        square.SetMinSize((25, 25))
        square.SetBackgroundColour(color)
        return square


    def makeParameterSelect(self, color):
        """Makes a field for selecting the color processing parameter"""
        select = wx.SpinCtrl(self.panel, min=0, max=100, initial=0)
        self.colorParamSelect[color] = select
        return select
    
    
    def onColorsChanged(self):
        """Behaviour for when the detected colors of the image have changed"""
        # Clears previous content
        self.colorTypeCB = {}
        self.colorParamSelect = {}
        self.colorSizer.Clear(True)
        self.refresh()
        # Adds new content
        content = [(wx.StaticText(self.panel, label=x, style=wx.ALIGN_CENTRE_HORIZONTAL)) for x in [" ","Color","Type","Parameter"]] # Headers
        content = content + [y for color in self.colors for y in [
            self.makeColorSquare(color=color),
            wx.StaticText(self.panel, label=color),
            self.makeCB(color),
            self.makeParameterSelect(color)]] # Values
        self.colorSizer.AddMany(content)
        # MAJ UI
        self.refresh()
        
    
    def getColorType(self, color: str) -> ColorType:
        """Finds the ColorType selected for a given color"""
        cb = self.colorTypeCB[color]
        return cb.GetClientData(cb.GetSelection())
        
    
    def getParameter(self, color: str) -> int:
        """Finds the parameter selected for a given color"""
        select = self.colorParamSelect[color]
        return select.GetValue()
        
        
    def onGenerate(self, event):
        """Behaviour of the 'generate' button"""
        try:
            colors = [ColorDefinition(color, self.getColorType(color), self.getParameter(color)) for color in self.colors]
            generateSTL(self.imagePath, colors)
            wx.MessageBox('STL generation successful !', 'Info', wx.OK)
        # TODO Better exception handling with specific exceptions
        except Exception: 
            wx.MessageBox('STL generation unsuccessful !', 'Error', wx.OK | wx.ICON_ERROR)