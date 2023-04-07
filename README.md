# Image2Touch

## User manual

### About

Image2Touch is a tool that makes maps and other diagrams accessible to visually impaired people.
It does that by converting 2D images with flat colouring into STL models for 3D printing.

The project is a collaboration between [MHK](https://www.mhk.fr/) and [Lab4i](https://groupe-ovalt.com/lab4i/).
You can find a more detailed description (in french) on the [MHK wiki](https://wikilab.myhumankit.org/index.php?title=Projets:Image2Touch).

### Requirements

This program has only been tested with Windows 10.

### Installation procedure (Windows)

This program is a standalone executable.
To install it, simply extract the files from the provided archive into an empty folder.
Once the files are extracted, you can run the program by executing the exe file included.

### How to convert an image to a printable SVG

In order to convert an image, follow these steps :
- Open the program, and wait for the graphical interface to appear.
- Click on "Open a file..." (Alt+O), choose the file you want to convert, and click "OK".
- Wait for the file to be processed, as indicated by the progress bar at the bottom of the screen. This may take between a few seconds and a minute.
- Change the parameters (dimensions, height of each color...) to your liking.
- Click on "Generate" (Alt+G).
- Wait for the file to be generated, as indicated by the progress bar at the bottom of the screen. This might take a few minutes.
- Recover your SVG file, placed next to the original image file.

### Command line options

If you wish to use the program without the user interface, you can use the following command line options :
- `--no-gui` / `--silent` / `-s` : disables the user interface
- `--file path/to/file` / `-f path/to/file` : file to convert to SVG (replace "path/to/file" with the desired path)

## Contributor manual

### Requirements
This tool is made with Python 3.10.9.
For a list of all python modules used, see the file *env.yml*.

Though not strictly required, the use of a virtual environment is strongly recommended.
In the following sections, this guide will assume you are using conda to manage virtual environments.

### How to setup your environment
1. Create a python virtual environment with `conda env create -f env.yml`
2. Open the new virtual environment with `conda activate image2touch`.

### How to run the tool from python
1. Create a python virtual environment as explained in the previous section
2. Open the virtual environment with `conda activate image2touch`.
3. Inside this new environment, run the tool with `python main.py`

### How to build the executable (Windows)
1. Create a python virtual environment as explained previously
2. Run the script *make.ps1* using powershell, for example by using `powershell -f build.ps1`. `