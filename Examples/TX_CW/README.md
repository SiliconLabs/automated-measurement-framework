# TX CW Sweep example

This example allows the user to perform CW output power measurements (on both the fundamental frequencies and harmonics) while sweeping parameters such as frequency, PA power, or power supply voltage.  This measurement currently doesn't take cable attenuation into consideration, so the user has to account for it after the measurement is done.

Required instruments: 

- Silicon Laboratories EFR32 with RAILTest configured
- Spectrum analyzer (the example was tested with ... and ...)
- (optional) Power supply (the example was tested with ... )

## Getting started

Follow these steps to start measuring CW TX power with the Automated Measurement Framework:

1. Install the framework by following the steps described in the README of the main folder
2. Activate the virtual environment by running the `activate_environment` script from PowerShell
3. Configure the DUT with a Railtest application. 
   - Because we are using CW signals here, this configuration doesn't matter much (as both TX power and frequency can be controlled from the framework)
4. Put together the physical measurement setup. 
   - If an external power supply is used, check that the VMCU of the radio board is disconnected from the WSTK.
5. In the code: 
   1. Set the chip and board names (these will only be used for documenting the results)
   2. Set the COM port of the WSTK (can be found in device manager for example)
   3. Set the VISA address of the spectrum analyzer and the (optional) power supply
      - In the example, we connected through an ethernet cable to an Anritsu spectrum analyzer and through a USB cable to a .... power supply.
      - If in doubt, you can run `pyvisa-shell` in the command line and then type `list`. This brings up a list with all the instrument addresses that VISA recognizes.
   4. Configure the parameters of the TX sweep
      - Measurement parameters (frequencies, supply voltage levels, numbers of harmonics)
      - Spectrum analyzer parameters (span, RBW): this is important to think through for higher frequency harmonics!
      - You can find a detailed list of all the available parameters below.
      - If no power supply is used, make sure to set `psu_present` to `False`
6. Run the *txcwsweep_example.py* Python script from the virtual environment using `py txcwspweep_example.py` in the correct folder. The output will be an excel file with all the measured raw data and output graphs.


---

## TX CW Sweep class

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
