import sys
import subprocess
import re
import os
import urllib
import urllib.request
import zipfile
import semver
import argparse
import json
import types

APP_VER = "0.5.1"

# semver.version.Version[]
availableVersions = []

# List of avliable versions
versionsUrl = "https://raw.githubusercontent.com/KenCorma/electron-swapper/refs/heads/test/versions.json"

# Level of verbosity
verboseLevel = 0

# printVerbose
def print_(anyObj, level= 0):
    if (verboseLevel >= level):
        print(anyObj)

# Run Powershell Command
def PSRun( cmd):
    print_(cmd,1)
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True)
    return completed

# Determine a version from the avaiable version list that closely matches the given version.
def DetermineClosesVer(targetVer):
    print_("Checking: " + targetVer.__str__(),1)
    availableMajors = []
    availableMinors = []
    highestMinor = 0
    bestMatch = semver.version.Version.parse("0.0.0")
    for _major in availableVersions:
        if (_major.major == targetVer.major):
            availableMajors.append(_major)
    for _minor in availableMajors:
        if (_minor.minor == targetVer.minor):
            availableMinors.append(_minor)
        if (highestMinor < _minor.minor):
            highestMinor = _minor.minor    
    for _patch in availableMinors:
        if (_patch.patch >= bestMatch.patch):
            bestMatch = _patch
    print_(bestMatch)
    if (bestMatch.major == 0):
        if (len(availableMajors) > 0):
            bestMatch = DetermineClosesVer(semver.version.Version(targetVer.major,highestMinor,0))
        else:
            bestMatch = DetermineClosesVer(targetVer.bump_major())

    return bestMatch

# Take the receipt file and use it to revert the injection 
def RevertInjection(receiptPath):
    with open(receiptPath) as f:
        receiptData = json.load(f)
    topPath = receiptPath.replace(os.path.basename(receiptPath),'')
    backupPath = topPath + "backup\\"
    for injFile in receiptData['newFiles']:
        os.remove(topPath + injFile)
    os.rmdir(topPath + "locales")
    for backFile in receiptData['itemsMoved']:
        os.rename(backupPath + backFile , topPath + backFile)
    os.remove(receiptPath)
    os.rmdir(backupPath)
    

# Use original if override was not provided
def OV(original,override):
    if (override == None):
        return original
    else:
        return override
    
# Helper, get the dict property from given obj
def GetObjDict(obj):
    return obj.__dict__

# Using input ask a yes or no question, repeat if needed
def AskYesOrNo(message):
    answer = input(message + " y (yes) or n (no)")
    if (answer == 'y' or answer == 'n'):
        if (answer == 'y'):
            return True
        else:
            return False
    else:
        AskYesOrNo(message)

