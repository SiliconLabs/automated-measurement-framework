from pywstk import pyRAIL
import time
from time import sleep
from pysiggen.pySigGen import SigGen
from pysiggen.pySigGen import SigGenSettings
from pyspecan.pySpecAn import SpecAn
from common import Logger, Level
import serial
import numpy as np
import xlsxwriter
from excel_plotter.Py_to_Excel_plotter_blocking import Py_to_Excel_plotter

board_name = 'BRD4264B'

desired_freqs = [868e6, 876e6, 915e6]
desired_cable_attenuation_dB = 7
desired_start_power_dBm = -101  #without the cable attenution
desired_stop_power_dBm = -107   #without the cable attenution
desired_power_steps = 13
desired_power_relative_to_sens_during_blocking_test_dB = 3  #blocking test when desired power is above the senitivity level by this value

blocker_offset_freqs = [1e6, -1e6, 2e6, -2e6, 8e6, -8e6]
blocker_cable_attenuation_dB = 7
blocker_start_power_dBm = -43   #without the cable attenution
blocker_stop_power_dBm = -3     #without the cable attenution
blocker_power_steps = 41


siggen = SigGen("GPIB0::5::INSTR") #this can change, run pyvisa-shell list command in cmd to find current address
siggen.getError()
settings = SigGenSettings()
settings.frequency_Hz = desired_freqs[0]
settings.amplitude_dBm = desired_start_power_dBm
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

specan = SpecAn("TCPIP::169.254.88.77::INSTR", auto_detect=True,logger_settings=Logger.Settings(logging_level=Level.INFO))
specan.reset()
specan.setAppSwitch("SG")
#specan.initiate()
specan.setSigGenFreq_Hz(desired_freqs[0] + blocker_offset_freqs[0])
specan.setSigGenPower_dBm(blocker_start_power_dBm)
specan.setSigGenOutput_toggle(on_off=False)

workbook_name = board_name + '_Blocking_test-results.xlsx'
workbook = xlsxwriter.Workbook(workbook_name)
sheet_parameters = workbook.add_worksheet('Parameters')
sheet_parameters.write(0, 0, 'Modulation')
sheet_parameters.write(0, 1, 'Data Rate [kbps]')
sheet_parameters.write(0, 2, 'Deviation [kHz]')
sheet_parameters.write(0, 3, 'BbT')
sheet_parameters.write(0, 4, 'Blocker Signal')
sheet_parameters.write(1, 0, settings.modulation.type)
sheet_parameters.write(1, 1, settings.modulation.symbolrate_sps / 1e3)
sheet_parameters.write(1, 2, settings.modulation.deviation_Hz / 1e3)
sheet_parameters.write(1, 3, settings.filter_BbT)
sheet_parameters.write(1, 4, 'CW')
sheet_rawdata = workbook.add_worksheet('RawData')
sheet_rawdata.write(0, 0, 'Frequency [MHz]')
sheet_rawdata.write(0, 1, 'Input Power [dBm]')
sheet_rawdata.write(0, 2, 'BER [%]')
sheet_rawdata.write(0, 3, 'RSSI')
sheet_rawdata.write(0, 4, 'Blocker Freq. Offset [MHz]')
sheet_rawdata.write(0, 5, 'Blocker Abs. Power [dBm]')
sheet_sensdata = workbook.add_worksheet('SensData')
sheet_sensdata.write(0, 0, 'Frequency [MHz]')
sheet_sensdata.write(0, 1, 'Sensitivity [dBm]')
sheet_sensdata.write(0, 2, 'BER [%]')
sheet_blockingdata = workbook.add_worksheet('BlockingData')
sheet_blockingdata.write(0, 0, 'Frequency [MHz]')
sheet_blockingdata.write(0, 1, 'Input Power [dBm]')
sheet_blockingdata.write(0, 2, 'Blocker Freq. Offset [MHz]')
sheet_blockingdata.write(0, 3, 'Blocker Abs. Power [dBm]')
sheet_blockingdata.write(0, 4, 'BER [%]')

if (desired_start_power_dBm - desired_cable_attenuation_dB) > 10:
    raise ValueError("Too high input power injected!")

sigGen_power_list = np.linspace(desired_start_power_dBm, desired_stop_power_dBm, desired_power_steps, dtype=float)
#sigGen_power_list = [-100, -109, -110, -120]
blocker_power_list = np.linspace(blocker_start_power_dBm, blocker_stop_power_dBm, blocker_power_steps, dtype=float)
#blocker_power_list = [-50, -45, -40, -35, -30]

