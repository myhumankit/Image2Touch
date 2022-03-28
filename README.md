# Blender-based SVG to STL 

## User manual

### Requirements

This program has only been tested for Windows 10.

### Installation procedure

This program is a standalone executable.
To install it, simply extract the files from the archive into an empty folder.
Once the files are extracted, you can run the program by executing the exe file included.

### How to convert an image to a printable SVG

In order to convert an image, follow these steps :
- Open the program, and wait for the GUI to appear.
- Click on "Select a file..." (Alt+F), choose the file you want to convert, and click "OK".
- Wait for the file to be processed, as indicated by the progress bar at the bottom of the screen. This may take between a few seconds and a minute.
- Change the parameters (dimensions, height of each color...) to your liking.
- Click on "Generate" (Alt+G).
- Wait for the file to be generated, as indicated by the progress bar at the bottom of the screen. This might take a few minutes.
- Recover your SVG file, placed next to the original image file.

## Contributor manual

### Requirements
- Python 3.7.11
- Anaconda
- Blender  (version 2.82 should be compatible)

For a list of all python modules used, see the file *env_mhk.yml*.

### How to setup your environment
1. Create a python virtual environment with `conda env create -f env_mhk.yml`
3. Open the mhk virtual environment with `conda activate mhk`.
4. Run the command `pip install bpy_post_install`. It will look for the Blender software on your computer and generate a symlink towards the Blender folder.

### How to run the script
1. Open the mhk virtual environment with `conda activate mhk`.
2. Use the command line `blender -P [script_name] --background`

### How to run the GUI
1. Open the mhk virtual environment with `conda activate mhk`.
2. Inside this new environment, launch `python main.py`

### How to setup run and debug for VSCode
1. Create a python virtual environment as explained in the previous section
2. Make sure pyinstaller is installed in your environment
3. Create a file named ".env", and inside define PYTHONPATH pointing to your environment, for example : `PYTHONPATH="C:\[...]\mhk\python.exe"`
