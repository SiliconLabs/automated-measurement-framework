param (
    [string]$mode = "fresh"
)

$local_python_dir = "local_python_env" # if this is changed, .gitignore MUST be changed also!!!
$venv_path = "venv"
$local_python_version = "3.10.5" # must be 3.x.x format

$message_color = "DarkGreen"

$keysight_visa_exec = "IOLibSuite_18_2_28014.exe"
$keysight_visa_web_file = "\\silabs.com\design\home\bamiklos\IOLibSuite_18_2_28014.exe"
#NI-VISA link,must contain .exe at the end can be switched to newer/older one
$ni_visa_exec = "ni-visa_19.5_online_repack3.exe" #NI-VISA installer file name, can be switched to a newer/older one
$ni_visa_web_file = "https://download.ni.com/support/nipkg/products/ni-v/ni-visa/19.5/online/ni-visa_19.5_online_repack3.exe" 

function Print{
    param(
        $string
    )
    Write-Host $string -ForegroundColor $message_color
}

Print "Automated Measurement Framework Install Script" 
Print "==============================================" 
Print " "

# delete previous enviroment
Print "-------------------------------------------------------"
if((Test-Path "$local_python_dir")){
    Print "Removing previous enviroment..."
    Remove-Item -Force -Recurse -Path ($local_python_dir)
}

# getting pyenv to handle python versions, only local, no system-wide modifications
Print "Fetching pyenv python enviroment manager from Github"
git clone https://github.com/pyenv-win/pyenv-win.git ".\$local_python_dir\pyenv-win"
Print "Installing separate local Python $local_python_version here"

# calling pyenv by executable, because PATH should not be modified
Print "-------------------------------------------------------"
$pyenv_cmd = "./$local_python_dir/pyenv-win/pyenv-win/bin/pyenv.bat"
Invoke-Expression "$pyenv_cmd versions"
Invoke-Expression "$pyenv_cmd install $local_python_version" # install custom py version with pyenv
$local_py= "./$local_python_dir\pyenv-win\pyenv-win\versions\$local_python_version\python"


# create virtual enviroment using the local py version
Print "-------------------------------------------------------"
Print "Creating virtual enviroment"
Invoke-Expression "$local_py -m venv ./$local_python_dir/$venv_path"
Invoke-Expression "./$local_python_dir/$venv_path/Scripts/activate" # activating the enviroment
Print "Activating virtual enviroment"

# install every required package from requirements.txt
Print "-------------------------------------------------------"
Print "Installing required Python Packages"
Invoke-Expression "pip install -r requirements.txt"
Print "Finished installing Python Packages"

# downloading NI-VISA for all the instrument drivers
Print "-------------------------------------------------------"
Print "Fetching NI-VISA from the web ..."
Start-BitsTransfer -Source $ni_visa_web_file -Destination ./$ni_visa_exec
Print "Installer fetched, please install every component"
Start-Process ("./$ni_visa_exec")
Read-Host "If You Completed the NI-VISA Installer (or to skip) Press Enter"
Print "Removing installer file ..."
Remove-Item ("./$ni_visa_exec")
Print "Installer file removed"


Print "-------------------------------------------------------"
Print "Fetching KEYSIGHT-VISA from the SL network ... This might take a few minutes"
Start-BitsTransfer -Source $keysight_visa_web_file -Destination ./$keysight_visa_exec
Start-Process ("./$keysight_visa_exec")
Read-Host "If You Completed the KEYSIGHT-VISA Installer (or to skip) Press Enter"
Print "Removing installer file ..."
Remove-Item ("./$keysight_visa_exec")
Print "Installer file removed"



# updating the  submodules
git submodule update --init --recursive
# if compatibility mode is enabled
if ($mode -eq "comp"){
    $VersionFile = "versions.txt"
    $Drivers = Get-Content $VersionFile | Out-String | ConvertFrom-StringData # read the driver version from versons.txt
    Print "-------------------------------------------------------"
    Print "Using these driver versions:"
    Print $Drivers
    foreach ($DriverName in $Drivers.Keys)
    {
        #change to submodule directory
        Set-Location $DriverName
        git config advice.detachedHead False #turn off detached head advice
        Print $DriverName": "
        git checkout $Drivers.$DriverName # checkout the compatible commit version
        git config advice.detachedHead True #turn back detached head advice
        Set-Location ..
        
    }
}
Print "===================Finished==================="
Print "=============================================="
Print "Virtual Enviroment active, to quit execute 'deactivate'"
Print "To reactivate, execute 'activate_enviroment.ps1' "