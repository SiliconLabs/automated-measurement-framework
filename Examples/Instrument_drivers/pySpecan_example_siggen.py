"""
Automated Measurement Framework - Spectrum analyzer driver example (signal generator mode)

This example demonstrates the use of the signal generator features of the pySpecAn driver by transmitting a signal and then measuring it with
the same device. To test this example, please connect the output of the analyzer to the input.
The Anritsu spectrum analyzer is also implemented as a signal generator in the pySigGen module (but only for CW signals).

Tested with:
    - Anritsu MS2692A

"""

#################################################################################################################################################

# This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
try:
    from pyspecan import pySpecAn
except ModuleNotFoundError:
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

#################################################################################################################################################

from pyspecan import pySpecAn
from common import Logger, Level
from time import sleep

# Set the spectrum analyzer address
specan = pySpecAn.SpecAn("TCPIP::169.254.88.77::INSTR", logger_settings=Logger.Settings(logging_level=Level.INFO))

freq = 470e6
pwr = -20

# Set the signal generator parameters

specan.setAppSwitch("SG") #"SA" for spectrum analyzer, "SG" for signal generator, "PN" for phase noise measurements

print("SigGen setings:")
specan.setSigGenFreq_Hz(freq)
print(specan.getSigGenFreq_Hz())
specan.setSigGenPower_dBm(pwr)
print(specan.getSigGenPower_dBm())
specan.setSigGenOutput_toggle(on_off=True) # Enable the generator output
print(specan.getSigGenOutput_toggle())
sleep(1)

# Set the spectrum analyzer parameters
specan.setAppSwitch("SA")
specan.updateDisplay(on_off=True)
specan.setFrequency(freq)
specan.setSpan(100e3)
specan.setRBW(1000.0)
specan.setRefLevel(pwr+10)
specan.initiate()
marker = specan.getMaxMarker() # Measure
print("\nMeasured SA results:")
print(marker)
sleep(1)

# Phase noise measurement mode
specan.setAppSwitch("PN")
specan.setFrequency(freq)
specan.setRBW(1000.0)
specan.setRefLevel(pwr+10)
sleep(3)

# Go back to signal generator to turn off the output
specan.setAppSwitch("SG")
specan.setSigGenOutput_toggle(on_off=False)
print(specan.getSigGenOutput_toggle()) # Turn off generator output

specan.setAppSwitch("SA")