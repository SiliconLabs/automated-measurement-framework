from pyspecan.pySpecAn import SpecAn
from common import logger as lg
from time import sleep

specan = SpecAn("TCPIP::169.254.88.77::INSTR", auto_detect=False,logger_settings=lg.Logger.Settings(logging_level=lg.Level.INFO))

freq = 870e6
pwr = -30.5

#specan.reset()
specan.setAppSwitch("SG") #"SA" for spectrum analyzer, "SG" for signal generator, "PN" for phase noise measurements
#specan.initiate()
print("SigGen setings:")
specan.setSigGenFreq_Hz(freq)
print(specan.getSigGenFreq_Hz())
specan.setSigGenPower_dBm(pwr)
print(specan.getSigGenPower_dBm())
specan.setSigGenOutput_toggle(on_off=True)
print(specan.getSigGenOutput_toggle())
sleep(1)

specan.setAppSwitch("SA")
specan.updateDisplay(on_off=True)
specan.setFrequency(freq)
specan.setSpan(100e3)
specan.setRBW(1000.0)
specan.setRefLevel(pwr+10)
specan.initiate()
marker = specan.getMaxMarker()
print("\nMeasured SA results:")
print(marker)
sleep(1)

specan.setAppSwitch("PN")
specan.setFrequency(freq)
specan.setRBW(1000.0)
specan.setRefLevel(pwr+10)
sleep(3)

specan.setAppSwitch("SG")
specan.setSigGenOutput_toggle(on_off=False)
print(specan.getSigGenOutput_toggle())