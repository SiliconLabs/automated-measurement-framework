"""
Automated Measurement Framework - RAILTest driver example (TX mode)

This examples demonstrates RX functionality using the pyRAIL driver. It sets the connected WSTK and radio board to RX mode then prints to the
console whenever it receives anything. 

For receiving packages, please make sure that the "reconfigure for BER" option is not checked in the radio configurator.

"""

#################################################################################################################################################

# This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
try:
    from pywstk import pyRAIL
except ModuleNotFoundError:
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

#################################################################################################################################################

from pywstk import pyRAIL
import time
from multiprocessing import Queue

if __name__ == "__main__":
    wstk = pyRAIL.WSTK_RAILTest("COM7") # Select the COM port of the WSTK

    while 1:
        try:
            rx_queue = wstk.receive(on_off=True,frequency_Hz = 2450e6,timeout_ms=10000) # Set the radio to receive mode
            time.sleep(1)
            while rx_queue.qsize(): 
                rx_str = rx_queue.get()
                hexstr_to_int_func = lambda x: int(x,16)
                rx_bytes = bytes(map(hexstr_to_int_func,rx_str.split()))
                print("recieve q:",rx_bytes)
        except KeyboardInterrupt:
            break