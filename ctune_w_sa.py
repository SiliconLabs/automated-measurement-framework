from pywstk import pyRAIL
from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pywstk.pyRAIL import WSTK_RAILTest
from time import sleep
from pyspecan.pySpecAn import SpecAn
from common import logger as lg
import serial
import numpy as np

def ctune(frequency:float, ctune_initial:int, power_raw:float, SA_Span:float, SA_RBW:float)->float:

    #specan = SpecAn("TCPIP::169.254.23.5::INSTR", auto_detect=False,logger_settings=lg.Logger.Settings(logging_level=lg.Level.INFO))
    specan = SpecAn("TCPIP::169.254.88.77::INSTR", auto_detect=False,logger_settings=lg.Logger.Settings(logging_level=lg.Level.INFO))
    #specan.setAppSwitch("SA")
    #specan.initiate()
    specan.updateDisplay(on_off=True)
    specan.setFrequency(frequency)
    specan.setSpan(SA_Span)
    specan.setRBW(SA_RBW)
    specan.setRefLevel(20)
    specan.initiate()
    sleep(0.5)
    wstk = WSTK_RAILTest("COM3",reset=True)
    #wstk.resetDevice()
    wstk.receive(on_off=False, frequency_Hz=frequency, timeout_ms=1000)
    
    #ctune_initial = wstk._driver.getCtune()
    #ctune_initial = 120
    ctune_max = 255
    ctune_steps = 20
    fine_error_Hz = 5000

    ctune_range = np.linspace(0, ctune_max, ctune_steps, dtype=int)
    global ctuned
    wstk._driver.setCtune(ctune_initial)
    wstk.transmit(mode="CW", frequency_Hz=frequency, power_dBm=power_raw, power_format="RAW")
    wstk._driver.setTxTone(on_off=True, mode="cw")
    sleep(0.2)
    marker_freq = specan.getMaxMarker().position
    
    if (marker_freq - frequency) < fine_error_Hz and (marker_freq - frequency) > -fine_error_Hz:
        
        if (marker_freq - frequency) == 0:
            ctuned = ctune_initial

        elif (marker_freq - frequency) > 0:
            ctune_range_fine = np.linspace(ctune_initial, ctune_max, ctune_max-ctune_initial+1, dtype=int)
            ctune_array = []
            marker_array = []
            i = 0
            for ctune_item_fine in ctune_range_fine:
                ctune_actual_fine = ctune_item_fine
                wstk._driver.setTxTone(on_off=False, mode="cw")
                wstk._driver.setCtune(ctune_actual_fine)
                wstk._driver.setTxTone(on_off=True, mode="cw")
                ctune_array.append(ctune_actual_fine)
                sleep(0.2)
                marker_freq_actual_fine = specan.getMaxMarker().position
                marker_array.append(marker_freq_actual_fine)
                            
                if (marker_freq_actual_fine - frequency) <= 0 and (frequency - marker_freq_actual_fine) < (marker_array[i-1] - frequency):
                    marker_freq = marker_freq_actual_fine
                    ctuned = ctune_actual_fine
                    
                    break

                if (marker_freq_actual_fine - frequency) <= 0 and (frequency - marker_freq_actual_fine) >= (marker_array[i-1] - frequency):
                    marker_freq = marker_array[i-1]
                    ctuned = ctune_array[i-1]
                    
                    break

                i += 1

        elif (marker_freq - frequency) < 0:
            ctune_range_fine = np.linspace(ctune_initial, 0, ctune_initial+1, dtype=int)
            ctune_array = []
            marker_array = []
            i = 0
            for ctune_item_fine in ctune_range_fine:
                ctune_actual_fine = ctune_item_fine
                wstk._driver.setTxTone(on_off=False, mode="cw")
                wstk._driver.setCtune(ctune_actual_fine)
                wstk._driver.setTxTone(on_off=True, mode="cw")
                ctune_array.append(ctune_actual_fine)
                sleep(0.2)
                marker_freq_actual_fine = specan.getMaxMarker().position
                marker_array.append(marker_freq_actual_fine)
            
                if (marker_freq_actual_fine - frequency) >= 0 and (marker_freq_actual_fine - frequency) < (frequency - marker_array[i-1]):
                    marker_freq = marker_freq_actual_fine
                    ctuned = ctune_actual_fine
                    
                    break

                if (marker_freq_actual_fine - frequency) >= 0 and (marker_freq_actual_fine - frequency) >= (frequency - marker_array[i-1]):
                    marker_freq = marker_array[i-1]
                    ctuned = ctune_array[i-1]
                    
                    break

                i += 1
        
    else:
        for ctune_item in ctune_range:
            ctune_actual = ctune_item
            wstk._driver.setTxTone(on_off=False, mode="cw")
            wstk._driver.setCtune(ctune_actual)
            wstk._driver.setTxTone(on_off=True, mode="cw")
            sleep(0.2)
            marker_freq_actual = specan.getMaxMarker().position
        
            if (marker_freq_actual - frequency) < fine_error_Hz and (marker_freq_actual - frequency) > -fine_error_Hz:
                
                if (marker_freq_actual - frequency) == 0:
                    ctuned = ctune_actual
                    marker_freq = marker_freq_actual

                    break

                elif (marker_freq_actual - frequency) > 0:
                    ctune_range_fine = np.linspace(ctune_actual, ctune_max, ctune_max-ctune_actual+1, dtype=int)
                    ctune_array = []
                    marker_array = []
                    i = 0
                    for ctune_item_fine in ctune_range_fine:
                        ctune_actual_fine = ctune_item_fine
                        wstk._driver.setTxTone(on_off=False, mode="cw")
                        wstk._driver.setCtune(ctune_actual_fine)
                        wstk._driver.setTxTone(on_off=True, mode="cw")
                        ctune_array.append(ctune_actual_fine)
                        sleep(0.2)
                        marker_freq_actual_fine = specan.getMaxMarker().position
                        marker_array.append(marker_freq_actual_fine)
                    
                        if (marker_freq_actual_fine - frequency) <= 0 and (frequency - marker_freq_actual_fine) < (marker_array[i-1] - frequency):
                            marker_freq = marker_freq_actual_fine
                            ctuned = ctune_actual_fine

                            break

                        if (marker_freq_actual_fine - frequency) <= 0 and (frequency - marker_freq_actual_fine) >= (marker_array[i-1] - frequency):
                            marker_freq = marker_array[i-1]
                            ctuned = ctune_array[i-1]
                    
                            break

                        i += 1

                elif (marker_freq_actual - frequency) < 0:
                    ctune_range_fine = np.linspace(ctune_actual, 0, ctune_actual+1, dtype=int)
                    ctune_array = []
                    marker_array = []
                    i = 0
                    for ctune_item_fine in ctune_range_fine:
                        ctune_actual_fine = ctune_item_fine
                        wstk._driver.setTxTone(on_off=False, mode="cw")
                        wstk._driver.setCtune(ctune_actual_fine)
                        wstk._driver.setTxTone(on_off=True, mode="cw")
                        ctune_array.append(ctune_actual_fine)
                        sleep(0.2)
                        marker_freq_actual_fine = specan.getMaxMarker().position
                        marker_array.append(marker_freq_actual_fine)
                    
                        if (marker_freq_actual_fine - frequency) >= 0 and (marker_freq_actual_fine - frequency) < (frequency - marker_array[i-1]):
                            marker_freq = marker_freq_actual_fine
                            ctuned = ctune_actual_fine
                    
                            break

                        if (marker_freq_actual_fine - frequency) >= 0 and (marker_freq_actual_fine - frequency) >= (frequency - marker_array[i-1]):
                            marker_freq = marker_array[i-1]
                            ctuned = ctune_array[i-1]
                    
                            break

                        i += 1
                
                break
    
    wstk._driver.setTxTone(on_off=False, mode="cw")                        
    return ctuned, marker_freq