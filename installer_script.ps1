param (
    [string]$mode = "fresh"
)

$local_python_dir = "local_python_env" # if this is changed, .gitignore MUST be changed also!!!
$venv_path = "venv"
$local_python_version = "3.10.5" # must be 3.x.x format

$message_color = "DarkGreen"

#NI-VISA link,must contain .exe at the end can be switched to newer/older one
$ni_visa_exec = "ni-visa_19.5_online_repack3.exe" #NI-VISA installer file name, can be switched to a newer/older one
$ni_visa_web_file = "https://download.ni.com/support/nipkg/products/ni-v/ni-visa/19.5/online/ni-visa_19.5_online_repack3.exe" 

function Print{
    param(
        $string,
        $color = $message_color
    )
    Write-Host $string -ForegroundColor $color
}

Print "Automated Measurement Framework Install Script" 
Print "==============================================" 
Print " "

# delete previous environment
Print "-------------------------------------------------------"
if((Test-Path "$local_python_dir")){
    Print "Removing previous environment..."
    Remove-Item -Force -Recurse -Path ($local_python_dir)
}

# getting pyenv to handle python versions, only local, no system-wide modifications
Print "Fetching pyenv python environment manager from Github"
git clone https://github.com/pyenv-win/pyenv-win.git ".\$local_python_dir\pyenv-win"
Print "Installing separate local Python $local_python_version here"

# calling pyenv by executable, because PATH should not be modified
Print "-------------------------------------------------------"
$pyenv_cmd = "./$local_python_dir/pyenv-win/pyenv-win/bin/pyenv.bat"
Invoke-Expression "$pyenv_cmd versions"
Invoke-Expression "$pyenv_cmd install $local_python_version" # install custom py version with pyenv
$local_py= "./$local_python_dir\pyenv-win\pyenv-win\versions\$local_python_version\python"


# create virtual environment using the local py version
Print "-------------------------------------------------------"
Print "Creating virtual environment"
Invoke-Expression "$local_py -m venv ./$local_python_dir/$venv_path"
Invoke-Expression "./$local_python_dir/$venv_path/Scripts/activate" # activating the enviroment
Print "Activating virtual environment"

# install every required package from requirements.txt
Print "-------------------------------------------------------"
Print "Installing required Python Packages"
Invoke-Expression "pip install -r requirements.txt"
Print "Finished installing Python Packages"

# downloading NI-VISA for all the instrument drivers
Print "-------------------------------------------------------"
$answer = Read-Host "Do you want to download and install NI-VISA (required software) [Y/N]"
if ($answer -eq "Y" -or $answer -eq "y") {
    Print "Fetching NI-VISA from the web ..."
    Start-BitsTransfer -Source $ni_visa_web_file -Destination ./$ni_visa_exec
    Print "Installer fetched, please install every component"
    Start-Process ("./$ni_visa_exec")
    Read-Host "If You Completed the NI-VISA Installer (or to skip) Press Enter"
    Print "Removing installer file ..."
    Remove-Item ("./$ni_visa_exec")
    Print "Installer file removed"
} else {
    Print "Skipping NI-VISA install...."
}

Print "-------------------------------------------------------"
$keysight_drivers_name = "Keysight IO Libraries"
# searching for any version of Keysight IO Libraries
$installedPackages = Get-Package | Where-Object { $_.Name -like "*$keysight_drivers_name*" }

if ($installedPackages) {
    Print "Found a version of $keysight_drivers_name installed."
    Print "`t Make sure it is supported by AMF! " "Yellow"
    Print "`t Currently tested versions:" "Yellow"
    Print "`t --------------------------" "Yellow"
    Print "`t - Keysight IO Libraries Suite 2022 Update 1" "Yellow"

} else {
    Print "No version of $keysight_drivers_name found. Please install from this link: www.keysight.com/find/iosuite" "Red"
    Print "IF NOT INSTALLED KEYSIGHT, AGILENT AND HP INSTRUMENTS WILL NOT FUNCTION PROPERLY!! " "Red"
    Print "`t Currently tested versions:" "Yellow"
    Print "`t --------------------------" "Yellow"
    Print "`t - Keysight IO Libraries Suite 2022 Update 1, Download link: www.keysight.com/find/iosuite" "Yellow"
}


# updating the  submodules
git submodule update --init --recursive


# if compatibility mode is enabled
# if ($mode -eq "comp"){
#     $VersionFile = "versions.txt"
#     $Drivers = Get-Content $VersionFile | Out-String | ConvertFrom-StringData # read the driver version from versons.txt
#     Print "-------------------------------------------------------"
#     Print "Using these driver versions:"
#     Print $Drivers
#     foreach ($DriverName in $Drivers.Keys)
#     {
#         #change to submodule directory
#         Set-Location $DriverName
#         git config advice.detachedHead False #turn off detached head advice
#         Print $DriverName": "
#         git checkout $Drivers.$DriverName # checkout the compatible commit version
#         git config advice.detachedHead True #turn back detached head advice
#         Set-Location ..
        
#     }
# }
Print "===================Finished==================="
Print "=============================================="
Print "Virtual Environment active, to quit execute 'deactivate'"
Print "To reactivate, execute 'activate_environment.ps1' "