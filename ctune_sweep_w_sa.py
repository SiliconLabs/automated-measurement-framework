from pywstk import pyRAIL
from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pywstk.pyRAIL import WSTK_RAILTest
from time import sleep
from pyspecan.pySpecAn import SpecAn
from common import logger as lg
import serial
import xlsxwriter
import numpy as np
from excel_plotter.Py_to_Excel_plotter_ctune_sweep import Py_to_Excel_plotter

board_name = 'BRD4264B'
frequency = 915e6
power_raw = 200
span = 200e3
RBW = 10e3
ctune_max = 255

specan = SpecAn("TCPIP::169.254.88.77::INSTR", auto_detect=False,logger_settings=lg.Logger.Settings(logging_level=lg.Level.INFO))
#specan.setAppSwitch("SA")
#specan.initiate()
specan.updateDisplay(on_off=True)
specan.setFrequency(frequency)
specan.setSpan(span)
specan.setRBW(RBW)
specan.setRefLevel(20)
specan.initiate()
sleep(0.2)
wstk = WSTK_RAILTest("COM3",reset=True)
#wstk.resetDevice()

workbook_name = board_name + '_CTUNE_sweep_results.xlsx'
workbook = xlsxwriter.Workbook(workbook_name)
sheet_rawdata = workbook.add_worksheet('RawData')
sheet_rawdata.write(0, 0, 'Actual Frequency [MHz]')
sheet_rawdata.write(0, 1, 'CTUNE value [decimal]')
sheet_rawdata.write(0, 2, 'Frequency Error [kHz]')

ctune_range = np.linspace(0, ctune_max, ctune_max+1, dtype=int)
#ctune_list = []
#freq_error_list = []
i = 1

wstk.receive(on_off=False, frequency_Hz=frequency, timeout_ms=1000)
sleep(0.1)
wstk.transmit(mode="CW", frequency_Hz=frequency, power_dBm=power_raw, power_format="RAW")
sleep(0.1)
wstk._driver.setTxTone(on_off=False, mode="cw")

for ctune_item in ctune_range:

    wstk._driver.setCtune(ctune_item)
    wstk._driver.setTxTone(on_off=True, mode="cw")
    sleep(0.2)
    marker_freq = specan.getMaxMarker().position
    sleep(0.1)
    
    freq_error_kHz = (marker_freq - frequency)/1e3
    wstk._driver.setTxTone(on_off=False, mode="cw")
    #freq_error_list.append(freq_error_kHz)
    #ctune_list.append(ctune_item)
    sheet_rawdata.write(i, 0, marker_freq/1e6)
    sheet_rawdata.write(i, 1, ctune_item)
    sheet_rawdata.write(i, 2, freq_error_kHz)
    i += 1

workbook.close()
#print(ctune_list)
#print(freq_error_list)

Py_to_Excel_plotter(workbook_name)

print('\nDone with measurements')