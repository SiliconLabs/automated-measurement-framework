# Automated Measurement Framework
## Install Script

This script is designed to automate the installation process of the Automated Measurement Framework. It contains a set of variables and functions that help the user install the required dependencies.

### Requirements

- PowerShell(already found on most Windows systems)
- Installed [Git Bash for Windows](https://github.com/git-for-windows/git/releases/download/v2.40.0.windows.1/Git-2.40.0-64-bit.exe)
- SSH key [Added to Stash Profile](https://confluence.atlassian.com/display/STASH025/Adding+an+SSH+key+to+your+Stash+account+on+Windows)

### Execution

Open PowerShell and navigate to the directory containing the script. Execute the script using the command `.\install_script.ps1`.


The script performs the following actions:

1. Deletes the previous environment if it exists.
2. Clones `pyenv-win` from Github to handle Python versions.
3. Installs a separate local Python environment with the version specified in the `$local_python_version` variable using `pyenv`.
4. Creates a virtual environment using the local Python version.
5. Installs all required Python packages from the `requirements.txt` file.
6. Downloads and installs NI-VISA.
7. Downloads and installs Keysight VISA.
8. Updates the submodules
9. At the end of the script execution, the virtual environment is activated. To deactivate the environment, execute `deactivate` in the console. To reactivate the environment, execute `activate_enviroment.ps1`.


### Parameters
The script contains the following variables:

* `$local_python_dir`: A string that specifies the directory where the local Python environment will be installed. This variable should not be changed unless the `.gitignore` file is also updated.
* `$venv_path`: A string that specifies the name of the virtual environment that will be created.
* `$local_python_version`: A string that specifies the version of Python that will be installed in the local Python environment. The version must be in the format 3.x.x. The tested python version is 3.10.5
* `$keysight_visa_exec`: A string that specifies the name of the Keysight VISA installer file.
* `$keysight_visa_web_file`: A string that specifies the location of the Keysight VISA installer file on the SiLabs network.
* `$ni_visa_exec`: A string that specifies the name of the NI-VISA installer file.
* `$ni_visa_web_file`: A string that specifies the location of the NI-VISA installer file on the web.
  
---
## Measurement Scripts
---
## TX CW Sweep

Sweeps and measures basic TX parameters, like harmonic power and consumption, in CW mode.

All configurable settings for this measurement are found below, contained in the Settings subclass of TXCWSweep.

Sweepable variables can be configured using start, stop and steps parameters or by a list. If a list is not initialized, the start/stop parameters will be used. 

### Initialization
The initialization takes these input parameters:

- `settings` (Settings): A `TXCWSweep.Settings` dataclass containing all the configuration.
- `chip_name` (str): A string indicating the name of the IC being tested. This is only used in reporting.
- `board_name` (str): A string indicating the name of the board containing the IC. This is only used in reporting.
- `logfile_name` (str): A string indicating the name of a separate logfile to be created for this measurement, if desired.
- `console_logging` (bool): A boolean indicating whether to enable console logging. This is `True` by default.

The `TXCWSweep.Settings` dataclass is documented below:

### Frequency Parameters

- `freq_start_hz` (int): Start frequency
- `freq_stop_hz` (int): Stop frequency
- `freq_num_steps` (int): Number of discrete frequency steps between stop and start values
- `freq_list_hz` (list): Custom list of frequencies
- `harm_order_up_to` (int): Number of harmonics to measure, fundamental included

### Power Supply Parameters

- `psu_present` (bool): Power supply presence variable, default False, meaning internal 3.3V is used
- `psu_address` (str): VISA address of PSU, if serial is used, it is a COM port, check PyVISA documentation
- `pavdd_min` (float): Minimum supply voltage
- `pavdd_max` (float): Maximum supply voltage
- `pavdd_num_steps` (int): Number of discrete voltage steps between stop and start values
- `pavdd_levels` (list): Custom list of voltages

### Amplifier Parameters

- `min_pwr_state` (int): Maximum power setting for EFR internal amplifier
- `max_pwr_state` (int): Minimum power setting for EFR internal amplifier
- `pwr_num_steps` (int): Number of amplifier power values between stop and start values
- `pwr_levels` (list): Custom list of power values

### Spectrum Analyzer Parameters

- `specan_address` (str): VISA address of Spectrum Analyzer, can check PyVISA documentation
- `specan_span_hz` (int): SA span in Hz
- `specan_rbw_hz` (int): SA resolution bandwidth in Hz
- `specan_ref_level_dbm` (int): SA reference level in dBm
- `specan_detector_type` (str): SA detector type, directly passed to pySpecAn
- `specan_ref_offset` (float): SA reference offset

### RAILTest Device Parameters

- `wstk_com_port` (str): COM port of the RAILTest device


### Output 

To start the measurement, call the `measure()` function. Which returns a Pandas DataFrame, and generates an excel file, both containing the results.

---
## RX sensitivity
