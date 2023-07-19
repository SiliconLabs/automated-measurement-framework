

"""
Automated Measurement Framework - TX CW measurement example

This script is intended as an example for the Automated Measurement Framework. Information about the example and the TXCWSweep class can be found in the README file
in this folder.

Tested with:
    - Keysight E3646A PSU
    - Anritsu MS2692A spectrum analyzer

"""

#################################################################################################################################################

try:
    from txcwsweep import TXCWSweep
except ModuleNotFoundError:
    # This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../../')
    
from txcwsweep import TXCWSweep
from common import Logger, Level
import os

#################################################################################################################################################

# Test 1
sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6],
    psu_present = False,
    pavdd_levels = [3.0,3.3],
    wstk_com_port = "COM10",
    specan_address = 'TCPIP::169.254.88.77::INSTR',
    specan_span_hz = 1e6,
    specan_rbw_hz = 100e3,
    specan_ref_level_dbm = 25,
    harm_order_up_to=3,
    pwr_levels=[200],
    psu_address = "wrong address", 
    # specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="1",board_name="1")

df = measurement.measure()

print(df.to_string())

# Test 2
sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6],
    psu_present = False,
    pavdd_levels = [3.0,3.3],
    wstk_com_port = "COM10",
    specan_address = 'TCPIP::169.254.88.77::INSTR',
    specan_span_hz = 1e6,
    specan_rbw_hz = 1e3,
    specan_ref_level_dbm = 25,
    harm_order_up_to=3,
    pwr_levels=[200],
    psu_address = "wrong address", 
    # specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="2",board_name="2")

df = measurement.measure()

print(df.to_string())

# Test 3
sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6, 915e6],
    psu_present = True,
    pavdd_levels = [3.0,3.3],
    wstk_com_port = "COM10",
    specan_address = 'TCPIP::169.254.88.77::INSTR',
    specan_span_hz = 1e6,
    specan_rbw_hz = 100e3,
    specan_ref_level_dbm = 25,
    harm_order_up_to=3,
    pwr_levels=[100,200],
    psu_address = "ASRL8::INSTR", 
    # specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO),
    psu_logger_settings= Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="3",board_name="3")

df = measurement.measure()

print(df.to_string())

# Test 4
sweep_settings = TXCWSweep.Settings(
    freq_start_hz=868e6,
    freq_stop_hz=915e6,
    freq_num_steps=3,
    psu_present = True,
    pavdd_min=3.0,
    pavdd_max=3.3,
    pavdd_num_steps=3,
    wstk_com_port = "COM10",
    specan_address = 'TCPIP::169.254.88.77::INSTR',
    specan_span_hz = 1e6,
    specan_rbw_hz = 100e3,
    specan_ref_level_dbm = 25,
    harm_order_up_to=3,
    min_pwr_state=100,
    max_pwr_state=200,
    pwr_num_steps=3,
    psu_address = "ASRL8::INSTR", 
    # specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO),
    psu_logger_settings= Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="4",board_name="4")

df = measurement.measure()

del measurement

print(df.to_string())
