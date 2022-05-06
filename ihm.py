import wx
import wx.lib.agw.floatspin as floatspin
from pubsub import pub
import threading
from color_detection import findColorsAndMakeNewImage
from generate_greyscale_image import generateGreyScaleImage
from color_types import ColorType, ColorDefinition
from stl_generation import MeshMandatoryParameters, generateSTL
import os

class MainWindow(wx.Frame):
    """The main window of the application"""
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title)
        
        self.colors = []
        self.colorTypeCB = {}
        self.colorParamSelect = {}
        self.pixel_list_labels = []
        self.relevant_label_to_color_hexes = {}
        self.img_width = 0
        self.img_height = 0
        self.max_height = 1000
        self.max_width = 1000

        self.initUI()
        self.Centre()


    def initUI(self):
        """Builds and displays all the UI elements of the window"""
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(3, 6)

        self.panel = panel
        self.sizer = sizer
        
        self.imagePathText = wx.StaticText(panel, label="No file selected")
        sizer.Add(self.imagePathText, pos=(0, 0))
        
        self.buttonOpen = wx.Button(panel, label="Select a &file...", size=(90, 28))
        self.buttonOpen.Bind(wx.EVT_BUTTON,self.onOpen)
        sizer.Add(self.buttonOpen, pos=(0, 1))
        
        self.colorSizer = wx.FlexGridSizer(cols=4, vgap=2, hgap=5)
        sizer.Add(self.colorSizer, pos=(1, 0), span=(1,2), flag=wx.EXPAND)
        
        self.dimensionSizer = wx.GridBagSizer(3,4)
        dimensionMainHeader = wx.StaticText(panel, label="Dimensions (mm) :")
        dimensionXHeader = wx.StaticText(panel, label="Length ")
        dimensionYHeader = wx.StaticText(panel, label="Width ")
        dimensionZHeader = wx.StaticText(panel, label="Height ")
        thicknessHeader = wx.StaticText(panel, label="Thickness ")
        self.dimensionXselect = wx.SpinCtrl(self.panel, min=10, max=self.max_width, initial=100)
        self.dimensionYselect = wx.SpinCtrl(self.panel, min=10, max=self.max_height, initial=100)
        self.dimensionZselect = wx.SpinCtrl(self.panel, min=1, max=100, initial=10)
        self.dimensionXselect.Bind(wx.EVT_SPINCTRL,self.onDimensionXChanged)
        self.dimensionYselect.Bind(wx.EVT_SPINCTRL,self.onDimensionYChanged)
        self.thicknessSelect = floatspin.FloatSpin(self.panel, min_val=0.5, max_val=100, increment=0.1, value=0.5)
        self.thicknessSelect.SetFormat("%f")
        self.thicknessSelect.SetDigits(1)
        self.dimensionSizer.Add(dimensionMainHeader, pos=(0, 0), span=(1,4))
        self.dimensionSizer.Add(dimensionXHeader, pos=(1, 0))
        self.dimensionSizer.Add(dimensionYHeader, pos=(1, 1))
        self.dimensionSizer.Add(dimensionZHeader, pos=(1, 2))
        self.dimensionSizer.Add(thicknessHeader, pos=(1, 3))
        self.dimensionSizer.Add(self.dimensionXselect, pos=(2, 0))
        self.dimensionSizer.Add(self.dimensionYselect, pos=(2, 1))
        self.dimensionSizer.Add(self.dimensionZselect, pos=(2, 2))
        self.dimensionSizer.Add(self.thicknessSelect, pos=(2, 3))
        sizer.Add(self.dimensionSizer, pos=(2, 0), span=(1,2))
        
        self.buttonGenerate = wx.Button(panel, label="&Generate", size=(90, 28))
        self.buttonGenerate.Bind(wx.EVT_BUTTON,self.onGenerate)
        sizer.Add(self.buttonGenerate, pos=(3, 0), span=(1,2), flag=wx.EXPAND)
        self.buttonGenerate.Disable() # This button is disabled at first and enabled when an image loads
        
        self.gaugeText = wx.StaticText(panel, label="Idle")
        sizer.Add(self.gaugeText, pos=(4, 0))
        
        self.gauge = wx.Gauge(panel, range=100)
        sizer.Add(self.gauge, pos=(5,0), span=(1,2), flag=wx.EXPAND)
        
        self.PhotoMaxSize = 100
        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, 
                                         wx.BitmapFromImage(wx.EmptyImage(self.PhotoMaxSize,self.PhotoMaxSize)))
        sizer.Add(self.imageCtrl, pos=(0, 3), span=(5,1), flag=wx.EXPAND)
        
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)
        
        panel.SetSizer(sizer)
        sizer.Fit(self)
        
        # Respond to the update event
        pub.subscribe(self.updateProgress, "update")
        
        
    def disableButtons(self):
        """Disables all buttons to prevent interaction during other work"""
        self.buttonOpen.Disable()
        self.buttonGenerate.Disable()
        
    def enableButtons(self):
        """Disables all buttons to prevent interaction during other work"""
        self.buttonOpen.Enable()
        self.buttonGenerate.Enable()
        
    def refresh(self):
        """Refreshes the layout of the window (this needs to happen if elements change size)"""
        self.panel.Refresh()
        self.sizer.Fit(self)
        
    @staticmethod
    def callUpdateProgress(value, message=""):
        """Updates the status of the progress bar from a thread"""
        wx.CallAfter(pub.sendMessage, "update", value=value, message=message)
        
    def updateProgress(self, value, message=""):
        """Updates the status of the progress bar"""
        if value >= 100:
            message = "Done"
        if message != "":
            self.gaugeText.SetLabel(message)
        self.gauge.SetValue(value)
        
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
                    # The intensive stuff is done in a thread
                    t=threading.Thread(target=self.onImageLoad)
                    t.start()
            except IOError:
                wx.LogError(f"Cannot open file '{pathname}'.")
        
    
    def setImage(self, imageCtrl, imagePath):
        # scale the image, preserving the aspect ratio
        img = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
        self.image_width = img.GetWidth()
        self.image_height = img.GetHeight()
        if self.image_width > self.image_height:
            NewW = self.PhotoMaxSize
            NewH = self.PhotoMaxSize * self.image_height / self.image_width
        else:
            NewH = self.PhotoMaxSize
            NewW = self.PhotoMaxSize * self.image_width / self.image_height
        img = img.Scale(NewW,NewH)
        # Update the image preview
        imageCtrl.SetBitmap(wx.BitmapFromImage(img))
    
    def onImageLoad(self):
        """Behaviour for loading an image to be processed (executed in a thread)"""
        # Prevents the user from interacting with the software
        wx.CallAfter(self.disableButtons)
        
        # Update the text containing the path
        wx.CallAfter(self.imagePathText.SetLabel, os.path.basename(self.imagePath))
        # MAJ UI
        wx.CallAfter(self.refresh)
        
        # Find the colors in the image
        self.colors, self.flatImagePath, self.pixel_list_labels, self.relevant_label_to_color_hexes = findColorsAndMakeNewImage(self.imagePath, MainWindow.callUpdateProgress)
        # Flattened image preview
        wx.CallAfter(self.setImage, self.imageCtrl, self.flatImagePath)
        
        # MAJ UI
        wx.CallAfter(self.refresh)
        
        # Triggers the appearance of the color UI
        wx.CallAfter(self.onColorsChanged)
        
        # Allow the user further interaction with the software
        wx.CallAfter(self.enableButtons)
        
    
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
        select = wx.SpinCtrl(self.panel, min=0, max=100, initial=len(self.colorParamSelect))
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
        
    def onDimensionXChanged(self, event):
        """When the height is changed, ajusts the width to keep the aspect ratio"""
        if self.image_height > 0 and self.image_width > 0:
            newx = self.dimensionXselect.GetValue()
            newy = newx * self.image_height / self.image_width
            if newy <= self.max_height:
                self.dimensionYselect.SetValue(newy)
            else:
                # In case the value went over the maximum
                newx = newx * self.max_height / newy
                self.dimensionXselect.SetValue(newx)
                self.onDimensionXChanged(event)
    
    def onDimensionYChanged(self, event):
        """When the width is changed, ajusts the height to keep the aspect ratio"""
        if self.image_height > 0 and self.image_width > 0:
            newy = self.dimensionYselect.GetValue()
            newx = newy * self.image_width / self.image_height
            if newx <= self.max_width:
                self.dimensionXselect.SetValue(newx)
            else:
                # In case the value went over the maximum
                newy = newy * self.max_width / newx
                self.dimensionYselect.SetValue(newy)
                self.onDimensionYChanged(event)
        
    def onGenerate(self, event):
        """Behaviour of the 'generate' button"""
        # The intensive stuff is done in a thread
        t=threading.Thread(target=self.generate)
        t.start()
                    
    def generate(self):
        """Generates the STL file. Runs in a thread."""
        # Prevents the user from interacting with the software
        wx.CallAfter(self.disableButtons)
        
        try:
            MainWindow.callUpdateProgress(0, "Generating height map")
            colors = [ColorDefinition(color, self.getColorType(color), self.getParameter(color)) for color in self.colors]
            grayscaleImagePath = generateGreyScaleImage(self.imagePath, colors, self.pixel_list_labels, self.relevant_label_to_color_hexes)
            desiredSize = (self.dimensionXselect.GetValue(), self.dimensionYselect.GetValue(),self.dimensionZselect.GetValue())
            desiredThickness = self.thicknessSelect.GetValue()
            meshMandatoryParams = MeshMandatoryParameters(self.imagePath, desiredSize=desiredSize, desiredThickness=desiredThickness)
            MainWindow.callUpdateProgress(50, "Generating STL file")
            generateSTL(grayscaleImagePath, meshMandatoryParams,MainWindow.callUpdateProgress)
            MainWindow.callUpdateProgress(100)
            wx.CallAfter(wx.MessageBox, 'STL generation successful !', 'Info', wx.OK)
        # TODO Better exception handling with specific exceptions
        except Exception as ex:
            MainWindow.callUpdateProgress(0, "Unsuccessful")
            wx.CallAfter(wx.MessageBox, 'STL generation unsuccessful : '+str(ex), 'Error', wx.OK | wx.ICON_ERROR)
        finally:
            # Allow the user further interaction with the software
            wx.CallAfter(self.enableButtons)