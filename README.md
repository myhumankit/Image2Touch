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

The binary files for this program can be found on the [Releases page.](https://github.com/myhumankit/Image2Touch/releases).
To install it, simply extract the files from the provided archive into an empty folder.
Once the files are extracted, you can run the program by executing the exe file included.

### Limits to which images can be converted

This tool can load any jpg, bmp or png image.
However, some images might not produce satisfactory resutls when used with the tool.
To ensure the best possible result, consider using an image which meets these criteria :
- The image should not be too small to avoid pixelation
- The image should only use flat colouring (no gradients, photographs, etc.)
- The image should not contain thin lines. If you image does contain lines, consider erasing (or thickening) them manually before using the tool.
- The image should not contain too many (as in hundreds of) different colors. This includes colors that may seem identical from afar.

### How to convert an image to a printable STL file

In order to convert an image, follow these steps :
- Open the program, and wait for the graphical interface to appear.
- Click on "Open a file..." (Alt+O), choose the file you want to convert, and click "OK".
- Wait for the file to be processed, as indicated by the progress bar at the bottom of the screen. This may take between a few seconds and a minute.
- If needed, change the height of each color to your liking. Note that the height of each color is an arbitrary value, and will be scaled according to the chosen depth of the object. By default, the colors are sorted from most to least frequent, with the most frequent color having the lowest heignt. This helps minimize the amount of material required.
- Change the dimensions of the generated mesh to your liking.
- Select one or multiple output formats (STL and/or BLEND files).
- Click on "Generate" (Alt+G).
- Wait for the file to be generated, as indicated by the progress bar at the bottom of the screen. This might take up to a few minutes.
- Recover your STL file, placed next to the original image file.

### Command line options

If you wish to use the program without the user interface, you can use the following command line options :
- `--no-gui` / `--silent` / `-s` : disables the user interface
- `--file path/to/file` / `-f path/to/file` : file to convert to STL (replace "path/to/file" with the desired path)

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