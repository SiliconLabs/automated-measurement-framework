"""
Automated Measurement Framework - Signal generator driver example (packet mode)

This example demonstrates the use of the pySiggen driver through sending out pre-defined packets using a set modulation.
The file path for the packet data should always be set before running.

Tested with:

"""

#################################################################################################################################################

try:
    from pysiggen import pySigGen
except ModuleNotFoundError:
    # This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

from pysiggen import pySigGen
from time import sleep

#################################################################################################################################################

'''

Keysight E4432B manual:
https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf

R&S SMBV100A manual:
https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/s/smu200a_1/SMU200A_OperatingManual_en_19.pdf

'''

siggen = pySigGen.SigGen("GPIB2::28::INSTR") # This can change, run pyvisa-shell list command in cmd to find current address

siggen.getError()
settings = pySigGen.SigGenSettings()

# Define signal and stream properties
settings.frequency_Hz = 915e6                                       # Output center frequency
settings.amplitude_dBm = -10                                        # Output power
settings.modulation.type = "FSK2"                                   # See all modulation abbrevations in manuals
settings.modulation.symbolrate_sps = 2000e3                         # FSK symbol rate
settings.modulation.deviation_Hz = 500e3                            # FSK deviation
settings.rf_on = True                                               # Turn on RF output
settings.mod_on = True                                              # Turn on modulation
settings.stream_type = "\"TEMP@BIT\""                               # @BIT format necessary
settings.pattern_repeat = "SINGle"                                  # On trigger, only send a single packet
settings.filter_type = "GAUS"                                       # Check manual for generators, GAUS is for gaussian
settings.filter_BbT = 0.5                                           # BT parameter of the filter in the transmitter
settings.custom_on = True                                           # This should always be 'True'
settings.per_packet_filename = "packets/std_rail_packet.csv"        # File path for the packet data
settings.per_packet_siggen_name = "TEMP"
#################

siggen.reset()
siggen.setStream(settings)
siggen.sendTrigger(100,delay=0.01)
siggen.getError()


