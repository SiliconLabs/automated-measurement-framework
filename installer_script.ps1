param (
    [string]$mode = "fresh"
)

$local_python_dir = "local_python_env"
$venv_path = "venv"
$local_python_version = "3.10.5"

$NiVisaExec = "ni-visa_19.5_online_repack3.exe" #NI-VISA installer file name, can be switched to a newer/older one
$WebFileNiVisa = "https://download.ni.com/support/nipkg/products/ni-v/ni-visa/19.5/online/ni-visa_19.5_online_repack3.exe" 

Write-Output "Automated Measurement Framework Install Script"
Write-Output "=============================================="
Write-Output " "
Write-Output "----------------------------------------------"
Write-Output " "
#mkdir $local_python_dir
#Set-Location $local_python_dir

if((Test-Path "$local_python_dir")){
    Write-Output "Removing previous enviroment"
    Remove-Item -Force -Recurse -Path ($local_python_dir)
}

Write-Output "Fetching pyenv python enviroment manager"
git clone https://github.com/pyenv-win/pyenv-win.git ".\$local_python_dir\pyenv-win"

$PyEnvCmd = "./$local_python_dir/pyenv-win/pyenv-win/bin/pyenv.bat"
iex "$PyEnvCmd versions"
iex "$PyEnvCmd install $local_python_version"
$LocalPython = "./$local_python_dir\pyenv-win\pyenv-win\versions\$local_python_version\python"
Write-Output "Creating virtual enviroment"
$VenvPath = "venv"
iex "$LocalPython -m venv ./$local_python_dir/$venv_path"
iex "./$local_python_dir/$venv_path/Scripts/activate"
Write-Output "Activating virtual enviroment"

Write-Output "Installing required Python Packages"
iex "pip install -r requirements.txt"
Write-Output "Finished installing Python Packages"
Write-Output "Fetching NI-VISA from the web...."


#NI-VISA link,must contain .exe at the end can be switched to newer/older one
 
Clear-Host
 
(New-Object System.Net.WebClient).DownloadFile($WebFileNiVisa,"$env:HOME\$NiVisaExec")
Start-Process ("$env:Home\$NiVisaExec")
Read-Host "If You Completed the VISA Installer (or to skip) Press Enter"
Remove-Item ("$env:Home\$NiVisaExec")




git submodule update --init --recursive
# if compatibility mode is enabled
if ($mode -eq "comp"){
    $VersionFile = "versions.txt"
    $Drivers = Get-Content $VersionFile | Out-String | ConvertFrom-StringData # read the driver version from versons.txt
    Write-Output "Using these driver versions:"
    Write-Output $Drivers
    foreach ($DriverName in $Drivers.Keys)
    {
        #change to submodule directory
        Set-Location $DriverName
        git config advice.detachedHead False #turn off detached head advice
        Write-Output $DriverName": "
        git checkout $Drivers.$DriverName # checkout the compatible commit version
        git config advice.detachedHead True #turn back detached head advice
        Set-Location ..
        
    }
}
Write-Output "===================Finished==================="
Write-Output "=============================================="
Write-Output "Virtual Enviroment active, to quit execute 'deactivate'"
Write-Output "To reactivate, execute '.\$local_python_dir\$venv_path\Scripts\activate' "