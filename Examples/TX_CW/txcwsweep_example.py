

"""
Automated Measurement Framework - TX CW measurement example

This script is intended as an example for the Automated Measurement Framework. Information about the example and the TXCWSweep class can be found in the README file
in this folder.

Tested with:
    - Keysight E3646A PSU
    - Anritsu MS2692A spectrum analyzer
    - Rohde&Schwarz FSV spectrum analyzer

"""

#################################################################################################################################################

try:
    from txcwsweep import TXCWSweep
except ModuleNotFoundError:
    # This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')
    
from txcwsweep import TXCWSweep
from common import Logger, Level

#################################################################################################################################################


sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6,915e6],   # List of fundamental frequencies to be measured
    psu_present = False,            # Set to "True" if a PSU is present in the system 
    pavdd_levels = [3.0,3.3],       # List of power supply voltages to be measured
    wstk_com_port = "COM4",         # COM port of the DUT
    specan_address = 'TCPIP::169.254.88.77::INSTR', # Address of the spectrum analyzer
    specan_span_hz = 1e6,           # SPAN setting of the spectrum analyzer
    specan_rbw_hz = 100e3,          # RBW setting of the spectrum analyzer
    specan_ref_level_dbm = 20,      # Reference level of the spectrum analyzer
    harm_order_up_to=5,             # How many harmonics to measure
    pwr_levels=[100],               # Power levels to be measured. Default format is 'raw'
    psu_address = "ASRL8::INSTR",   # Address of the PSU used
    # specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    # specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks

    # Change the logger levels to Level.DEBUG to see every command sent to the instruments
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO),
    psu_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="EFR32FG23",board_name="BRD4204D")

df = measurement.measure()

print(df.to_string())