# Blender-based SVG to STL 

## Requirements
- Python 3.7.11
- OpenCV2 opencv_python-4.5.4.60 (pip3 install opencv-python)
- Reportlab 3.6.2 (pip3 install reportlab)
- svglib 1.1.0 (pip3 install svglib)
- bpy 2.82.1
- wxPython 4.1.1

## How to run the script
1. Open a terminal
2. Use the command line *blender -P [script_name] --background*

## How to run the GUI
1. Create a python virtual environment with `conda env create -f env_mhk.yml`
2. Inside this new environment, launch `python main.py`