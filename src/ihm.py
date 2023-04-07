import wx
from wx.lib.expando import ExpandoTextCtrl
from pubsub import pub
import threading
from color_types import ColorDefinition
from progress import Progress
import os
from img_to_stl import ImgToStl

class LabeledControlHelper(object):
    """ Represents a Labeled Control, inspierd by the NVDA implementation.
    The label can be made invisible, in order to change what is said by screen readers without displaying the label on screen
    """
    def __init__(self, parent: wx.Window, labelText: str, wxCtrlClass: wx.Control, orientation=wx.HORIZONTAL, noLabel:bool=False, **kwargs):
        """Constructor for the labelled control

        Args:
            parent (wx.Window):  An instance of the parent wx window. EG wx.Dialog
            labelText (str): The text to display next to the control
            wxCtrlClass (wx.Control): The class of the control
            orientation (_type_, optional): If wx.VERTICAL, the label is to the top of the control, otherwise it is to the left. Defaults to wx.HORIZONTAL.
            noLabel (bool, optional): If true, the label is not displayed on screen, but will still be read by screen readers. Defaults to False.
        """
        
        object.__init__(self)
        if noLabel:
            self.label = wx.StaticText(parent, label=labelText, size=(0,0))
        else:
            self.label = wx.StaticText(parent, label=labelText)
        self.control = wxCtrlClass(parent, **kwargs)
        self.sizer = wx.BoxSizer(orientation)
        self.sizer.Add(self.label, flag=(wx.ALIGN_CENTER_VERTICAL if orientation==wx.HORIZONTAL else wx.ALIGN_CENTER_HORIZONTAL))
        self.sizer.AddSpacer(10 if orientation==wx.HORIZONTAL else 3)
        self.sizer.Add(self.control, flag=(wx.ALIGN_CENTER_VERTICAL if orientation==wx.HORIZONTAL else wx.ALIGN_CENTER_HORIZONTAL))

    def make(parent: wx.Window, labelText: str, wxCtrlClass: wx.Control, orientation=wx.HORIZONTAL, noLabel:bool=False, **kwargs):
        lch = LabeledControlHelper(parent, labelText, wxCtrlClass, orientation, noLabel, **kwargs)
        return  lch.control, lch.sizer

