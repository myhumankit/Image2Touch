# Blender-based SVG to STL 

## Requirements
- Python 3.7.11
- OpenCV2 opencv_python-4.5.4.60 (pip3 install opencv-python)
- Reportlab 3.6.2 (pip3 install reportlab)
- svglib 1.1.0 (pip3 install svglib)
- wxPython 4.1.1
- bpy 2.82.1
- bpy_post_install 

## How to insall
1. Download and install the Blender software.
2. Use Anaconda to import the mhk virtual environment.
3. Open the mhk virtual environment terminal.
4. Run the command pip install bpy_post_install. It will look for the Blender software on your computer and generate a symlink towards the Blender folder.

## How to run the script
1. Open a terminal
2. Use the command line *blender -P [script_name] --background*

## How to run the GUI
1. Create a python virtual environment with `conda env create -f env_mhk.yml`
2. Inside this new environment, launch `python main.py`