from pywstk import pyRAIL
from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pywstk.pyRAIL import WSTK_RAILTest
from time import sleep
from pysiggen.pySigGen import SigGen
from pysiggen.pySigGen import SigGenSettings
from common import logger as lg
import serial
import xlsxwriter
import numpy as np
from excel_plotter.Py_to_Excel_plotter_rssi_sweep import Py_to_Excel_plotter

# RSSI vs input power/frequency sweep while having the radio chip tuned to a fixed frequency channel
board_name = 'BRD4264B'
#ctune = 91
freq_radio_chip = 902e6

SG_freq_min = 868e6
SG_freq_max = 928e6
SG_freq_steps = 31
SG_freq_list = np.linspace(SG_freq_min, SG_freq_max, SG_freq_steps, dtype=float)

SG_power_max = 0
SG_power_min = -120
SG_power_steps = 13
SG_power_list = np.linspace(SG_power_min, SG_power_max, SG_power_steps, dtype=float)

siggen = SigGen("GPIB0::5::INSTR") #this can change, run pyvisa-shell list command in cmd to find current address
siggen.getError()
settings = SigGenSettings()
settings.frequency_Hz = freq_radio_chip
settings.amplitude_dBm = -50
settings.modulation.type = "FSK2" #see all modulation abbrevations at page 299 of https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.modulation.symbolrate_sps = 100e3
settings.modulation.deviation_Hz = 50e3
settings.rf_on = True
settings.mod_on = False
settings.stream_type = "PN9" #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.filter_type = "Gaussian" #Gaussian or Nyquist
settings.filter_BbT = 0.5
settings.custom_on = True
siggen.setStream(settings)
#print(settings)
sleep(0.2)
wstk = WSTK_RAILTest("COM3",reset=True)
#wstk.resetDevice()

workbook_name = board_name + '_' + str(freq_radio_chip/1e6) + 'MHz' + '_RSSI_sweep_results.xlsx'
workbook = xlsxwriter.Workbook(workbook_name)
sheet_rawdata = workbook.add_worksheet('RawData')
sheet_rawdata.write(0, 0, 'Frequency [MHz]')
sheet_rawdata.write(0, 1, 'SigGen Power [dBm]')
sheet_rawdata.write(0, 2, 'RSSI')
i = 1

wstk.receive(on_off=True, frequency_Hz=freq_radio_chip, timeout_ms=1000)
sleep(0.2)
#wstk._driver.setCtune(ctune)
wstk._driver.rx(True)

for freq in SG_freq_list:

    siggen.setFrequency(freq)

    for power in SG_power_list:
        siggen.setAmplitude(power)
        sleep(0.2)
        rssi = wstk.readRSSI()
        sleep(0.2)

        sheet_rawdata.write(i, 0, freq/1e6)
        sheet_rawdata.write(i, 1, power)
        sheet_rawdata.write(i, 2, rssi)
        i += 1

#siggen.toggleModulation(False)
siggen.toggleRFOut(False)
wstk._driver.rx(False)

workbook.close()
Py_to_Excel_plotter(workbook_name)

print('\nDone with measurements')