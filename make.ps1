<#
    .SYNOPSIS
        Generates an exe file containing the program

    .DESCRIPTION
        The exe file contains the python environment, and the python source needed to run the program
        In order for bpy to find the blender scripts, they need to be provided next to the exe
        Temporary files will be stored in ./build/
        Generated exe and copied Blender scripts will be stored in ./dist/

    .PARAMETER PythonPath
        The path to your python executable.
        If using a virtual environment, the python executable sould be inside
        If not specified, the script will look for it in the file '.env'

    .PARAMETER BlenderScriptPath
        The path to the folder containing the Blender python scripts.
        In not specified, the script will look for it inside your bpy installation.
#>
param(
    [string]$PythonPath = $null,
    [string]$BlenderScriptPath = $null
)

$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition
$needsCondaActivate = $true

if((-not $PythonPath) -and (Test-Path .env)) {
    # Read python env directory
    $PythonPath = (Get-Content .env) `
    | Where-Object { $_ -match '^PYTHONPATH="?(.*)python.exe' } `
    | ForEach-Object { $Matches[1] }
}

if(-not $PythonPath) {
    # Use the default python and hope we already are in a virtual environment
    $PythonPath = split-path -parent (Get-Command python).Source
    $needsCondaActivate = $false
}

# Error handling
if(-not $PythonPath) {
    Write-Error "Could not locate python path. Define it in file '.env' or pass it as an argument"
    exit
}

if(-not $BlenderScriptPath) {
    # Old script location
    $benderScriptFolder = (Get-ChildItem $PythonPath) `
    | Where-Object { $_.Name -match "^\d+\.\d+$" } `
    | ForEach-Object { $_.FullName }
}

if(-not $BlenderScriptPath) {
    # New script location
    $benderScriptFolder = (Get-ChildItem (Join-Path $PythonPath "Lib\site-packages\bpy")) `
    | Where-Object { $_.Name -match "^\d+\.\d+$" } `
    | ForEach-Object { $_.FullName }
}

# Error handling
if(-not $benderScriptFolder) {
    Write-Error "Could not locate blender scripts in python folder '$PythonPath'"
    exit
}

# Makes shure we are in the correct folder
Push-Location $scriptPath
if(-not (Test-Path "src/main.py")) {
    Write-Error "Could not locate python file : main.py."
    exit
}

# Generate executable (path is changed to double all occurences of '\' to please cmd)
if($needsCondaActivate) {
    cmd /c "call conda activate `"$($PythonPath -replace '\\','\\')`" & pyinstaller --onefile src/main.py"
}
else {
    cmd /c "pyinstaller --onefile src/main.py"
}

# Renames the executable
$exeName = "Image2Touch.exe"
$exePath = "dist/$exeName"
if(Test-Path $exePath) {
    Remove-Item $exePath
}
Rename-Item "dist/main.exe" $exeName

# Copy Blender scripts
Copy-Item -Recurse -Force $benderScriptFolder dist\

# Convert and copy documentation
./doc_to_html.ps1
Copy-Item "help.html" dist\

# Leave the folder
Pop-Location