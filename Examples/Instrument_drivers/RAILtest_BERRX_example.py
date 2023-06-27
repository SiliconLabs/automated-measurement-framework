"""
Automated Measurement Framework - RAILTest driver example (BER measurement)

This example creates a basic BER measurement setup between two WSTKs and radio boards. 
The boards have to be configured for the same PHY in RAILTest, and the receiver board has to have the "reconfigure for BER" option selected in
the radio configurator.

"""

#################################################################################################################################################

try:
    from pywstk import pyRAIL
except ModuleNotFoundError:
    # This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')
    from pywstk import pyRAIL

import time
from common import Logger, Level

#################################################################################################################################################

if __name__ == "__main__":

    # If more information is needed about the sent/received messages, change this to Level.DEBUG
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)

    wstk_rx = pyRAIL.WSTK_RAILTest("COM4",reset=True, logger_settings=wstk_logger_settings) # Select COM ports for RX and TX 
    wstk_tx = pyRAIL.WSTK_RAILTest("COM7",reset=True, logger_settings=wstk_logger_settings)

    frequency = 2450e6
    # Transmit in PN9 stream mode
    wstk_tx.transmit(mode="PN9",frequency_Hz=frequency,power_dBm=0)

    # Blocking BER measurement function with timeout, syncs on PN9
    # Can only be used with BER configured RAILtest
    ber_percent,done_percent,rssi = wstk_rx.measureBer(nbytes=100000,timeout_ms=10000,frequency_Hz=frequency) 

    print("BER: ", ber_percent,"%, Done percent: ", done_percent, "%")
    print("Press Ctrl-C to quit!")
    
    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            wstk_rx.stop()
            wstk_tx.stop()
            break