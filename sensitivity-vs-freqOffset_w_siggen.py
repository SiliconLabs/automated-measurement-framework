from pywstk import pyRAIL
import time
from pySigGen import pySigGen
import serial
import numpy as np
import xlsxwriter
from excel_plotter.Py_to_Excel_plotter_sens_vs_freqoffset import Py_to_Excel_plotter

board_name = 'BRD4264B'
freqs = [868e6, 915e6]
freq_offset_min = -100e3
freq_offset_max = 100e3
freq_offset_steps = 81

cable_attenuation_dB = 0.5
start_power_dBm = -84.5
stop_power_dBm = -112.5
power_steps = 113

siggen = pySigGen.SigGen("GPIB0::5::INSTR") #this can change, run pyvisa-shell list command in cmd to find current address
siggen.getError()
settings = pySigGen.SigGenSettings()
settings.frequency_Hz = freqs[0]
settings.amplitude_dBm = start_power_dBm
settings.modulation.type = "FSK2" #see all modulation abbrevations at page 299 of https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.modulation.symbolrate_sps = 100e3
settings.modulation.deviation_Hz = 50e3
settings.rf_on = True
settings.mod_on = True
settings.stream_type = "PN9" #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
settings.filter_type = "Gaussian" #Gaussian or Nyquist
settings.filter_BbT = 0.5
settings.custom_on = True
siggen.setStream(settings)
#print(settings)

workbook_name = board_name + '_Sensitivity-vs-FreqOffset_test-results.xlsx'
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
sheet_sensdata = workbook.add_worksheet('SensData')
sheet_sensdata.write(0, 0, 'Frequency [MHz]')
sheet_sensdata.write(0, 1, 'Freq. Offset [kHz]')
sheet_sensdata.write(0, 2, 'Sensitivity [dBm]')
sheet_sensdata.write(0, 3, 'BER [%]')

if (start_power_dBm - cable_attenuation_dB) > 10:
    raise ValueError("Too high input power injected!")

sigGen_power_list = np.linspace(start_power_dBm, stop_power_dBm, power_steps, dtype=float)
freq_offset_list = np.linspace(freq_offset_min, freq_offset_max, freq_offset_steps)

if __name__ == "__main__":
    wstk_rx = pyRAIL.WSTK_RAILTest("COM5",reset=True)
    i = 1
    sens_list = []
    for actual_freq in freqs:
        frequency = actual_freq
        # transmit in PN9 stream mode
        settings.frequency_Hz = frequency
        settings.amplitude_dBm = start_power_dBm
        siggen.setStream(settings)
        # blocking BER measurement function with timeout, syncs on PN9
        # can only be used with BER configured RAILtest

        for freq_offset_item in freq_offset_list:
            freq_offset = freq_offset_item
            settings.frequency_Hz = frequency + freq_offset
            j = 1   #dummy counter to log sensitivity if BER measurement fails between two input-power steps

            for sigGen_power_item in sigGen_power_list:
                
                sigGen_power = sigGen_power_item
                settings.amplitude_dBm = sigGen_power
                siggen.setStream(settings)
                
                ber_percent,done_percent,rssi = wstk_rx.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency,echo=True)
                print("Input Power:" + str(sigGen_power-cable_attenuation_dB) + " dBm")

                if ber_percent >= 0.1:
                    sens_str = "At " + str(actual_freq/1e6) + "MHz with frequency offset of " + str(freq_offset/1e3) + "kHz, Sensitivity: " + str(sigGen_power-cable_attenuation_dB) + " dBm, RSSI:" + str(rssi)
                    print(sens_str)
                    sens_list.append(sens_str)
                    sheet_sensdata.write(i, 0, frequency/1e6)
                    sheet_sensdata.write(i, 1, freq_offset/1e3)
                    sheet_sensdata.write(i, 2, sigGen_power-cable_attenuation_dB)
                    sheet_sensdata.write(i, 3, ber_percent)
                    i += 1
                    break

                if done_percent == 0 and j == 1:
                    print("\nBER measurement failed..")
                    break

                if done_percent == 0 and j > 1:
                    sens_str = "At " + str(actual_freq/1e6) + "MHz with frequency offset of " + str(freq_offset/1e3) + "kHz, Sensitivity: " + str(sigGen_power_list[j-2]-cable_attenuation_dB) + " dBm, RSSI:" + str(rssi)
                    print(sens_str)
                    sens_list.append(sens_str)
                    sheet_sensdata.write(i, 0, frequency/1e6)
                    sheet_sensdata.write(i, 1, freq_offset/1e3)
                    sheet_sensdata.write(i, 2, sigGen_power_list[j-2]-cable_attenuation_dB)
                    sheet_sensdata.write(i, 3, ber_percent)
                    i += 1
                    break

                j += 1

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