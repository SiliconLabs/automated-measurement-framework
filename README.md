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

## Logger module


Every layer of this framework is equipped with a mostly pre-configured version of the official logging module. It is defined in the `/common/logger.py`. It can be imported from every folder, because it is installed as a package.

It will log everything from every driver and measurement on the set logging level( `DEBUG` is default) to the master logfile: `app.log`. Separate log files for measurements can be created, if the `logfile_name` parameter is given at initialization. 

---
## Measurement Scripts
---

## Initialization of measurement scripts

The initialization takes these input parameters:

- `settings` (Settings): A `.Settings` subclass of the measurement, a dataclass containing all the configuration.
- `chip_name` (str): A string indicating the name of the IC being tested. This is only used in reporting.
- `board_name` (str): A string indicating the name of the board containing the IC. This is only used in reporting.
- `logfile_name` (str): A string indicating the name of a separate logfile to be created for this measurement, if desired.
- `console_logging` (bool): A boolean indicating whether to enable console logging. This is `True` by default.
### Output 

To start a measurement, call the `measure()` function. Which returns a Pandas DataFrame, and generates an excel file, both containing the results.

### Common settings

All configurable settings for the measurements are  contained in the Settings subclass.

Sweepable variables can be configured using start, stop and steps parameters or by a list. If a list is not initialized, the start/stop parameters will be used. 

---

## Troubleshoot and add new measurements


Not all instruments are created equal, so driver compatibility issues can rise while executing the measurements with new instruments. 

It supposed to be easy to add new instrument compatibility to the drivers.

All the instrument drivers like pySpecan,pySigGen and pyPSU have a generic class, which has the SCPI interface configuration and all the ( hopefully standard) common functions implemented. If a new instrument needs new or changed functions just inherit a new class from the Generic type:
```
class NewSpecAn(GenericSpecAn):

    def setDivision(self,div_db):
        self.command("DISP:TRAC:Y:MODE ABS ")
        self.command("DISP:TRAC:Y:RPOS 100PCT")
        self.command("DISP:TRAC:Y " + str(div_db*10)+"dB")

``` 
The example above is for a new spectrum analyzer with the setDivision function overwritten.

All the instrument drivers use the command function to send SCPI instructions, this should be used for new instruments.
The SCPI commands for an instrument can be found in either its datasheet or a separate guide/app note listing all the possible parameters.

The most common errors that can come up are:

### PyVISA Errors
 `Insufficient location information or the device or resource is not present in the system`: 

No communication can be done with the instrument. Usually, this means the instrument address is wrong. If using ethernet, the IP can be checked on the instruments setup page. If USB/Serial is used, just check COM ports in a serial terminal or in device manager, to see if your device's address is correct.

If the IP address is correct check if you can ping the address from the host computer, if not check adapter settings on the PC and turn firewall off on the instrument ( on R&s instruments this is especially relevant).

To check if SCPI communication is working, type `pyvisa-shell` into a terminal, then `open TCPIP::169.254.88.77::INSTR (your instrument's address)`, if the instrument opens, type `*IDN?`. The answer should be the brand and model ID of the isntrument. If it is, then the working of the SCPI interface is confirmed. 

### SCPI Errors

Most common SCPI errors, these usually rise when new instruments are added to the drivers. 

- `113, "Undefined header"` : This means that some parts of the command are wrong, one of the headers, the some word between the double dots, is non-existent on the instrument, or there is a missing space between the command and its parameter value. Check the instruments manual more thoroughly!

- ` 410, "Query INTERRUPTED"` : The driver did not leave enough time for the instrument to answer or did not read the answer to the query. In the first case, this is usually because of too fast instrument polling, but most likely the cause is a slow interface like RS-232. Increase the query delay or switch to a faster interface (anything but RS-232). Not having the correct termination character can also cause this error, set it at the VISA init, ot on the instrument itself.

- `420, "Query UNTERMINATED"` : Not having the correct termination character can also cause this error too. Or sending an incorrect query can generate this. 

