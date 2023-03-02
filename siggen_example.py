from pysiggen.pySigGen import SigGen
from pysiggen.pySigGen import SigGenSettings
from time import sleep

siggen = SigGen("GPIB0::5::INSTR") #this can change, run pyvisa-shell list command in cmd to find current address

siggen.getError()
settings = SigGenSettings()

# Define signal and stream properties
settings.frequency_Hz = 868e6
settings.amplitude_dBm = -107
settings.modulation.type = "FSK2" #see all modulation abbrevations at page 299 of https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.modulation.symbolrate_sps = 100e3
settings.modulation.deviation_Hz = 50e3
settings.rf_on = True
settings.mod_on = True
settings.stream_type = "PN9" #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.filter_type = "Gaussian" #Gaussian or Nyquist
settings.filter_BbT = 0.5
settings.custom_on = True
#################

siggen.setStream(settings)
print(settings)

