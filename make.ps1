# Error handling
if(-not (Test-Path .env)) {
    exit
}

# Read python env directory
$pythonfolder = (Get-Content .env) |? { $_ -match 'PYTHONPATH="?(.*)python.exe' } |% { $Matches[1] }
$benderScriptFolder = (Get-ChildItem $pythonfolder) |? { $_.Name -match "^\d+\.\d+$" } |% { $_.FullName }

# Error handling
if(-not ($pythonfolder -and $benderScriptFolder)) {
    exit
}

# Generate executable
cmd /c "call conda activate $pythonfolder & pyinstaller --onefile main.py"

# Copy Blender scripts
Copy-Item -Recurse -Force $benderScriptFolder dist\