if __name__ == '__main__':

    # Set arg handlers
    argHandler = argparse.ArgumentParser("Electron Swapper v" + APP_VER)
    argHandler.add_argument("-v","--version",help="Print Version", action="version", version="v0.1.0")
    argHandler.add_argument("-t","--target", help="Path to a electron app's .exe to be injected",type=str, metavar='PATH')
    argHandler.add_argument("-r","--revert",metavar="PATH", help="Path to receipt file to revert the injection", type=str)
    argHandler.add_argument("-ov","--override-version",metavar="\"x.y.z\"", help="Use this version instead of them one from the target", type=str)
    argHandler.add_argument("-ou","--override-url",metavar="URL",help="Overide the url used to inject target with new electron", type=str)
    argHandler.add_argument("--verbose",metavar="NUMBER", help="Level of verbosity, 0 - 2, lower is less", type=int,default=0)
    argHandler.add_argument("dragTarget", nargs=argparse.REMAINDER, help="Enables Drag and Drop targets for default swapping or reverting")
    parsedArgs = argHandler.parse_args()
    
    # Set verbose level
    verboseLevel = parsedArgs.verbose

    # If revert flag then run that program
    if (parsedArgs.revert != None):
        revertPath = parsedArgs.revert
        if (revertPath.endswith(".receipt")):
             RevertInjection(os.path.normpath(revertPath))
        else:
            print_("The receipt path " + revertPath + " , Is not correct")
        sys.exit()
       
    #Set Target Path
    if (parsedArgs.target != None):
        electronTargetPath = parsedArgs.target
    elif (parsedArgs.dragTarget != None and len(parsedArgs.dragTarget) > 0):
        electronTargetPath = parsedArgs.dragTarget[0]
        if (electronTargetPath.endswith(".receipt")):
            RevertInjection(os.path.normpath(electronTargetPath))
    else:
        print_("No Target!")
        sys.exit()

    print_("Path: " + electronTargetPath)
    print_("exe: " + os.path.basename(electronTargetPath),1)

    # Gather available builds
    tempVerArray = []
    versionUrlDataRaw = urllib.request.urlopen(versionsUrl).read().decode("utf-8")
    versionsUrlData = json.loads(versionUrlDataRaw)
    for _version in versionsUrlData["versions"]:
        tempVerArray.append(semver.version.Version.parse(_version))

    availableVersions = tempVerArray
    
    # Use Powershell to get version string
    selectCommand = "select-string -Path \"{0}\" -Pattern \"{1}\" -AllMatches"
    mainPath = os.path.normpath(electronTargetPath)
    exeName = os.path.basename(electronTargetPath)
    regexPattern = "Chrome/[0-9.]* Electron/[0-9.]*"
    commandReturn = PSRun(selectCommand.format(mainPath,regexPattern))
    stringMatch = re.search(regexPattern, commandReturn.stdout.decode())
    if stringMatch:
        found = stringMatch.group(0)
    else:
        print_("Cant find electron version in {0}".format(stringMatch))
        sys.exit()

    eFound = re.search("Electron/[0-9.]*", found)
    targetsElectronVer = semver.version.Version.parse(eFound.group(0).replace("Electron/",""))

    if (targetsElectronVer.major < 23):
        print_("Replacement not needed")
        sys.exit()

    # Check if there is a version override 
    if (parsedArgs.override_version != None):
        closestVer = semver.version.Version.parse(parsedArgs.override_version)
    else:
        closestVer = DetermineClosesVer(targetsElectronVer)

    print_("Closes available version:" + closestVer.__str__(),1)

    # Ask Before
    answer = AskYesOrNo("Target Version: {0} will be replaced with {1} . Is that Ok?".format(targetsElectronVer.__str__(),closestVer.__str__()))
    
    if (answer == False):
        sys.exit()
    
    replaceFiles = [
        "locales",
        "chrome_100_percent.pak",
        "chrome_200_percent.pak",
        "d3dcompiler_47.dll",
        "ffmpeg.dll",
        "icudtl.dat",
        "libEGL.dll",
        "libGLESv2.dll",
        "LICENSE.electron.txt",
        "LICENSES.chromium.html",
        "resources.pak",
        "snapshot_blob.bin",
        "v8_context_snapshot.bin",
        "vk_swiftshader.dll",
        "vk_swiftshader_icd.json",
        exeName
    ]

    # Set up receipt Object 
    receiptData = types.SimpleNamespace()
    receiptData.injectorVer = APP_VER
    receiptData.itemsMoved = replaceFiles
    receiptData.newFiles = []
    receiptData.originalElectronVersion = targetsElectronVer.__str__()
    receiptData.injectedElectronVersion = closestVer.__str__()
    
    mainPath = mainPath.replace(exeName,'')
    
    os.makedirs(mainPath + "\\backup",exist_ok=True)
    for oldF in replaceFiles:
        os.renames(mainPath + "\\" + oldF,mainPath + r"\backup\{0}".format(oldF))

    verToUse = "30.5.1" #OV(closestVer.__str__(),parsedArgs.override_version)

    zipDLPath = OV("https://github.com/KenCorma/supermium-electron/releases/download/v{0}/electron-v{1}-win32-x64.zip".format(verToUse , verToUse), parsedArgs.override_url)

    print_("Downloading: " + zipDLPath,1)

    # Download and unpack zip
    zip_path, _ = urllib.request.urlretrieve(zipDLPath)
    with zipfile.ZipFile(zip_path, "r") as zFile:
        tempZipFileList = []
        print_("Extracing Zip",1)
        for unpackedFile in zFile.filelist:
            print_("Extracting: " + unpackedFile.filename,2)
            tempZipFileList.append(unpackedFile.filename)
        receiptData.newFiles = tempZipFileList
        zFile.extractall(mainPath)

    # Create Shortcut which can be used to run app
    shortcutFileName = exeName + ".lnk"
    shortcutFilePath = mainPath + "\\" + shortcutFileName
    receiptData.newFiles.append(shortcutFileName)
    shortcutCommand = '''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{0}")
        $Shortcut.TargetPath = "{1}"
        $Shortcut.IconLocation = "{2},0"
        $Shortcut.Save()
    '''.format(shortcutFilePath,mainPath + "\\Electron.exe",mainPath + "\\backup\\" + exeName)

    # Execute Shortcut creation
    createLink = PSRun(shortcutCommand)
    print_("Creating new shortcut")
    print_(createLink,2)

    print_("Dumping Receipt")
    print_(receiptData,2)

    # Save a receipt of the inject
    with open(os.path.join(mainPath.replace(exeName,''), exeName.replace(".exe",'') + '.receipt'), 'w') as eFound:
        json.dump(receiptData, eFound, ensure_ascii=False,default=GetObjDict)
    
    print_("Swap Complete")

