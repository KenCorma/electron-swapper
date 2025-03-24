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

# semver.version.Version[]
avaliableVersions = [
]

# List of avliable versions
versionsUrl = "https://raw.githubusercontent.com/KenCorma/electron-swapper/refs/heads/test/versions.json"

verboseLevel = 0

# printVerbose
def print_(anyObj, level= 0):
    if (verboseLevel >= level):
        print(anyObj)

# Run Powershell Command
def run( cmd):
    print_(cmd)
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True)
    return completed

# Determine a version from the avaiable version list that closely matches the given version.
def determinClosesVer(targetVer):
    print_("Checking: " + targetVer.__str__())
    avaliableMajors = []
    avaliableMinors = []
    highestMinor = 0
    bestMatch = semver.version.Version.parse("0.0.0")
    for _major in avaliableVersions:
        if (_major.major == targetVer.major):
            avaliableMajors.append(_major)
    for _minor in avaliableMajors:
        if (_minor.minor == targetVer.minor):
            avaliableMinors.append(_minor)
        if (highestMinor < _minor.minor):
            highestMinor = _minor.minor    
    for _patch in avaliableMinors:
        if (_patch.patch >= bestMatch.patch):
            bestMatch = _patch
    print_(bestMatch)
    if (bestMatch.major == 0):
        if (len(avaliableMajors) > 0):
            bestMatch = determinClosesVer(semver.version.Version(targetVer.major,highestMinor,0))
        else:
            bestMatch = determinClosesVer(targetVer.bump_major())

    return bestMatch

# Take the reciept file and use it to revert the injection 
def RevertInjection(recieptPath):
    with open(recieptPath) as f:
        recieptData = json.load(f)
    topPath = recieptPath.replace(os.path.basename(recieptPath),'')
    backupPath = topPath + "backup\\"
    for injFile in recieptData['newFiles']:
        os.remove(topPath + injFile)
    os.rmdir(topPath + "locales")
    for backFile in recieptData['itemsMoved']:
        os.rename(backupPath + backFile , topPath + backFile)
    os.remove(recieptPath)
    os.rmdir(backupPath)
    

# Use original if override was not provided
def OV(orignal,override):
    if (override == None):
        return orignal
    else:
        return override
    
# Helper, get the dict property from given obj
def get_obj_dict(obj):
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
    argHandler = argparse.ArgumentParser("Electron Injector")
    argHandler.add_argument("-t","--target", help="Path to a electron app's .exe to be injected",type=str, metavar='PATH')
    argHandler.add_argument("-r","--revert",metavar="PATH", help="Path to recipt file to revert the injection", type=str)
    argHandler.add_argument("-v","--version",help="Print Version", action="version", version="v0.1.0")
    argHandler.add_argument("-ov","--override-version",metavar="\"x.y.z\"", help="Use this version instead of them one from the target", type=str)
    argHandler.add_argument("-ou","--override-url",metavar="URL",help="Overide the url used to inject target with new electron", type=str)
    argHandler.add_argument("dragTarget", nargs=argparse.REMAINDER)
    parsedArgs = argHandler.parse_args()
    
    # If revert flag then run that program
    if (parsedArgs.revert != None):
        revertPath = parsedArgs.revert
        if (revertPath.endswith(".reciept")):
             RevertInjection(os.path.normpath(revertPath))
        else:
            print_("The recipt path " + revertPath + " , Is not correct")
        exit()
       
    #Set Target Path
    if (parsedArgs.target != None):
        electronTargetPath = parsedArgs.target
    elif (parsedArgs.dragTarget != None and len(parsedArgs.dragTarget) > 0):
        electronTargetPath = parsedArgs.dragTarget[0]
    else:
        print_("No Target!")
        exit()

    print_("Path: " + electronTargetPath)
    print_("exe: " + os.path.basename(electronTargetPath))

    # Gather avaliable builds
    tempVerArray = []
    versionUrlDataRaw = urllib.request.urlopen(versionsUrl).read().decode("utf-8")
    versionsUrlData = json.loads(versionUrlDataRaw)
    for _version in versionsUrlData["versions"]:
        tempVerArray.append(semver.version.Version.parse(_version))

    avaliableVersions = tempVerArray
    
    # Use Powershell to get version string
    selectCommand = "select-string -Path \"{0}\" -Pattern \"{1}\" -AllMatches"
    mainPath = os.path.normpath(electronTargetPath)
    exeName = os.path.basename(electronTargetPath)
    regexPattern = "Chrome/[0-9.]* Electron/[0-9.]*"
    commandReturn = run(selectCommand.format(mainPath,regexPattern))
    stringMatch = re.search(regexPattern, commandReturn.stdout.decode())
    if stringMatch:
        found = stringMatch.group(0)
    else:
        print_("Cant find electron version in {0}".format(stringMatch))
        exit()

    eFound = re.search("Electron/[0-9.]*", found)
    targetsElectronVer = semver.version.Version.parse(eFound.group(0).replace("Electron/",""))

    if (targetsElectronVer.major < 23):
        print_("Replacement not needed")

    # Check if there is a version override 
    if (parsedArgs.override_version != None):
        closestVer = semver.version.Version.parse(parsedArgs.override_version)
    else:
        closestVer = determinClosesVer(targetsElectronVer)

    print_("Closes" + closestVer.__str__())

    # Ask Before
    answer = AskYesOrNo("Target Version: {0} will be replaced with {1} . Is that Ok?".format(targetsElectronVer.__str__(),closestVer.__str__()))
    
    if (answer == False):
        exit()
    
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

    # Set up Reciept Object 
    reciptData = types.SimpleNamespace()
    reciptData.injectorVer = "0.1.0"
    reciptData.itemsMoved = replaceFiles
    reciptData.newFiles = []
    reciptData.originalElectronVersion = targetsElectronVer.__str__()
    reciptData.injectedElectronVersion = closestVer.__str__()
    
    mainPath = mainPath.replace(exeName,'')
    
    os.makedirs(mainPath + "\\backup",exist_ok=True)
    for oldF in replaceFiles:
        os.renames(mainPath + "\\" + oldF,mainPath + r"\backup\{0}".format(oldF))


    # Download and unpack zip
    zip_path, _ = urllib.request.urlretrieve(OV("https://github.com/KenCorma/supermium-electron/releases/download/" + OV("v30.5.1-0",parsedArgs.override_version) + "/electron-v30.5.1-win32-x64.zip", parsedArgs.override_url))
    with zipfile.ZipFile(zip_path, "r") as zFile:
        tempZipFileList = []
        for unpackedFile in zFile.filelist:
            tempZipFileList.append(unpackedFile.filename)
        reciptData.newFiles = tempZipFileList
        zFile.extractall(mainPath)

    # Create Shortcut which can be used to run app
    shortcutFileName = exeName + ".lnk"
    shortcutFilePath = mainPath + "\\" + shortcutFileName
    reciptData.newFiles.append(shortcutFileName)
    shortcutCommand = '''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{0}")
        $Shortcut.TargetPath = "{1}"
        $Shortcut.IconLocation = "{2},0"
        $Shortcut.Save()
    '''.format(shortcutFilePath,mainPath + "\\Electron.exe",mainPath + "\\backup\\" + exeName)

    # Execute Shortcut creation
    createLink = run(shortcutCommand)
    print_(createLink)

    print (reciptData)

    # Save a reciept of the inject
    with open(os.path.join(mainPath.replace(exeName,''), exeName.replace(".exe",'') + '.reciept'), 'w') as eFound:
        json.dump(reciptData, eFound, ensure_ascii=False,default=get_obj_dict)

