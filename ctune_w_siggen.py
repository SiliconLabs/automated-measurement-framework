from pywstk import pyRAIL
from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pywstk.pyRAIL import WSTK_RAILTest
from time import sleep
from pysiggen.pySigGen import SigGen
from pysiggen.pySigGen import SigGenSettings
import serial
import numpy as np

def ctune_sg(frequency:float, ctune_initial:int, ctune_min:int, ctune_max:int, data_rate:float, deviation:float)->float:

    siggen = SigGen("GPIB0::5::INSTR")     #this can change, run pyvisa-shell list command in cmd to find current address
    #siggen.getError()
    settings = SigGenSettings()
    settings.frequency_Hz = frequency
    settings.amplitude_dBm = -30
    settings.modulation.type = "FSK2"               #see all modulation abbrevations at page 299 of https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
    settings.modulation.symbolrate_sps = data_rate
    settings.modulation.deviation_Hz = deviation
    settings.rf_on = True
    settings.mod_on = True
    settings.stream_type = "PN9"                    #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
    settings.filter_type = "Gaussian"               #Gaussian or Nyquist
    settings.filter_BbT = 0.5
    settings.custom_on = True
    siggen.setStream(settings)
    #print(settings)

    #ctune_min = 0
    #ctune_max = 255

    wstk = WSTK_RAILTest("COM3",reset=True)
    #wstk.resetDevice()
    wstk.receive(on_off=True, frequency_Hz=frequency, timeout_ms=1000)
    sleep(0.1)
    wstk._driver.rx(False)
    wstk._driver.setCtune(ctune_initial)
    wstk._driver.rx(True)
    RSSI_max = wstk.readRSSI()
    ctuned = ctune_initial
    #ctuned = wstk._driver.getCtune()
    ctune_range = np.linspace(ctune_min, ctune_max, ctune_max-ctune_min+1, dtype=int)
    
    for ctune_item in ctune_range:
        ctune_actual = ctune_item
        wstk._driver.rx(False)
        wstk._driver.setCtune(ctune_actual)
        wstk._driver.rx(True)
        RSSI_actual = wstk.readRSSI()
        if RSSI_actual > RSSI_max:
            RSSI_max = RSSI_actual
            ctuned = ctune_actual

    siggen.toggleModulation(False)
    siggen.toggleRFOut(False)

    return ctuned, RSSI_max