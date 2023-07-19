# Automated Measurement Framework

The goal of this project is to provide an open source solution for the automation of RF measurements, focused on measuring devices using Silicon Laboratories products. This enables customers of Silicon Laboratories to perform standardized measurements, while automating the repetitive steps in the process.

## Features:

- Fully automatic and repeatable measurements and tests
- Automatic and non-intrusive installation (doesn't effect local Python)
- Easy to start out with well documented examples
- Highly costumizable (fully open source)
- Easy to read and easy to process outputs (available as both Excel files and Pandas dataframes)

## Getting started:

First, it is recommended to read everything found on this page. After that, the *TxCWPower* or *RX* examples are a great way to start out with using the framework. For these scripts, you can also find detailed getting started guides in the appropriate folder. Most of the measurements needed in everyday RF development can be done using only these two examples.

There are also small examples provided for each instrument driver. You can use these to try out the basic functions provided by these submodules. 

The documentation for the classes can be found in the README files for the examples and in the code itself as comments.

## Provided examples:

### Recommended starting points:
These are examples that have good documentation and "Getting started" guides.
- **RX:** 
  - Sensitivity (BER/PER)
  - Waterfall diagram
  - RSSI sweep
  - Blocking performance
  - Automatic CTUNE calibration
- **TX_CW:** 
  - TX CW power measurement (with automatic harmonic power measurements)
- **Instrument drivers:** 
  - These can be used to test some basic functionalities implemented in the instrument drivers. It is recommended to try these if you have problems with controlling your instruments.

### Other examples:
These are more specific examples that have less documentation and thus are not that suitable for new users. However, they are great for demonstrating how parts of the framework could be used to develop your own applications.
- **Telec245:** 
  - A whole T254 certification measurement for the EFR32FG25
- **DcDc_Spurs:** 
  - DC-DC spur level measurements in TX CW mode

## Supported devices:

In terms of devices that can be tested, currently only Series 1 and 2 EFR32 devices are supported (the ones that can be used with the RAILTest application). The framework was tested during development with the following instruments (but other instruments from the same manufacturer are likely compatible, and also custom instruments can be added easily, as the framework uses SCPI commands to communicate with them):

- Anritsu MS2692A spectrum analyzer (can be used as a CW generator as well)
- Rohde&Schwarz FSV spectrum analyzer
- Keysight E3646A power supply
- Rohde&Schwarz SMBV100A signal generator
- HP E4432B signal generator

---

## Installation

---

 The Automated Measurement Framework comes with a script that is designed to automate the installation process. It contains a set of variables and functions that help the user install the required dependencies.

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

## Logger module


Every layer of this framework is equipped with a mostly pre-configured version of the official logging module. It is defined in the `/common/logger.py`. It can be imported from every folder, because it is installed as a package.

It will log everything from every driver and measurement on the set logging level( `DEBUG` is default) to the master logfile: `app.log`. Separate log files for measurements can be created, if the `logfile_name` parameter is given at initialization. 


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

# Disclaimer

Everything in this repository is provided AS IS. By downloading and using the framework, the user assumes and bears all liability emerging from the application of it.