class MainWindow(wx.Frame):
    """The main window of the application"""
    def __init__(self, parent, title):
        """Constructor for the window"""
        super(MainWindow, self).__init__(parent, title=title)
        
        self.image_width = 0
        self.image_height = 0
        self.max_height = 1000
        self.max_width = 1000
        self.max_depth = 50
        self.minimum_step_btw_highest_lowest_points = 1.0 # The minimum step of height between the highest point of the object and the lowest point of the top surface.

        self.img_to_stl = ImgToStl()
        self.progress = Progress(max=100, callback=MainWindow.callUpdateProgress, error_callback=self.callErrorMessageBox)

        self.initUI()
        self.Centre()


    def initUI(self):
        """Builds and displays all the UI elements of the window"""
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(vgap=10)
        
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)

        self.panel = panel
        self.sizer = sizer
        self.outer_sizer = wx.BoxSizer()        
        self.outer_sizer.Add(self.sizer, flag= wx.ALL | wx.EXPAND, border=10)
        
        panel.SetSizer(self.outer_sizer)
        
        #################### Menu Bar ####################
        
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.menuhandler)

        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, '&File')
        
        self.openMenuItem = wx.MenuItem(fileMenu,wx.ID_OPEN, text = "&Open...",kind = wx.ITEM_NORMAL)
        fileMenu.Append(self.openMenuItem)

        self.generateMenuItem = wx.MenuItem(fileMenu,wx.ID_EXECUTE, text = "&Generate",kind = wx.ITEM_NORMAL)
        fileMenu.Append(self.generateMenuItem)
        # This menu item is disabled at first and enabled when an image loads
        self.generateMenuItem.Enable(False)

        helpMenu = wx.Menu()
        menuBar.Append(helpMenu, '&Help')
        
        manualMenuItem = wx.MenuItem(helpMenu,wx.ID_HELP, text = "User &Manual",kind = wx.ITEM_NORMAL)
        helpMenu.Append(manualMenuItem)
        
        aboutMenuItem = wx.MenuItem(helpMenu,wx.ID_ABOUT, text = "&About",kind = wx.ITEM_NORMAL)
        helpMenu.Append(aboutMenuItem)
        
        #################### Input file ####################
        
        fileChoixeSizer = wx.StaticBoxSizer(wx.HORIZONTAL, panel, "Input file")
        # ExpandoTextCtrl is a variant of wx.StaticText that stays focusable even in readonly mode
        self.imagePathText = ExpandoTextCtrl(panel, value="No file selected", style= wx.TE_READONLY, size=(-1, 26))
        fileChoixeSizer.Add(self.imagePathText, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
        
        self.buttonOpen = wx.Button(panel, label="&Open a file...", size=(-1, 28))
        self.buttonOpen.Bind(wx.EVT_BUTTON,self.onOpen)
        fileChoixeSizer.Add(self.buttonOpen, flag=wx.ALL, border=4)
        
        sizer.Add(fileChoixeSizer, pos=(0, 0), flag=wx.EXPAND)
        
        #################### Colors ####################
        
        self.colorSizer = wx.FlexGridSizer(cols=3, vgap=4, hgap=10)
        
        colorGroupSizer = wx.StaticBoxSizer(wx.VERTICAL, panel, "Colors")
        colorGroupSizer.Add(self.colorSizer, flag=wx.ALL, border=4)
        sizer.Add(colorGroupSizer, pos=(1, 0), flag=wx.EXPAND)
        
        #################### Dimensions (mm) ####################
        
        dimensionSizer = wx.StaticBoxSizer(wx.HORIZONTAL, panel, "Dimensions (mm)")
        
        self.widthSpinner, widthSizer = LabeledControlHelper.make(self.panel, "Width", wx.SpinCtrl, orientation=wx.VERTICAL,
                                                                  min=10, max=self.max_width, initial=self.img_to_stl.meshParameters.meshWidthMM, size=(50,-1))
        self.heightSpinner, heightSizer = LabeledControlHelper.make(self.panel, "Height", wx.SpinCtrl, orientation=wx.VERTICAL, 
                                                                    min=10, max=self.max_height, initial=self.img_to_stl.meshParameters.meshHeightMM, size=(50,-1))
        self.baseThicknessSpinner, baseThicknessSizer = LabeledControlHelper.make(self.panel, "Base Thickness", wx.SpinCtrl, orientation=wx.VERTICAL, 
                                                                                  min=1, max=self.max_depth, initial=self.img_to_stl.meshParameters.meshBaseThicknessMM, size=(50,-1))
        self.widthSpinner.Bind(wx.EVT_SPINCTRL,self.onWidthChanged)
        self.heightSpinner.Bind(wx.EVT_SPINCTRL,self.onHeightChanged)
        self.imageThicknessSpinner, imageThincknessSizer = LabeledControlHelper.make(self.panel, "Shape Thickness", wx.SpinCtrl, orientation=wx.VERTICAL, 
                                                                                     min=1, max=self.max_depth, initial=self.img_to_stl.meshParameters.meshImageThicknessMM, size=(50,-1))
        dimensionSizer.Add(widthSizer, flag=wx.ALL, border=4)
        dimensionSizer.Add(heightSizer, flag=wx.ALL, border=4)
        dimensionSizer.Add(baseThicknessSizer, flag=wx.ALL, border=4)
        dimensionSizer.Add(imageThincknessSizer, flag=wx.ALL, border=4)
        
        sizer.Add(dimensionSizer, pos=(2, 0), flag=wx.EXPAND)

        #################### Export options ####################
        
        exportSizer = wx.StaticBoxSizer(wx.HORIZONTAL, panel, "Export options")
        self.checkboxSaveSTLFile = wx.CheckBox(panel, label='Save STL file')
        self.checkboxSaveSTLFile.SetValue(True)
        exportSizer.Add(self.checkboxSaveSTLFile, flag=wx.ALL, border=4)
        
        self.checkboxSaveBlendFile = wx.CheckBox(panel, label='Save Blend file')  
        exportSizer.Add(self.checkboxSaveBlendFile, flag=wx.ALL, border=4)
        
        sizer.Add(exportSizer, pos=(3, 0), flag=wx.EXPAND)

        #################### Generation ####################
        
        self.buttonGenerate = wx.Button(panel, label="&Generate", size=(90, 28))
        self.buttonGenerate.Bind(wx.EVT_BUTTON,self.onGenerate)
        sizer.Add(self.buttonGenerate, pos=(4, 0), flag=wx.EXPAND | wx.TOP, border=5)
        # This button is disabled at first and enabled when an image loads
        self.buttonGenerate.Disable()
        
        
        loadingSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.gaugeText = wx.StaticText(panel, label="Idle")
        loadingSizer.Add(self.gaugeText)
        
        self.gauge = wx.Gauge(panel, range=100)
        loadingSizer.Add(self.gauge, flag=wx.EXPAND)
        
        sizer.Add(loadingSizer, pos=(5, 0), flag=wx.EXPAND)
        
        # Respond to the update event
        pub.subscribe(self.updateProgress, "update")
        
        #################### Preview ####################
        
        self.PhotoMaxSize = 200
        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, 
                                         wx.Bitmap(wx.Image(self.PhotoMaxSize,self.PhotoMaxSize)))
        sizer.Add(self.imageCtrl, pos=(0, 2), span=(5,1), flag=wx.EXPAND)
        
        #############################################
        
        self.outer_sizer.Fit(self)
        
    def menuhandler(self, event):
        """
        Called when a menu item is used.
        Contains no logic, simply redirects to the appropriate functions.
        """
        id = event.GetId() 
        match id:
            # File -> Open
            case wx.ID_OPEN:
                self.onOpen(event)
            # File -> Generate
            case wx.ID_EXECUTE:
                self.onGenerate(event)
            # Help -> User Manual
            case wx.ID_HELP:
                self.onHelp(event)
            # Help -> About
            case wx.ID_ABOUT:
                self.onAbout(event)
            # Other
            case _:
                pass
    
    def onHelp(self, event):
        help_url = "help.html"
        if os.path.isfile(help_url):
            os.system(f"start {help_url}")
        else:
            wx.MessageBox('Help file not found', 'Error', wx.OK | wx.ICON_ERROR)
    
    def onAbout(self, event):
        about_text = (
            "Image2Touch\n"
            "\nDeveloped in collaboration between MHK and Lab4i"
            "\nGithub repository : https://github.com/myhumankit/Image2Touch"
            "\nProject page on the MHK wiki : https://wikilab.myhumankit.org/index.php?title=Projets:Image2Touch"
        )
        wx.MessageBox(about_text, 'Image2Touch', wx.OK | wx.ICON_INFORMATION)
    
    def disableButtons(self):
        """Disables all buttons and menu items to prevent interaction during other work"""
        # Buttons
        self.buttonOpen.Disable()
        self.buttonGenerate.Disable()
        self.checkboxSaveSTLFile.Disable()
        self.checkboxSaveBlendFile.Disable()
        # Menu Items
        self.openMenuItem.Enable(False)
        self.generateMenuItem.Enable(False)

    def enableButtons(self):
        """Re-enables all buttons and menu items after background work is done"""
        # Buttons
        self.buttonOpen.Enable()
        self.buttonGenerate.Enable()        
        self.checkboxSaveSTLFile.Enable()
        self.checkboxSaveBlendFile.Enable()
        # Menu Items
        self.openMenuItem.Enable()
        self.generateMenuItem.Enable()
        
    def refresh(self):
        """Refreshes the layout of the window (this needs to happen if elements change size)"""
        self.panel.Refresh()
        self.outer_sizer.Fit(self)
        
    @staticmethod
    def callUpdateProgress(value, message=""):
        """Updates the status of the progress bar from a thread"""
        wx.CallAfter(pub.sendMessage, "update", value=value, message=message)
        
    def updateProgress(self, value, message=""):
        """Updates the status of the progress bar"""
        if value >= 100 and message == "":
            message = "Done"
        if message != "":
            self.gaugeText.SetLabel(message)
        self.gauge.SetValue(int(value))
        
    def callErrorMessageBox(self, message: str):
        wx.CallAfter(wx.LogError, message)
        
    def onOpen(self, event):
        """Behaviour for the 'Open...' button. An image file can be selected for processing"""
        supported_formats = [
            "jpg",
            "jpeg",
            "jpe",
            "bmp",
            "png",
        ]
        supported_formats_str = ";".join([f"*.{ext}" for ext in supported_formats])
        with wx.FileDialog(self, "Load an image file to process", wildcard=f"Image files ({supported_formats_str}) |{supported_formats_str}",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            try:
                # We try to open the file to check if it is accessible
                with open(pathname, 'r') as file:
                    # self.imagePath = pathname
                    # The intensive stuff is done in a thread
                    threading.Thread(target=self.onImageLoad, args=[pathname]).start()
            except IOError:
                wx.LogError(f"Cannot open file '{pathname}'.")
        
    
    def setImage(self, imageCtrl, imagePath):
        """Changes the displayed image in the preview"""
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
        img = img.Scale(int(NewW),int(NewH))
        # Update the image preview
        imageCtrl.SetBitmap(wx.Bitmap(img))
    
    def onImageLoad(self, imagePath: str):
        """Behaviour for loading an image to be processed (executed in a thread)"""
        # Prevents the user from interacting with the software
        wx.CallAfter(self.disableButtons)
        
        # Update the text containing the path
        wx.CallAfter(self.imagePathText.SetValue, os.path.basename(imagePath))
        
        # MAJ UI
        wx.CallAfter(self.refresh)
        
        # Find the colors in the image
        self.img_to_stl.loadImageSync(imagePath, self.progress)
        
        # Flattened image preview
        wx.CallAfter(self.setImage, self.imageCtrl, self.img_to_stl.flatImagePath)
        
        # MAJ UI
        wx.CallAfter(self.refresh)
        
        # Triggers the appearance of the color UI
        wx.CallAfter(self.onColorsChanged)
        
        # Triggers the aspect ratio logic
        wx.CallAfter(self.onWidthChanged, None)
        
        # Allow the user further interaction with the software
        wx.CallAfter(self.enableButtons)
        
    
    def makeColorSquare(self, color):
        """Makes a color square with the given color"""
        square = wx.StaticText(self.panel, label=" ")
        square.SetMinSize((25, 25))
        square.SetBackgroundColour(color)
        return square


    def makeColorHeightSelect(self, color):
        """Makes a field for selecting the color processing parameter"""
        select, sizer = LabeledControlHelper.make(self.panel, f"Height for color {1+len(self.colorHeightSelect)}", noLabel=True,
                                                  wxCtrlClass=wx.SpinCtrl, min=0, max=100, initial=len(self.colorHeightSelect))
        self.colorHeightSelect[color] = select
        return sizer
    
    
    def onColorsChanged(self):
        """Behaviour for when the detected colors of the image have changed"""
        # Clears previous content
        self.colorTypeCB = {}
        self.colorHeightSelect = {}
        self.colorSizer.Clear(True)
        self.refresh()
        
        # Adds new content
        content = [(wx.StaticText(self.panel, label=x, style=wx.ALIGN_CENTRE_HORIZONTAL)) for x in [" ","Color","Height"]] # Headers
        content = content + [y for color in self.img_to_stl.colors for y in [
            self.makeColorSquare(color=color),
            wx.StaticText(self.panel, label=color),
            self.makeColorHeightSelect(color)]]
        self.colorSizer.AddMany(content)
        
        # Handle tab order
        for i, color in enumerate(self.img_to_stl.colors):
            select = self.colorHeightSelect[color]
            if(i == 0):
                select.MoveAfterInTabOrder(self.buttonOpen)
            else:
                select.MoveAfterInTabOrder(self.colorHeightSelect[self.img_to_stl.colors[i-1]])
            
        # MAJ UI
        self.refresh()
        
    
    def getColorHeight(self, color: str) -> int:
        """Finds the parameter selected for a given color"""
        select = self.colorHeightSelect[color]
        return select.GetValue()
        
    def onWidthChanged(self, event):
        """When the height is changed, ajusts the width to keep the aspect ratio"""
        if self.image_height > 0 and self.image_width > 0:
            newx = self.widthSpinner.GetValue()
            newy = newx * self.image_height / self.image_width
            if newy <= self.max_height:
                self.heightSpinner.SetValue(int(newy))
            else:
                # In case the value went over the maximum
                newx = newx * self.max_height / newy
                self.widthSpinner.SetValue(int(newx))
                self.onWidthChanged(int(event))
    
    def onHeightChanged(self, event):
        """When the width is changed, ajusts the height to keep the aspect ratio"""
        if self.image_height > 0 and self.image_width > 0:
            newy = self.heightSpinner.GetValue()
            newx = newy * self.image_width / self.image_height
            if newx <= self.max_width:
                self.widthSpinner.SetValue(int(newx))
            else:
                # In case the value went over the maximum
                newy = newy * self.max_width / newx
                self.heightSpinner.SetValue(int(newy))
                self.onHeightChanged(event)

        
    def onGenerate(self, event):
        """Behaviour of the 'generate' button"""
        # The intensive stuff is done in a thread
        threading.Thread(target=self.generate).start()
                    
    def generate(self):
        """Generates the STL file. Runs in a thread."""
        saveBlendFile=self.checkboxSaveBlendFile.GetValue()
        saveSTL=self.checkboxSaveSTLFile.GetValue()
        
        self.img_to_stl.meshParameters.saveBlendFile = self.checkboxSaveBlendFile.GetValue()
        self.img_to_stl.meshParameters.saveSTL = self.checkboxSaveSTLFile.GetValue()
        
        self.img_to_stl.colors_definitions = [ColorDefinition(color, self.getColorHeight(color)) for color in self.img_to_stl.colors]
        
        self.img_to_stl.meshParameters.meshWidthMM = self.widthSpinner.GetValue()
        self.img_to_stl.meshParameters.meshHeightMM = self.heightSpinner.GetValue()
        self.img_to_stl.meshParameters.meshBaseThicknessMM = self.baseThicknessSpinner.GetValue()
        self.img_to_stl.meshParameters.meshImageThicknessMM = self.imageThicknessSpinner.GetValue()
        self.img_to_stl.preserveAspectRatio = False

        if (not saveBlendFile and not saveSTL):
            wx.CallAfter(wx.MessageBox, 'Please, choose at least one file type to save', 'Warning', wx.OK | wx.ICON_WARNING)
        else:
            # Prevents the user from interacting with the software
            wx.CallAfter(self.disableButtons)            

            if self.img_to_stl.generateMeshSync(progress=self.progress):
                message = 'STL generation successful !'
                wx.CallAfter(wx.MessageBox, message, 'Info', wx.OK)
            else:
                wx.CallAfter(wx.MessageBox, 'STL generation unsuccessful', 'Error', wx.OK | wx.ICON_ERROR)
            
            # Allow the user further interaction with the software
            wx.CallAfter(self.enableButtons)