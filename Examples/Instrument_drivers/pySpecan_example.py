"""
Automated Measurement Framework - Spectrum analyzer driver example

This example demonstrates the use of the pySpecAn driver by setting the basic parameters and getting a max marker measurement value 
from the instrument.

Tested with:

"""

#################################################################################################################################################

try:
    from pyspecan import pySpecAn
except ModuleNotFoundError:
    # This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

from pyspecan import pySpecAn
from common import Logger, Level

#################################################################################################################################################

# If you need more data about the sent/received SCPI messages, change this to Level.DEBUG
specan_logger_settings = Logger.Settings(logging_level=Level.INFO) 

# Set the spectrum analyzer address
specan = pySpecAn.SpecAn("TCPIP::169.254.0.3::INSTR", auto_detect=True, logger_settings=specan_logger_settings)
specan.updateDisplay(on_off=True)
specan.setFrequency(433.965e6)
specan.setSpan(50e3)
specan.setRBW(10000.0)
specan.setRefLevel(-60.0)
# Auto-peak detector on Rohde&Schwarz instruments
specan.setDetector("APE") # Please see the device manual for available detector types
# specan.setDetector("NORM") # Anritsu: Simultaneous detection for positive and negative peaks
specan.setTraceStorageMode("OFF") # Please see the device manual for available trace storage modes
specan.initiate()
marker = specan.getMaxMarker() # Get the measurement result
print(marker)
