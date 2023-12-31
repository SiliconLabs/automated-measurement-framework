# RX measurements example

This example allows the user to perform various RX measurements using a signal generator. The available measurements are: 
- BER/PER sensitivity
  - This test implements a basic sensitivity measurement. The script sweeps through the given power levels until it detects a PER or BER value that is greater than the given error rate threshold. The power level where this happens will be logged as the measured sensitivity.
  - For PER measurements, a valid packet for the given PHY has to be loaded into the generator. You can find a standard RAIL packet included in this folder. 
  - All the measurements that measure PER or BER in some form (all of them here except RSSI) inherit their parameters from this measurement.
- Waterfall diagram
  - This is basically the same as a sensitivity measurement, but it doesn't stop at the error rate threshold, instead sweeps through *all* the given power levels. It can be useful when experiencing noisy behavior regarding BER/PER numbers.
- Sensitivity with frequency offset
  - This test measures sensitivity using a signal that has a frequency offset compared to the expected carrier. This offset can be sweeped, allowing the user to map out a given configuration's ability to handle frequency errors.
  - For this script, a `Plot_Bathtub` option is available. If this is set to `True`, the measurement doesn't stop at the set error rate threshold, but sweeps through all the power levels (just like with a waterfall diagram, but for every frequency offset). The output of this is a 3D HTML plot of the results. Warning: this can make the measurement very slow to complete.
- Blocking performance
  - This script first measures sensitivity (with either BER or PER, depending on the settings), then sets the useful signal's power to be a certain level higher than the result (how much higher this is can be set of course). Then, the second generator starts transmitting a CW signal and measures the power level where the BER or PER reaches a certain error rate threshold.
- RSSI sweep
  - This measurement transmits a PN9 modulated signal then measures the RSSI recorded by the DUT. The frequency of this injected signal can be sweeped.  

As these measurements are all derivatives of the Sensitivity class, we will focus on doing a basic sensitivity measurement in the "Getting started" section. All other measurement options can be easily figured out from the class documentations in this page or the code itself.

Required instruments: 

- Silicon Laboratories EFR32 with RAILTest configured (with the correcty PHY and the *"reconfigure for BER"* option set if needed)
- Signal generator (tested with Rohde&Schwarz SMBV100A and HP E4432B)
- (optional) Shielded box
- (for blocking) Other signal generator or spectrum analyzer with generator functionality (tested with Rohde&Schwarz SMBV100A, HP E4432B and Anritsu MS2692A)
- (optional) Spectrum analyzer for automatic CTUNE setting (tested with Anritsu MS2692A and Rohde&Schwarz FSV)


Manuals for tested generators:

[HP E4432B programming guide](https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf)

[ R&S SMBV100A programming guide](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/s/smbv/SMBV100A_OperatingManual_en_18.pdf)

## Getting started

Follow these steps to start measuring RX performance with the Automated Measurement Framework:

1. Install the framework by following the steps described in the README of the main folder
2. Activate the virtual environment by running the `.\activate_environment.ps1` command (if it is not already active)
3. Configure the DUT with a Railtest application 
   - It is important to configure the DUT with the actual PHY parameters that the measurement will use. If you need to test more PHYs in an automated way, you can add multiple radio configs to the RAILTest that you are using, and you can switch between them using the WSTK driver module.
   - If you are planning to do BER measurements, make sure to select the "*reconfigure for BER*" option in the radio configurator. Otherwise, make sure that this is disabled.
   - For blocking testing, an RF power combiner needs to be used to combine the blocking and useful signals.
4. Put together the physical measurement setup
   - For sensitivity measurements in general, a shielded box is recommended.
5. In the code: 
   1. Set the chip and board names (these will only be used for documenting the results)
   2. Set the COM port of the WSTK (can be found in device manager for example)
   3. Set the VISA address of the signal generator(s) and the (optional) spectrum analyzer
      - If in doubt, you can run `pyvisa-shell` in the command line and then type `list`. This brings up a list with all the instrument addresses that VISA recognizes. Then you can try opening the instruments to see if the visa connection can be established.
   4. Set the cable attenuation of the signal path (for blocking tests, this needs to be set separately for the blocker path). The script uses this to correct the actual measured values.
   5. Configure the parameters of the measurement
      - You can find all the available parameters in the `Settings` class of the chosen measurement
      - Automatic CTUNE calibration can be done by setting the appropriate variable to `True`. There are 2 options for this: using a spectrum analyzer or using a signal generator. It is of course more comfortable to use the signal generator as this option doesn't require you to change the RF connection during the measurement, but with high BW PHYs this can be very inaccurate (as this method uses RSSI as an indicator of how well the center frequency is tuned)
      - When doing PER measurements, please make sure to uncomment the appropriate block of code. For this, you also need to have a packet file in the folder (we supply a 16 byte long standard RAIL packet file with the framework).
6. Run the *rxtests_example.py* Python script from the virtual environment usin `py rxtests_example.py` in the correct folder. The output will be an excel file with all the measured raw data and output graphs.

--- 

# Available class parameters

## RX sensitivity
Measuring receiver sensitivity of the EFR32-based design.

Required instruments: 
- SiLabs EFR with RAILTest configured
- Signal Generator, currently tested with Rohde & Schwarz SMBV100A and HP E4432B generator.
- (optional) If CTUNE is done with Spectrum analyzer, then it is needed


