from pywstk import pyRAIL
import time
from pysiggen import pySigGen
import serial
import numpy as np
import xlsxwriter
from excel_plotter.Py_to_Excel_plotter_sens import Py_to_Excel_plotter

board_name = 'BRD4264B'
freqs = [868e6]

cable_attenuation_dB = 0.5
start_power_dBm = -77.5
stop_power_dBm = -114.5
power_steps = 149

siggen = pySigGen.SigGen("GPIB0::5::INSTR") #this can change, run pyvisa-shell list command in cmd to find current address
siggen.getError()
settings = pySigGen.SigGenSettings()
settings.frequency_Hz = freqs[0]
settings.amplitude_dBm = start_power_dBm
settings.modulation.type = "FSK2" #see all modulation abbrevations at page 299 of https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.modulation.symbolrate_sps = 500e3
settings.modulation.deviation_Hz = 175e3
settings.rf_on = True
settings.mod_on = True
settings.stream_type = "PN9" #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.filter_type = "Gaussian" #Gaussian or Nyquist
settings.filter_BbT = 0.5
settings.custom_on = True
siggen.updateDisplay(disp_on=True)
siggen.setStream(settings)
#print(settings)

workbook_name = board_name + '_Sensitivity_Waterfall_test-results.xlsx'
workbook = xlsxwriter.Workbook(workbook_name)
sheet_parameters = workbook.add_worksheet('Parameters')
sheet_parameters.write(0, 0, 'Modulation')
sheet_parameters.write(0, 1, 'Data Rate [kbps]')
sheet_parameters.write(0, 2, 'Deviation [kHz]')
sheet_parameters.write(0, 3, 'BbT')
sheet_parameters.write(1, 0, settings.modulation.type)
sheet_parameters.write(1, 1, settings.modulation.symbolrate_sps / 1e3)
sheet_parameters.write(1, 2, settings.modulation.deviation_Hz / 1e3)
sheet_parameters.write(1, 3, settings.filter_BbT)
sheet_rawdata = workbook.add_worksheet('RawData')
sheet_rawdata.write(0, 0, 'Frequency [MHz]')
sheet_rawdata.write(0, 1, 'Input Power [dBm]')
sheet_rawdata.write(0, 2, 'BER [%]')
sheet_rawdata.write(0, 3, 'RSSI')
sheet_sensdata = workbook.add_worksheet('SensData')
sheet_sensdata.write(0, 0, 'Frequency [MHz]')
sheet_sensdata.write(0, 1, 'Sensitivity [dBm]')
sheet_sensdata.write(0, 2, 'BER [%]')

if (start_power_dBm - cable_attenuation_dB) > 10:
    raise ValueError("Too high input power injected!")

sigGen_power_list = np.linspace(start_power_dBm, stop_power_dBm, power_steps, dtype=float)
#sigGen_power_list = [-100, -109, -110, -120]

if __name__ == "__main__":
    wstk_rx = pyRAIL.WSTK_RAILTest("COM5",reset=True)
    i = 1
    j = 1
    sens_list = []
    for actual_freq in freqs:
        frequency = actual_freq
        # transmit in PN9 stream mode
        settings.frequency_Hz = frequency
        settings.amplitude_dBm = start_power_dBm
        siggen.setStream(settings)
        # blocking BER measurement function with timeout, syncs on PN9
        # can only be used with BER configured RAILtest
        
        k = 1
        for sigGen_power_item in sigGen_power_list:
            
            sigGen_power = sigGen_power_item
            settings.amplitude_dBm = sigGen_power
            siggen.setStream(settings)
            
            ber_percent,done_percent,rssi = wstk_rx.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency,echo=True)
            print("Input Power:" + str(sigGen_power-cable_attenuation_dB) + " dBm")

            sheet_rawdata.write(i, 0, frequency/1e6)
            sheet_rawdata.write(i, 1, sigGen_power-cable_attenuation_dB)
            sheet_rawdata.write(i, 2, ber_percent)
            sheet_rawdata.write(i, 3, rssi)
            i += 1

            if k == 1 and ber_percent >= 0.1:
                sens_str = "At " + str(actual_freq/1e6) + "MHz, Sensitivity: " + str(sigGen_power-cable_attenuation_dB) + " dBm, RSSI:" + str(rssi)
                print(sens_str)
                sens_list.append(sens_str)

                sheet_sensdata.write(j, 0, frequency/1e6)
                sheet_sensdata.write(j, 1, sigGen_power-cable_attenuation_dB)
                sheet_sensdata.write(j, 2, ber_percent)
                j += 1
                k += 1

                #break

        #print("BER: ", ber_percent,"%, Done percent: ", done_percent, "%")
    print('\n')
    print(sens_list)
        #print("Press Ctrl-C to quit!")
    
    #while 1:
    #    try:
    #        time.sleep(1)
    #    except KeyboardInterrupt:
    #        wstk_rx.stop(echo=False)
    #        break
    
    workbook.close()
    
    settings.rf_on = False
    settings.mod_on = False
    siggen.setStream(settings)

Py_to_Excel_plotter(workbook_name)

print('\nDone with measurements')