"""
Automated Measurement Framework - Signal generator driver example (stream mode)

This example demonstrates the use of the pySiggen driver through sending out a stream of bits using a set modulation.

Tested with:
    - HP E4432B

"""

#################################################################################################################################################

# This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
try:
    from pysiggen import pySigGen
except ModuleNotFoundError:
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

#################################################################################################################################################

from pysiggen import pySigGen
from time import sleep

'''

Keysight E4432B manual:
https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf

R&S SMBV100A manual:
https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/s/smu200a_1/SMU200A_OperatingManual_en_19.pdf

'''
siggen = pySigGen.SigGen("GPIB1::5::INSTR") #this can change, run pyvisa-shell list command in cmd to find current address

siggen.getError()
settings = pySigGen.SigGenSettings()

# Define signal and stream properties
settings.frequency_Hz = 915e6                       # Output center frequency
settings.amplitude_dBm = -10                        # Output power
settings.modulation.type = "FSK2"                   # See all modulation abbrevations in manuals
settings.modulation.symbolrate_sps = 2000e3         # FSK symbol rate
settings.modulation.deviation_Hz = 500e3            # FSK deviation
settings.rf_on = True                               # Turn on RF output
settings.mod_on = True                              # Turn on modulation
settings.stream_type = "PN9"                        # For EFR BER measurements, always use PN9
settings.filter_type = "GAUS"                       # Check manual for generators, GAUS is for gaussian
settings.filter_BbT = 0.5                           # BT parameter of the filter in the transmitter
settings.custom_on = True                           # This should always be 'True'
#################

siggen.reset()
siggen.setStream(settings)