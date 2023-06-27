"""
Automated Measurement Framework - RAILTest driver example (TX mode)

This example demonstrates TX functionality using the pyRAIL driver. It sends a pre-defined packet every second through the connected WSTK and 
radio board, using the radio configuration of the RAILTest flashed to the board.

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

#################################################################################################################################################

if __name__ == "__main__":
    data_to_tx_16 = bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    wstk = pyRAIL.WSTK_RAILTest("COM4") # Select the correct COM port of the WSTK
    wstk.transmitData(data=data_to_tx_16, frequency_Hz=2450e6, power_dBm=0, timeout_ms=2000) # This already sends one packet

    while 1:
        try:
            wstk.sendPacketInBuffer(timeout_ms=2000) # This sends the same packet multiple times
            time.sleep(1)
        except KeyboardInterrupt:
            break