The `Sensitivity.Settings` dataclass containing the settings, is documented below:
### Frequency Parameters

- `freq_start_hz` (int): Start frequency in Hz.
- `freq_stop_hz` (int): Stop frequency in Hz.
- `freq_num_steps` (int): Number of discrete frequency steps between stop and start values.
- `freq_list_hz` (list): Custom list of frequencies.

### Logger Settings
- `logger_settings`(Logger.Settings): Logger module settings for the measurement, imported from common
### CTUNE Parameters

- `measure_with_CTUNE_w_SA` (bool): Enable CTUNE with spectrum analyzer (more accurate). Uses a CW signal from the DUT, measuring its accurate frequency and tunes accordingly.
- `measure_with_CTUNE_w_SG` (bool): Enable CTUNE with signal generator (easier setup, faster). Uses CW signal from the generator, and measures RSSI on the DUT. While sweeping CTUNe values, it chooses Can be unreliable with wide bandwidth PHYs.

### Error rate parameters

- `err_rate_type` (str): 'BER' or 'PER', for PER the `siggen_stream_type` should be a @BIT filename like "TEMP@BIT", use \"\"
- `err_rate_threshold_percent` (float): where the sensitivity threshold is reached, different for standards

### Cable Attenuation Parameters

- `cable_attenuation_dB` (float): Total cable loss in the test setup between SigGen and DUT.

### Signal Generator Parameters
- `siggen_address` (str): VISA address of Signal Generator(SigGen), more in [PyVISA documentation](https://pyvisa.readthedocs.io/en/1.8/names.html)
- `siggen_power_start_dBm` (float): Start SigGen power in dBm, cable loss not included.
- `siggen_power_stop_dBm` (float): Stop SigGen power in dBm, cable loss not included.
- `siggen_power_steps` (int): Number of discrete SigGen power steps between stop and start values.
- `siggen_power_list_dBm` (list): Custom list of SigGen powers in dBm.
- `siggen_modulation_type` (str): Modulation type, most common values: BPSK|QPSK|OQPSK|MSK|FSK2|FSK4|FSK8. See manuals of supported generators(at the end of introduction).
- `siggen_modulation_symbolrate_sps` (float): Symbol rate of the output signal in symbols per second.
- `siggen_modulation_deviation_Hz` (float): Frequency deviation in hertz for FM types.
- `siggen_modulation_bits_per_symbol` (int): Bits per symbol, important for R&S generators, to correctly calculate transmission length
- `siggen_stream_type` (str): Data type of the output stream, values: PN9|PN11|PN15|PN20|PN23|FIX4|"<file name>"|EXT|P4|P8|P16|P32|P64. See manuals of supported generators(at the end of introduction).
- `siggen_filter_type` (str): RCOSine | COSine | GAUSs | LGAuss | CONE. See manuals of supported generators(at the end of introduction). Older instruments, like the HP only support gaussian and nygquist filter shapes.
- `siggen_filter_BbT` (float): Filter BT factor between 0 and 1.
- `siggen_custom_on` (bool): Custom mode one, for all SG functionality this should be on.
- `siggen_per_packet_filename` (str): the name of the file on this PC, that contains the binary data of the test packet.
Should be in the format of Saleae Logic analyzers .csv export.
- `siggen_per_packet_siggen_name`(str): what the name of the @BIT file will be on the generator itself
- `siggen_pattern_repeat` (str): continuous or single ( CONT or SING)
- `siggen_trigger_type` (str): KEY|BUS|EXT- triggerkey on generator, GPIB bus, or external, almost always use BUS
- `siggen_logger_settings` (Logger.Settings): Logger module settings for SG.

### Spectrum Analyzer Parameters

- `specan_address` (str): VISA address of Spectrum Analyzer,  more in [PyVISA documentation](https://pyvisa.readthedocs.io/en/1.8/names.html)
- `specan_span_hz` (int): SA span in Hz
- `specan_rbw_hz` (int): SA resolution bandwidth in Hz
- `specan_ref_level_dbm` (int): SA reference level in dBm
- `specan_detector_type` (str): SA detector type, directly passed to pySpecAn
- `specan_ref_offset` (float): SA reference offset
- `specan_logger_settings` (Logger.Settings): Logger module settings for SA.

### RAILTest Device Settings

- `wstk_com_port` (str): COM port of the RAILTest device.
- `wstk_logger_settings` (Logger.Settings): Logger module settings for WSTK.

### Test data quantities

- `ber_bytes_to_test` (int): Number of bytes to be used for one BER measurement
- `per_packets_to_test` (int): Number of packets to be used for one PER measurement
  
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

- `plot_bathtub` (bool): Plot Freq. Offset - Power - PER 3D graph, makes measurement slower, but sweeps every value, and generates html interactive plot.

- `bathtub_filename_html` (str): Name of aforementioned interactive plot, has to end with .html.

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

### Known Issues

EFR32MG1P/EFR32MG1B: MEasurement only works if the flashed RAILTest application has the `Reconfigure for BER testing` option enabled.

---
## Waterfall
Measures receiver sensitivity, just with a continuous power sweep, and plotting capabilities

Settings completely inherited from `Sensitivity`.

---