if __name__ == "__main__":
    wstk_rx = pyRAIL.WSTK_RAILTest("COM7",reset=True)
    i = 1
    j = 1
    k = 1
    sens_list = []
    blocking_list = []

    for actual_freq in desired_freqs:
        frequency = actual_freq
        # transmit in PN9 stream mode
        #settings.frequency_Hz = frequency
        #settings.amplitude_dBm = desired_start_power_dBm
        siggen.setFrequency(frequency)
        siggen.setAmplitude(desired_start_power_dBm)
        #siggen.setStream(settings)
        # blocking BER measurement function with timeout, syncs on PN9
        # can only be used with BER configured RAILtest
        
        for sigGen_power_item in sigGen_power_list:
            
            sigGen_power = sigGen_power_item
            siggen.setAmplitude(sigGen_power)
            
            ber_percent,done_percent,rssi = wstk_rx.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency)
            print("Input Power:" + str(sigGen_power-desired_cable_attenuation_dB) + " dBm")

            sheet_rawdata.write(i, 0, frequency/1e6)
            sheet_rawdata.write(i, 1, sigGen_power-desired_cable_attenuation_dB)
            sheet_rawdata.write(i, 2, ber_percent)
            sheet_rawdata.write(i, 3, rssi)
            sheet_rawdata.write(i, 4, " ")
            sheet_rawdata.write(i, 5, " ")
            i += 1

            if ber_percent >= 0.1:
                sens_str = "At " + str(frequency/1e6) + "MHz, Sensitivity: " + str(sigGen_power-desired_cable_attenuation_dB) + " dBm, RSSI:" + str(rssi)
                print(sens_str)
                sens_list.append(sens_str)

                sheet_sensdata.write(j, 0, frequency/1e6)
                sheet_sensdata.write(j, 1, sigGen_power - desired_cable_attenuation_dB)
                sheet_sensdata.write(j, 2, ber_percent)
                j += 1

                break

        siggen.setAmplitude(sigGen_power + desired_power_relative_to_sens_during_blocking_test_dB)
        specan.setSigGenOutput_toggle(on_off=True)

        for actual_blocker_offset_freq in blocker_offset_freqs:
            blocker_offset_freq = actual_blocker_offset_freq
            specan.setSigGenFreq_Hz(frequency + blocker_offset_freq)

            for blocker_power_item in blocker_power_list:
                blocker_power = blocker_power_item
                specan.setSigGenPower_dBm(blocker_power)
                ber_percent,done_percent,rssi = wstk_rx.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency)

                sheet_rawdata.write(i, 0, frequency/1e6)
                sheet_rawdata.write(i, 1, sigGen_power + desired_power_relative_to_sens_during_blocking_test_dB - desired_cable_attenuation_dB)
                sheet_rawdata.write(i, 2, ber_percent)
                sheet_rawdata.write(i, 3, rssi)
                sheet_rawdata.write(i, 4, blocker_offset_freq/1e6)
                sheet_rawdata.write(i, 5, blocker_power-blocker_cable_attenuation_dB)
                i += 1

                if ber_percent >= 0.1:
                    blocking_str = "At " + str(frequency/1e6) + "MHz with " + str(blocker_offset_freq/1e6) + "MHz offset, Blocking: " + str(blocker_power-blocker_cable_attenuation_dB) + " dBm, RSSI:" + str(rssi)
                    print(blocking_str)
                    blocking_list.append(blocking_str)

                    sheet_blockingdata.write(k, 0, frequency/1e6)
                    sheet_blockingdata.write(k, 1, sigGen_power + desired_power_relative_to_sens_during_blocking_test_dB - desired_cable_attenuation_dB)
                    sheet_blockingdata.write(k, 2, blocker_offset_freq/1e6)
                    sheet_blockingdata.write(k, 3, blocker_power-blocker_cable_attenuation_dB)
                    sheet_blockingdata.write(k, 4, ber_percent)
                    k += 1

                    break

        specan.setSigGenOutput_toggle(on_off=False)

        #print("BER: ", ber_percent,"%, Done percent: ", done_percent, "%")    
        #print("Press Ctrl-C to quit!")
    
    #while 1:
    #    try:
    #        time.sleep(1)
    #    except KeyboardInterrupt:
    #        wstk_rx.stop(echo=False)
    #        break
    
    workbook.close()
    print("\n")

    siggen.toggleModulation(False)
    siggen.toggleRFOut(False)

    print("\n")
    print(sens_list)
    print(blocking_list)
    
Py_to_Excel_plotter(workbook_name)

print('\nDone with measurements')