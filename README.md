# Electron Swapper 

### ALPHA 

**Right now this is still in development, the ONLY available election version is 30.1.5 x64, so if the target app is not compatiable with that then there might be issues.**

Electron Swapper is a windows program that will swap an App's electron core with a Supermium version ( or supplied mirror ) to enable broad win32 support across Windows generations. 

## Process

The exe that you click when you run an Electron app is just the base Electron app that points to app.asar. This is generic enough to be able to swapped out and still run the app like normal. 

Providing this app with a target, it will use string-search to probe the target exe and extract the Electron version. It will then download a Supermium version and replace all the file ( while generating a backup). It will create a new shortcut that links the new electron.exe with the target's app.asar that can be used to run the app like normal. 

Providing this app with a .receipt file will undo the swapping that was performed before. 

Dragging the target exe or receipt into the swapper exe will trigger the app to run with the default settings ( Supermium + Closest version). Run the app via command prompt or powershell to enable more commands, like override-url to set the path to a zip that contains electron ( this will also override the version ). 

## Usage

```
positional arguments:
  dragTarget            Enables Drag and Drop targets for default swapping or reverting

options:
  -h, --help            show this help message and exit
  -v, --version         Print Version
  -t PATH, --target PATH
                        Path to a electron app's .exe to be injected
  -r PATH, --revert PATH
                        Path to receipt file to revert the injection
  -ov "x.y.z", --override-version "x.y.z"
                        Use this version instead of them one from the target
  -ou URL, --override-url URL
                        Overide the url used to inject target with new electron
  --verbose NUMBER      Level of verbosity, 0 - 2, lower is less
```

## Building

Pip install all the imports if you don't already have them. Download PypInstaller and use the .spec file to build swapper.py .
