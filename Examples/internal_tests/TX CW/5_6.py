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


# Test 5
sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6],
    psu_present = False,
    pavdd_levels = [3.0,3.3],
    wstk_com_port = "COM10",
    specan_address = 'TCPIP::169.254.0.3::INSTR',
    specan_span_hz = 1e6,
    specan_rbw_hz = 100e3,
    specan_ref_level_dbm = 25,
    harm_order_up_to=3,
    pwr_levels=[200],
    psu_address = "wrong address", 
    specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    # specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="5",board_name="5")

df = measurement.measure()

print(df.to_string())

# Test 6
sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6],
    psu_present = False,
    pavdd_levels = [3.0,3.3],
    wstk_com_port = "COM10",
    specan_address = 'TCPIP::169.254.0.3::INSTR',
    specan_span_hz = 1e6,
    specan_rbw_hz = 1e3,
    specan_ref_level_dbm = 25,
    harm_order_up_to=3,
    pwr_levels=[200],
    psu_address = "wrong address", 
    specan_detector_type = "APE" , # Auto peak for Rohde&Schwarz instruments
    # specan_detector_type= "NORM", # Anritsu: Simultaneous detection for positive and negative peaks
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

measurement = TXCWSweep(settings=sweep_settings,chip_name="6",board_name="6")

df = measurement.measure()

print(df.to_string())