Check [Tektronix's write-up]( https://www.tek.com/en/documents/application-note/eliminating-common-scpi-errors) for a more verbose guide.

---
## TX CW Sweep

Sweeps and measures basic TX parameters, like harmonic power and consumption, in CW mode.



The `TXCWSweep.Settings` dataclass containing the settings, is documented below:

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


---
## RX sensitivity
Measuring receiver sensitivity of the EFR32-based design.

Required instruments: 
- SiLabs EFR with RAILTest configured
- Signal Generator, currently tested with HP E4432B generator.
- (optional) If CTUNE is done with Spectrum analyzer, then it is needed

The `Sensitivity.Settings` dataclass containing the settings, is documented below:
### Frequency Parameters

- `freq_start_hz` (int): Start frequency in Hz.
- `freq_stop_hz` (int): Stop frequency in Hz.
- `freq_num_steps` (int): Number of discrete frequency steps between stop and start values.
- `freq_list_hz` (list): Custom list of frequencies.

### CTUNE Parameters

- `measure_with_CTUNE_w_SA` (bool): Enable CTUNE with spectrum analyzer (more accurate).
- `measure_with_CTUNE_w_SG` (bool): Enable CTUNE with signal generator (easier setup, faster).

### Error rate parameters

- `err_rate_type` (str): 'BER' or 'PER', for PER the `siggen_stream_type` should be a @BIT filename like "TEMP@BIT", use \"\"
- `err_rate_threshold_percent` (float): where the sensitivity threshold is reached, different for standards

### Cable Attenuation Parameters

- `cable_attenuation_dB` (float): Total cable loss in the test setup between SigGen and DUT.

### Signal Generator Parameters

- `siggen_power_start_dBm` (float): Start SigGen power in dBm, cable loss not included.
- `siggen_power_stop_dBm` (float): Stop SigGen power in dBm, cable loss not included.
- `siggen_power_steps` (int): Number of discrete SigGen power steps between stop and start values.
- `siggen_power_list_dBm` (list): Custom list of SigGen powers in dBm.
- `siggen_modulation_type` (str): Modulation type, most common values: BPSK|QPSK|OQPSK|MSK|FSK2|FSK4|FSK8. See all modulation abbrevations at page 299 of [Keysight programming guide](https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf).
- `siggen_modulation_symbolrate_sps` (float): Symbol rate of the output signal in symbols per second, minimum :47.684 sps, max: 12.500000 Msps.
- `siggen_modulation_deviation_Hz` (float): Frequency deviation in hertz for FM types.
- `siggen_stream_type` (str): Data type of the output stream, values: PN9|PN11|PN15|PN20|PN23|FIX4|"<file name>"|EXT|P4|P8|P16|P32|P64. See all documentation for stream modes by searching for "RADio:CUSTom:DATA" in [Keysight programming guide](https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf).
- `siggen_filter_type` (str): "Gaussian" or "Nyquist".
- `siggen_filter_BbT` (float): Filter BT factor between 0 and 1.
- `siggen_custom_on` (bool): Custom mode one, for all SG functionality this should be on.
- `siggen_per_packet_filename`: the name of the file on this PC, that contains the binary data of the test packet
                                                Should be in the format of Saleae Logic analyzers csv export
- `siggen_per_packet_siggen_name`(str): what the name of the @BIT file will be on the generator itself
- `siggen_pattern_repeat` (str): continuous or single ( CONT or SING)
- `siggen_trigger_type` (str): KEY|BUS|EXT- triggerkey on generator, GPIB bus, or external, almost always use BUS
- `siggen_logger_settings` (Logger.Settings): Logger module settings for SG.

### Spectrum Analyzer Parameters

- `specan_address` (str): VISA address of Spectrum Analyzer, can check PyVISA documentation
- `specan_span_hz` (int): SA span in Hz
- `specan_rbw_hz` (int): SA resolution bandwidth in Hz
- `specan_ref_level_dbm` (int): SA reference level in dBm
- `specan_detector_type` (str): SA detector type, directly passed to pySpecAn
- `specan_ref_offset` (float): SA reference offset
- `specan_logger_settings` (Logger.Settings): Logger module settings for SA.

### RAILTest Device Settings

- `wstk_com_port`: COM port of the RAILTest device.
- `wstk_logger_settings` (Logger.Settings): Logger module settings for WSTK.

---

## Frequency Offset Sensitivity
Measuring receiver sensitivity to frequency offset of the EFR32-based design.

Subclass of `Sensitivity`, so all the parameters from before are inherited.

The `FreqOffset_Sensitivity.Settings` dataclass containing the settings, is documented below:

### Frequency Offset Sweep Parameters
- `freq_offset_start_Hz` (int): Frequency offset stop value in Hz
- `freq_offset_stop_Hz` (int): Frequency offset stop value in Hz
- `freq_offset_steps` (int): Frequency offset step values in Hz
- `freq_offset_list_Hz` (list): Discrete frequency list option

- `freq_offset_logger_settings` (Logger.Settings): Logger module settings for frequency offset measurement.

---

## Blocking
Measuring receiver blocking on different frequencies of the EFR32-based design.

Subclass of `Sensitivity`, so all the parameters from it are inherited.

The `FreqOffset_Sensitivity.Settings` dataclass containing the settings, is documented below:

### Blocker Frequency Parameters
- `blocker_offset_start_freq_Hz` (int): Blocker frequency offset start value in Hz
- `blocker_offset_stop_freq_Hz` (int): Blocker frequency offset stop value in Hz
- `blocker_offset_freq_steps` (int): Blocker frequency offset step values
- `blocker_offset_freq_list_Hz` (list): Blocker frequency discrete list option
### Blocker Power Parameters
- `blocker_cable_attenuation_dB` (float):  Attenuation from the blocker generator to the DUT, in dB

- `blocker_start_power_dBm` (float): Blocker start power value in dBm, without the cable attenuation
- `blocker_stop_power_dBm` (float): Blocker stop power value in dBm, without the cable attenuation
- `blocker_power_steps` (int): Blocker power value steps 
- `blocker_power_list_dBm` (list): Blocker power discrete list option

- `blocker_logger_settings` (`Logger.Settings`): Logger module settings for blocking measurement

---

## RSSI Sweep
Measuring receiver RSSI metering accuracy on different frequencies of the EFR32-based design.

Subclass of `Sensitivity`, so all the parameters from it are inherited.

The `RSSI_Sweep.Settings` dataclass containing the settings, is documented below:
### Signal Generator Parameters

- `siggen_freq_start_Hz` (int): SG frequency start value in Hz
- `siggen_freq_stop_Hz` (int): SG frequency stop value in Hz
- `siggen_freq_steps` (int): SG frequency step values
- `siggen_freq_steps` (list): Blocker frequency discrete list option

---
## Waterfall
Measures receiver sensitivity, just with a continuous power sweep and plotting capabilities

Settings completely inherited from `Sensitivity`.

---
        

