from pydoc import visiblename
from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pywstk.pyRAIL import WSTK_RAILTest
from pyspecan.pySpecAn import SpecAn, RS_SpectrumAnalyzer
from pysiggen.pySigGen import SigGen
from pysiggen.pySigGen import SigGenSettings
import numpy as np
from pypsu import pyPSU
from matplotlib import pyplot as plt
import xlsxwriter
from time import sleep
from datetime import datetime as dt
from excel_plotter.Py_to_Excel_plotter import Py_to_Excel_plotter
import pandas as pd
from os import remove,path
from dataclasses import dataclass
from common import Logger, Level
import atexit
from pyvisa import errors as visaerrors
import serial
import xlsxwriter
import os


class Sensitivity():
    """
    Measuring receiver sensitivity of the EFR32-based design. 

    Required instruments: 
    - SiLabs EFR with RAILTest configured
    - Signal Generator
    """

    @dataclass
    class Settings():
        """
        All configurable settings for this measurement. 

        Sweepable variables can be configured using start,stop and steps parameters
        or by a list. If a list is not initialized, the start/stop parameters will be used. 

        :param int freq_start_hz: Start frequency
        :param int freq_stop_hz: Stop frequency
        :param int freq_num_steps: Number of discrete frequency steps between stop and start values
        :param list freq_list_hz: Custom list of frequencies
        
        :param Logger.Settings logger_settings: Logger module settings for the measurement, imported from common

        :param bool measure_with_CTUNE_w_SA: Enable CTUNE with spectrum analyzer (more accurate)
        :param bool measure_with_CTUNE_w_SG: Enable CTUNE with signal generator (easier setup, faster)


        :param str err_rate_type: 'BER' or 'PER', for PER the stream type should be a @BIT filename like "temp@BIT", use \"\"
        :param float err_rate_threshold_percent: where the sensitivity threshold is reached, different for standards

        :param float cable_attenuation_dB: total cable loss in the test setup between SigGen and DUT

        :param float siggen_power_start_dBm: Start SigGen power, cable loss not included
        :param float siggen_power_stop_dBm: Stop SigGen power, cabel loss not included
        :param int siggen_power_steps: Number of discrete SigGen power steps between stop and start values
        :param list siggen_power_list_dBm: Custom list of SigGen powers in dBm
        :param str siggen_modulation_type: Modulation type, most common values: BPSK|QPSK|OQPSK|MSK|FSK2|FSK4|FSK8
                                           See all modulation abbrevations at page 299 of:
                                           https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
        :param float siggen_modulation_symbolrate_sps: Symbol rate of the output signal in symbols per second,
                                                        minimum :47.684 sps, max: 12.500000 Msps
        :param float siggen_modulation_deviation_Hz: Frequency deviation in hertz for FM types
        :param str siggen_stream_type: data type of the output stream,
                                       values: PN9|PN11|PN15|PN20|PN23|FIX4|"<file name>"|EXT|P4|P8|P16|P32|P64
                                        see all documentation for stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
        :param str siggen_filter_type: "Gaussian" or "Nyquist" 
        :param float siggen_filter_BbT: Filter BT factor between 0 and 1
        :param bool siggen_custom_on: Custom mode one, for all SG functionality this should be on
        :param str siggen_per_packet_filename: the name of the file on this PC, that contains the binary data of the test packet
                                                Should be in the format of Saleae Logic analyzers csv export
        :param str siggen_per_packet_siggen_name : what the name of the @BIT file will be on the generator itself
        :param str siggen_pattern_repeat: continuous or single ( CONT or SING)
        :param str siggen_trigger_type: KEY|BUS|EXT- triggerkey on generator, GPIB bus, or external, almost always use BUS
        :param Logger.Settings siggen_logger_settings: Logger module settings for SG, imported from common
        
        :param str specan_address: VISA address of Spectrum Analyzer,can check PyVISA documentation
        :param int specan_span_hz: SA span in Hz
        :param int specan_rbw_hz: SA resolution bandwidth in Hz
        :param int specan_ref_level_dbm: SA reference level in dBm
        :param str specan_detector_type: SA detector type, directly passed to pySpecAn
        :param float specan_ref_offset: SA reference offset
        :param Logger.Settings specan_logger_settings: Logger module settings for SA, imported from common

        :param str wstk_com_port: COM port of the RAILTest device
        :param Logger.Settings wstk_logger_settings: Logger module settings for WSTK, imported from common
        """
        #Frequency range settings
        freq_start_hz: int = 868e6
        freq_stop_hz: int = 928e6
        freq_num_steps: int = 2
        freq_list_hz: list|None = None
        logger_settings: Logger.Settings = Logger.Settings()

        #Cable attenutation setting
        cable_attenuation_dB: float = 2
        cable_logger_settings: Logger.Settings = Logger.Settings()
        
        #sensitivity measurements with CTUNE
        ctune_initial:int = None
        measure_with_CTUNE_w_SA: bool = False
        measure_with_CTUNE_w_SG: bool = False
        #error rate settings
        err_rate_type: str = 'BER' #suprise, other possible option is 'PER'
        err_rate_threshold_percent:float = 0.1

        #SG settings 
        siggen_address: str = 'GPIB0::5::INSTR'
        siggen_power_start_dBm: float = -80
        siggen_power_stop_dBm: float = -110
        siggen_power_steps: int = 61
        siggen_power_list_dBm: list|None = None
        siggen_modulation_type: str = "FSK2" #see all modulation abbrevations at page 299 of https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
        siggen_modulation_symbolrate_sps: float = 100e3
        siggen_modulation_deviation_Hz: float = 50e3
        #siggen_rf_on = True
        #siggen_mod_on = True
        siggen_stream_type:str = "PN9" #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
        siggen_filter_type:str = "Gaussian" #Gaussian or Nyquist
        siggen_filter_BbT:float = 0.5
        siggen_custom_on:bool = True
        siggen_per_packet_filename :str = "pysiggen/packets/std_rail_packet.csv"
        siggen_per_packet_siggen_name :str = "TEMP"
        siggen_pattern_repeat:str = "SINGle"
        siggen_trigger_type:str = "BUS"
        siggen_logger_settings: Logger.Settings = Logger.Settings()

        #SA settings
        specan_address: str = 'TCPIP::169.254.88.77::INSTR'
        specan_span_hz: int = 200e3
        specan_rbw_hz: int = 10e3
        specan_ref_level_dbm: int = 20
        specan_detector_type: str = "NORM"
        specan_ref_offset: float = 0
        specan_logger_settings: Logger.Settings = Logger.Settings()

        #WSTK settings
        wstk_com_port: str = ""
        wstk_logger_settings: Logger.Settings = Logger.Settings()

        # Tested chip and board names 


    def __init__(self,settings:Settings,chip_name:str,board_name:str):
        """
        Initialize measurement class

        :param Settings settings: Settings dataclass containing all the configuration
        :param str chip_name : Name of IC being tested, only used in reporting
        :param str board_name: Name of board, containg the IC, only used in reporting
        :param str logfile_name: If initialized, separate logfile will be created for this measurement
        :param bool console_logging: Enable console logging, True by default
        """
        self.settings = settings
        self.chip_name = chip_name
        self.board_name = board_name

        timestamp = dt.now().timestamp()
        self.workbook_name = self.board_name + '_Sensitivity_results_'+str(int(timestamp))+'.xlsx'

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)


    def initialize_siggen(self):
        self.siggen = SigGen(resource=self.settings.siggen_address,logger_settings=self.settings.siggen_logger_settings)
        self.siggen.setAmplitude(self.settings.siggen_power_start_dBm)
        self.siggen.setModulation_type(self.settings.siggen_modulation_type)
        self.siggen.setSymbolrate(self.settings.siggen_modulation_symbolrate_sps)
        self.siggen.setDeviation(self.settings.siggen_modulation_deviation_Hz)
        self.siggen.setFilter(self.settings.siggen_filter_type)
        self.siggen.setFilterBbT(self.settings.siggen_filter_BbT)
        self.siggen.setBinaryData(self.settings.siggen_per_packet_filename,self.settings.siggen_per_packet_siggen_name)
        self.siggen.setPatternRepeat(self.settings.siggen_pattern_repeat)
        self.siggen.setTriggerType(self.settings.siggen_trigger_type)
        self.siggen.setStreamType(self.settings.siggen_stream_type)
        self.siggen.toggleCustom(self.settings.siggen_custom_on)
        self.siggen.toggleModulation(False)
        self.siggen.toggleRFOut(False)
        if self.settings.siggen_power_list_dBm is None:
            self.settings.siggen_power_list_dBm = np.linspace(
                                                    self.settings.siggen_power_start_dBm,
                                                    self.settings.siggen_power_stop_dBm,
                                                    self.settings.siggen_power_steps,
                                                    dtype=float
                                                    )

    def initialize_specan(self):
        self.specan = SpecAn(resource=self.settings.specan_address,logger_settings=self.settings.specan_logger_settings)
        self.specan.reset()
        self.specan.updateDisplay(on_off=True)
        self.specan.setMode('CONTINUOUS')
        self.specan.setSpan(self.settings.specan_span_hz)
        self.specan.setRBW(self.settings.specan_rbw_hz)
        self.specan.setRefLevel(self.settings.specan_ref_level_dbm)
        self.specan.setDetector(self.settings.specan_detector_type)
        self.specan.setRefOffset(self.settings.specan_ref_offset)
    
    def initialize_wstk(self):
        self.wstk = WSTK_RAILTest(self.settings.wstk_com_port,logger_settings=self.settings.wstk_logger_settings,reset=True)

        self.wstk._driver.reset()
        self.wstk._driver.rx(on_off=False)

        if self.settings.freq_list_hz is None:
            self.settings.freq_list_hz = np.linspace(
                                                    self.settings.freq_start_hz,
                                                    self.settings.freq_stop_hz,
                                                    self.settings.freq_num_steps,
                                                    dtype=float
                                                    )

    def initialize_reporter(self):
        self.workbook = xlsxwriter.Workbook(self.workbook_name)

        self.sheet_sum = self.workbook.add_worksheet('Summary')
        self.sheet_sum.write(0, 0, 'Chip name: ' + self.chip_name)
        self.sheet_sum.write(1, 0, 'Board name: ' + self.board_name)

        self.sheet_parameters = self.workbook.add_worksheet('Parameters')
        self.sheet_parameters.write(0, 0, 'Modulation')
        self.sheet_parameters.write(0, 1, 'Data Rate [kbps]')
        self.sheet_parameters.write(0, 2, 'Deviation [kHz]')
        self.sheet_parameters.write(0, 3, 'BbT')
        self.sheet_parameters.write(1, 0, self.settings.siggen_modulation_type)
        self.sheet_parameters.write(1, 1, self.settings.siggen_modulation_symbolrate_sps / 1e3)
        self.sheet_parameters.write(1, 2, self.settings.siggen_modulation_deviation_Hz / 1e3)
        self.sheet_parameters.write(1, 3, self.settings.siggen_filter_BbT)

        self.sheet_rawdata = self.workbook.add_worksheet('RawData')
        self.sheet_rawdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_rawdata.write(0, 1, 'Input Power [dBm]')
        self.sheet_rawdata.write(0, 2, self.settings.err_rate_type+' [%]')
        self.sheet_rawdata.write(0, 3, 'RSSI')
        
        self.sheet_sensdata = self.workbook.add_worksheet('SensData')
        self.sheet_sensdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_sensdata.write(0, 1, 'Sensitivity [dBm]')
        self.sheet_sensdata.write(0, 2, self.settings.err_rate_type+' [%]')
        self.sheet_sensdata.write(0, 3, 'RSSI')

        self.row = 1

        self.backup_csv_filename = "backup_csv_sens_raw.csv"


        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)

    def Py_to_Excel_plotter(self):
        # Import raw vs power data from existing xlsx
        summary = pd.read_excel(self.workbook_name, sheet_name="Summary")
        parameters = pd.read_excel(self.workbook_name, sheet_name="Parameters")
        raw_data = pd.read_excel(self.workbook_name, sheet_name="RawData")
        sens_data = pd.read_excel(self.workbook_name, sheet_name="SensData")
        
        # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
        output_workbook_name = "Plot" + self.workbook_name
        workbook = xlsxwriter.Workbook(output_workbook_name)
        Summary_Sheet = workbook.add_worksheet(name= 'Summary')
        Parameters_Sheet = workbook.add_worksheet(name= 'Parameters')
        Raw_Sheet = workbook.add_worksheet(name= 'RawData')
        Sens_Sheet = workbook.add_worksheet(name= 'SensData')
        Chart_Sheet = workbook.add_worksheet(name= 'Charts')
        # Copy imported data to this new xlsx
        col_name: str
        for i, col_name in enumerate(raw_data.columns):
            Raw_Sheet.write(0, i, col_name)
            Raw_Sheet.write_column(1, i, raw_data[col_name])
        col_name: str
        for i, col_name in enumerate(sens_data.columns):
            Sens_Sheet.write(0, i, col_name)
            Sens_Sheet.write_column(1, i, sens_data[col_name])
        col_name: str
        for i, col_name in enumerate(parameters.columns):
            Parameters_Sheet.write(0, i, col_name)
            Parameters_Sheet.write_column(1, i, parameters[col_name])
        col_name: str
        for i, col_name in enumerate(summary.columns):
            Summary_Sheet.write(0, i, col_name)
            Summary_Sheet.write_column(1, i, summary[col_name])
    
        # Create empty plot for input power vs BER
        plot = workbook.add_chart({"type" : "scatter"})
        # Plot the Fundamental input power vs BER
        plot.add_series({"categories" : "=RawData!$B$2:$B$10000",
                    "values" : "=RawData!$C$2:$C$10000",
                    "name" : self.settings.err_rate_type})
        plot.set_x_axis({"name" : "Input Power [dBm]"})
        plot.set_y_axis(({"name" : self.settings.err_rate_type+' [%]'}))
        plot.set_title({'name': 'Waterfall', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "1", plot, {'x_scale': 1.2, 'y_scale': 1.4})

        # Create empty plot for frequency vs Sensitivity
        plot_sens = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
        # Plot the Fundamental frequency vs Sensitivity
        plot_sens.add_series({"categories" : "=SensData!$A$2:$A$10000",
                    "values" : "=SensData!$B$2:$B$10000",
                    "name" : "Sens."})
        plot_sens.set_x_axis({"name" : "Frequency [MHz]"})
        plot_sens.set_y_axis(({"name" : "Sensitivity [dBm]"}))
        plot_sens.set_title({'name': 'Sensitivity vs Frequency', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "22", plot_sens, {'x_scale': 1.2, 'y_scale': 1.4})
        
        # shaping and filtering
        Parameters_Sheet.set_column(0, 13, 16)
        Raw_Sheet.set_column(0, 13, 16)
        Raw_Sheet.autofilter(0, 0, 10000, 0)
        Sens_Sheet.set_column(0, 13, 16)
        Sens_Sheet.autofilter(0, 0, 10000, 0)

        workbook.close()

        #replace original xlsx file with new xlsx file containing the plots
        os.remove(self.workbook_name)
        os.rename(output_workbook_name, self.workbook_name)
    
    def initiate(self):
        
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)
        i = 1
        j = 1
        global ber_success
        ber_success = True

        for freq in self.settings.freq_list_hz:

            self.siggen.setFrequency(freq)

            sens_raw_measurement_record = {
                    'Frequency [MHz]':freq/1e6,
                    'Input Power [dBm]':0,
                    self.settings.err_rate_type+' [%]':0,
                    'RSSI':0,     
                }

            for siggen_power in self.settings.siggen_power_list_dBm:

                self.siggen.setAmplitude(siggen_power)

                if self.settings.err_rate_type == 'BER':
                    err_percent,done_percent,rssi = self.wstk.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=freq)
                elif self.settings.err_rate_type == 'PER':
                    err_percent,done_percent,rssi = self.wstk.measurePer(npackets=100,interpacket_delay_s = 0.001,frequency_Hz=freq,tx_start_function=self.siggen.sendTrigger)
                else:
                    raise TypeError('Not recognized error rate string!')
                if i == 1 and done_percent == 0 and rssi == 0:
                    print(self.settings.err_rate_type +" measurement failed!")
                    ber_success = False
                    break

                sens_raw_measurement_record['Input Power [dBm]'] = siggen_power-self.settings.cable_attenuation_dB
                sens_raw_measurement_record[self.settings.err_rate_type +' [%]'] = err_percent
                sens_raw_measurement_record['RSSI'] = rssi

                self.sheet_rawdata.write(i, 0, freq/1e6)
                self.sheet_rawdata.write(i, 1, siggen_power-self.settings.cable_attenuation_dB)
                self.sheet_rawdata.write(i, 2, err_percent)
                self.sheet_rawdata.write(i, 3, rssi)
                i += 1

                record_df = pd.DataFrame(sens_raw_measurement_record,index=[0])
                record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                self.logger.info("\n"+record_df.to_string())

                if err_percent >= self.settings.err_rate_threshold_percent:

                        self.sheet_sensdata.write(j, 0, freq/1e6)
                        self.sheet_sensdata.write(j, 1, siggen_power-self.settings.cable_attenuation_dB)
                        self.sheet_sensdata.write(j, 2, err_percent)
                        self.sheet_sensdata.write(j, 3, rssi)
                        j += 1

                        break                       

        self.wstk._driver.reset()
 
    def ctune_w_sa(self):

        freq = self.settings.freq_list_hz[0]
        ctune_init = 120
        pwr_raw = 200

        self.initialize_specan()
        #sleep(0.1)
        self.specan.setFrequency(freq)
        sleep(0.1)

        ctune_min = 0
        ctune_max = 255
        ctune_steps = 20
        fine_error_Hz = 5000

        ctune_range = np.linspace(ctune_min, ctune_max, ctune_steps, dtype=int)
        global ctuned
        self.wstk._driver.setCtune(ctune_init)
        self.wstk.transmit(mode="CW", frequency_Hz=freq, power_dBm=pwr_raw, power_format="RAW")
        self.wstk._driver.setTxTone(on_off=True, mode="cw")
        sleep(0.2)
        marker_freq = self.specan.getMaxMarker().position
        
        if (marker_freq - freq) < fine_error_Hz and (marker_freq - freq) > -fine_error_Hz:
            
            if (marker_freq - freq) == 0:
                ctuned = ctune_init

            elif (marker_freq - freq) > 0:
                ctune_range_fine = np.linspace(ctune_init, ctune_max, ctune_max-ctune_init+1, dtype=int)
                ctune_array = []
                marker_array = []
                i = 0
                for ctune_item_fine in ctune_range_fine:
                    ctune_actual_fine = ctune_item_fine
                    self.wstk._driver.setTxTone(on_off=False, mode="cw")
                    self.wstk._driver.setCtune(ctune_actual_fine)
                    self.wstk._driver.setTxTone(on_off=True, mode="cw")
                    ctune_array.append(ctune_actual_fine)
                    sleep(0.2)
                    marker_freq_actual_fine = self.specan.getMaxMarker().position
                    marker_array.append(marker_freq_actual_fine)
                                
                    if (marker_freq_actual_fine - freq) <= 0 and (freq - marker_freq_actual_fine) < (marker_array[i-1] - freq):
                        marker_freq = marker_freq_actual_fine
                        ctuned = ctune_actual_fine
                        
                        break

                    if (marker_freq_actual_fine - freq) <= 0 and (freq - marker_freq_actual_fine) >= (marker_array[i-1] - freq):
                        marker_freq = marker_array[i-1]
                        ctuned = ctune_array[i-1]
                        
                        break

                    i += 1

            elif (marker_freq - freq) < 0:
                ctune_range_fine = np.linspace(ctune_init, 0, ctune_init+1, dtype=int)
                ctune_array = []
                marker_array = []
                i = 0
                for ctune_item_fine in ctune_range_fine:
                    ctune_actual_fine = ctune_item_fine
                    self.wstk._driver.setTxTone(on_off=False, mode="cw")
                    self.wstk._driver.setCtune(ctune_actual_fine)
                    self.wstk._driver.setTxTone(on_off=True, mode="cw")
                    ctune_array.append(ctune_actual_fine)
                    sleep(0.2)
                    marker_freq_actual_fine = self.specan.getMaxMarker().position
                    marker_array.append(marker_freq_actual_fine)
                
                    if (marker_freq_actual_fine - freq) >= 0 and (marker_freq_actual_fine - freq) < (freq - marker_array[i-1]):
                        marker_freq = marker_freq_actual_fine
                        ctuned = ctune_actual_fine
                        
                        break

                    if (marker_freq_actual_fine - freq) >= 0 and (marker_freq_actual_fine - freq) >= (freq - marker_array[i-1]):
                        marker_freq = marker_array[i-1]
                        ctuned = ctune_array[i-1]
                        
                        break

                    i += 1
            
        else:
            for ctune_item in ctune_range:
                ctune_actual = ctune_item
                self.wstk._driver.setTxTone(on_off=False, mode="cw")
                self.wstk._driver.setCtune(ctune_actual)
                self.wstk._driver.setTxTone(on_off=True, mode="cw")
                sleep(0.2)
                marker_freq_actual = self.specan.getMaxMarker().position
            
                if (marker_freq_actual - freq) < fine_error_Hz and (marker_freq_actual - freq) > -fine_error_Hz:
                    
                    if (marker_freq_actual - freq) == 0:
                        ctuned = ctune_actual
                        marker_freq = marker_freq_actual

                        break

                    elif (marker_freq_actual - freq) > 0:
                        ctune_range_fine = np.linspace(ctune_actual, ctune_max, ctune_max-ctune_actual+1, dtype=int)
                        ctune_array = []
                        marker_array = []
                        i = 0
                        for ctune_item_fine in ctune_range_fine:
                            ctune_actual_fine = ctune_item_fine
                            self.wstk._driver.setTxTone(on_off=False, mode="cw")
                            self.wstk._driver.setCtune(ctune_actual_fine)
                            self.wstk._driver.setTxTone(on_off=True, mode="cw")
                            ctune_array.append(ctune_actual_fine)
                            sleep(0.2)
                            marker_freq_actual_fine = self.specan.getMaxMarker().position
                            marker_array.append(marker_freq_actual_fine)
                        
                            if (marker_freq_actual_fine - freq) <= 0 and (freq - marker_freq_actual_fine) < (marker_array[i-1] - freq):
                                marker_freq = marker_freq_actual_fine
                                ctuned = ctune_actual_fine

                                break

                            if (marker_freq_actual_fine - freq) <= 0 and (freq - marker_freq_actual_fine) >= (marker_array[i-1] - freq):
                                marker_freq = marker_array[i-1]
                                ctuned = ctune_array[i-1]
                        
                                break

                            i += 1

                    elif (marker_freq_actual - freq) < 0:
                        ctune_range_fine = np.linspace(ctune_actual, 0, ctune_actual+1, dtype=int)
                        ctune_array = []
                        marker_array = []
                        i = 0
                        for ctune_item_fine in ctune_range_fine:
                            ctune_actual_fine = ctune_item_fine
                            self.wstk._driver.setTxTone(on_off=False, mode="cw")
                            self.wstk._driver.setCtune(ctune_actual_fine)
                            self.wstk._driver.setTxTone(on_off=True, mode="cw")
                            ctune_array.append(ctune_actual_fine)
                            sleep(0.2)
                            marker_freq_actual_fine = self.specan.getMaxMarker().position
                            marker_array.append(marker_freq_actual_fine)
                        
                            if (marker_freq_actual_fine - freq) >= 0 and (marker_freq_actual_fine - freq) < (freq - marker_array[i-1]):
                                marker_freq = marker_freq_actual_fine
                                ctuned = ctune_actual_fine
                        
                                break

                            if (marker_freq_actual_fine - freq) >= 0 and (marker_freq_actual_fine - freq) >= (freq - marker_array[i-1]):
                                marker_freq = marker_array[i-1]
                                ctuned = ctune_array[i-1]
                        
                                break

                            i += 1
                    
                    break
        
        self.wstk._driver.setTxTone(on_off=False, mode="cw") 
        self.wstk._driver.reset()
        self.wstk._driver.rx(on_off=False)
        self.wstk._driver.setCtune(ctuned)
        self.logger.info("Tuned CTUNE value: " + str(ctuned))
        self.logger.info("Actual DUT frequency: " + str(marker_freq) + " Hz")
        self.logger.info("Frequency error: " + str(marker_freq - freq) + " Hz")

        return ctuned    
    def ctune_w_sg(self):

        ctune_init = 120
        ctune_min = 0
        ctune_max = 255
        freq = self.settings.freq_list_hz[0]

        self.siggen.setFrequency(freq)
        self.siggen.setAmplitude(-40)
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)

        self.wstk.receive(on_off=True, frequency_Hz=freq, timeout_ms=1000)
        sleep(0.1)
        self.wstk._driver.rx(False)
        self.wstk._driver.setCtune(ctune_init)
        self.wstk._driver.rx(True)
        RSSI_max = self.wstk.readRSSI()
        ctuned = ctune_init
        ctune_range = np.linspace(ctune_min, ctune_max, 100, dtype=int)
        
        for ctune_item in ctune_range:
            ctune_actual = ctune_item
            self.wstk._driver.rx(False)
            self.wstk._driver.setCtune(ctune_actual)
            self.wstk._driver.rx(True)
            try:
                RSSI_actual = self.wstk.readRSSI()
            except ValueError:
                self.wstk._driver.rx(True)
                RSSI_actual = self.wstk.readRSSI()
                self.logger.debug("Caught RAIL bug getRSSI value error")
            self.logger.debug("Actual CTUNE: " +str(ctune_actual)+", actual RSSI: "+ str(RSSI_actual))
            if RSSI_actual > RSSI_max:
                RSSI_max = RSSI_actual
                ctuned = ctune_actual

        self.siggen.toggleModulation(False)
        self.siggen.toggleRFOut(False)

        self.wstk._driver.reset()
        self.wstk._driver.rx(on_off=False)
        self.wstk._driver.setCtune(ctuned)

        self.logger.info("Tuned CTUNE value: " + str(ctuned))
        self.logger.info("Max RSSI: " + str(RSSI_max) + " dBm")

    
    def stop(self):
        # if workbook already exists no need to close again
        if not path.isfile(self.workbook_name):
            self.logger.info("excel workbook closed")
            if hasattr(self,'workbook'):
                self.workbook.close()

        try:
            if hasattr(self,'siggen'):
                self.siggen.toggleModulation(False)
                self.siggen.toggleRFOut(False)
                self.siggen.logger.handlers.clear()
                del self.siggen
        # if someone already closed the visa session
        except visaerrors.InvalidSession:
            self.siggen.logger.handlers.clear() 
            self.initialize_siggen() 
            self.siggen.toggleModulation(False) 
            self.siggen.toggleRFOut(False)
            self.siggen.logger.handlers.clear()
            del self.siggen

        try:
            if hasattr(self,'wstk'):
                self.wstk._driver.reset()
                self.wstk.logger.handlers.clear()
                self.wstk.close()
                del self.wstk
        # if someone already closed the visa session
        except visaerrors.InvalidSession:
            self.wstk.logger.handlers.clear() 
            self.wstk._driver.reset()
            self.wstk.logger.handlers.clear()
            self.wstk.close()
            del self.wstk  

    @staticmethod
    def get_dataframe(dataframe_filename:str,index_col:list = [0,1,2])->pd.DataFrame:
        """
        Get DataFrame from backup file.

        :param str dataframe_filename: Path for backup file
        :param list index_col: Columns with MultiIndex, see Pandas MultiIndex docs

        :return: DataFrame stored in the backup file
        :rtype: pandas.DataFrame
        """
        final_df  = pd.read_csv(
                                dataframe_filename,
                                index_col = index_col
                                )
        return final_df

    def measure(self)->pd.DataFrame:
        """
        Initiate the measurement.

        :return: The measured data
        :rtype: pandas.DataFrame
        """
        self.initialize_siggen()
        self.initialize_wstk()
        self.initialize_reporter()

        if (self.settings.siggen_power_list_dBm[0] - self.settings.cable_attenuation_dB) > 10:
            raise ValueError("Too high input power injected!")
        
        if self.settings.ctune_initial is None:

            if self.settings.measure_with_CTUNE_w_SA:
                self.ctune_w_sa()
                self.logger.warn("Switch to SG!")
                input()

            if self.settings.measure_with_CTUNE_w_SG:
                self.ctune_w_sg()
        else:
            self.wstk._driver.setCtune(self.settings.ctune_initial)
            self.logger.info("Set Ctune:"+str(self.settings.ctune_initial))

        self.initiate()

        self.stop()

        self.Py_to_Excel_plotter()

        if ber_success:
            df = self.get_dataframe(self.backup_csv_filename)
            self.logger.debug(df.to_string())
            self.logger.info("\nDone with measurements")

            return df
       
    def __del__(self):
        self.stop()


class Blocking(Sensitivity):
    
    @dataclass
    class Settings(Sensitivity.Settings):

        desired_power_relative_to_sens_during_blocking_test_dB: float = 3  #blocking test when desired power is above the senitivity level by this value
        
        blocker_offset_start_freq_Hz: int = -8e6   
        blocker_offset_stop_freq_Hz: int = 8e6     
        blocker_offset_freq_steps: int = 5
        blocker_offset_freq_list_Hz: list|None = None

        blocker_cable_attenuation_dB: float = 7

        blocker_start_power_dBm: float = -43   #without the cable attenution
        blocker_stop_power_dBm: float = -3     #without the cable attenution
        blocker_power_steps: int = 41
        blocker_power_list_dBm: list|None = None

        blocker_logger_settings: Logger.Settings = Logger.Settings()
                

    def __init__(self,settings:Settings,chip_name:str,board_name:str):
        """
        Initialize measurement class

        :param Settings settings: Settings dataclass containing all the configuration
        :param str chip_name : Name of IC being tested, only used in reporting
        :param str board_name: Name of board, containg the IC, only used in reporting
        :param str logfile_name: If initialized, separate logfile will be created for this measurement
        :param bool console_logging: Enable console logging, True by default
        """
        self.settings = settings
        self.chip_name = chip_name
        self.board_name = board_name

        timestamp = dt.now().timestamp()
        self.workbook_name = self.board_name + '_Blocking_results_'+str(int(timestamp))+'.xlsx'

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)

    def initialize_specan_Generator(self):
        self.specan = SpecAn(resource=self.settings.specan_address,logger_settings=self.settings.specan_logger_settings)
        self.specan.reset()
        self.specan.updateDisplay(on_off=True)
        self.specan.setAppSwitch("SG")
        self.specan.setSigGenFreq_Hz(self.settings.freq_list_hz[0] + self.settings.blocker_offset_start_freq_Hz)
        self.specan.setSigGenPower_dBm(self.settings.blocker_start_power_dBm)
        self.specan.setSigGenOutput_toggle(on_off=False) 
        if self.settings.blocker_power_list_dBm is None:
            self.settings.blocker_power_list_dBm = np.linspace(
                                                    self.settings.blocker_start_power_dBm,
                                                    self.settings.blocker_stop_power_dBm,
                                                    self.settings.blocker_power_steps,
                                                    dtype=float
                                                    )
        if self.settings.blocker_offset_freq_list_Hz is None:
            self.settings.blocker_offset_freq_list_Hz = np.linspace(
                                                    self.settings.blocker_offset_start_freq_Hz,
                                                    self.settings.blocker_offset_stop_freq_Hz,
                                                    self.settings.blocker_offset_freq_steps,
                                                    dtype=float
                                                    )
    
    def initialize_reporter(self):
        self.workbook = xlsxwriter.Workbook(self.workbook_name)

        self.sheet_sum = self.workbook.add_worksheet('Summary')
        self.sheet_sum.write(0, 0, 'Chip name: ' + self.chip_name)
        self.sheet_sum.write(1, 0, 'Board name: ' + self.board_name)

        self.sheet_parameters = self.workbook.add_worksheet('Parameters')
        self.sheet_parameters.write(0, 0, 'Modulation')
        self.sheet_parameters.write(0, 1, 'Data Rate [kbps]')
        self.sheet_parameters.write(0, 2, 'Deviation [kHz]')
        self.sheet_parameters.write(0, 3, 'BbT')
        self.sheet_parameters.write(0, 4, 'Blocker Signal')
        self.sheet_parameters.write(1, 0, self.settings.siggen_modulation_type)
        self.sheet_parameters.write(1, 1, self.settings.siggen_modulation_symbolrate_sps / 1e3)
        self.sheet_parameters.write(1, 2, self.settings.siggen_modulation_deviation_Hz / 1e3)
        self.sheet_parameters.write(1, 3, self.settings.siggen_filter_BbT)
        self.sheet_parameters.write(1, 4, 'CW')

        self.sheet_rawdata = self.workbook.add_worksheet('RawData')
        self.sheet_rawdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_rawdata.write(0, 1, 'Input Power [dBm]')
        self.sheet_rawdata.write(0, 2, self.settings.err_rate_type +' [%]')
        self.sheet_rawdata.write(0, 3, 'RSSI')
        self.sheet_rawdata.write(0, 4, 'Blocker Freq. Offset [MHz]')
        self.sheet_rawdata.write(0, 5, 'Blocker Abs. Power [dBm]')
        
        self.sheet_sensdata = self.workbook.add_worksheet('SensData')
        self.sheet_sensdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_sensdata.write(0, 1, 'Sensitivity [dBm]')
        self.sheet_sensdata.write(0, 2, self.settings.err_rate_type +' [%]')
        self.sheet_sensdata.write(0, 3, 'RSSI')

        self.sheet_blockingdata = self.workbook.add_worksheet('BlockingData')
        self.sheet_blockingdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_blockingdata.write(0, 1, 'Input Power [dBm]')
        self.sheet_blockingdata.write(0, 2, 'Blocker Freq. Offset [MHz]')
        self.sheet_blockingdata.write(0, 3, 'Blocker Abs. Power [dBm]')
        self.sheet_blockingdata.write(0, 4, self.settings.err_rate_type +' [%]')

        self.row = 1

        self.backup_csv_filename = "backup_csv_blocking_raw.csv"

        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)

    def Py_to_Excel_plotter(self):
        # Import raw vs power data from existing xlsx
        summary = pd.read_excel(self.workbook_name, sheet_name="Summary")
        parameters = pd.read_excel(self.workbook_name, sheet_name="Parameters")
        raw_data = pd.read_excel(self.workbook_name, sheet_name="RawData")
        sens_data = pd.read_excel(self.workbook_name, sheet_name="SensData")
        blocking_data = pd.read_excel(self.workbook_name, sheet_name="BlockingData")
        
        # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
        output_workbook_name = "Plot" + self.workbook_name
        workbook = xlsxwriter.Workbook(output_workbook_name)
        Summary_Sheet = workbook.add_worksheet(name= 'Summary')
        Parameters_Sheet = workbook.add_worksheet(name= 'Parameters')
        Raw_Sheet = workbook.add_worksheet(name= 'RawData')
        Sens_Sheet = workbook.add_worksheet(name= 'SensData')
        Blocking_Sheet = workbook.add_worksheet(name= 'BlockingData')
        Chart_Sheet = workbook.add_worksheet(name= 'Charts')
        # Copy imported data to this new xlsx
        col_name: str
        for i, col_name in enumerate(raw_data.columns):
            Raw_Sheet.write(0, i, col_name)
            Raw_Sheet.write_column(1, i, raw_data[col_name])
        col_name: str
        for i, col_name in enumerate(sens_data.columns):
            Sens_Sheet.write(0, i, col_name)
            Sens_Sheet.write_column(1, i, sens_data[col_name])
        col_name: str
        for i, col_name in enumerate(blocking_data.columns):
            Blocking_Sheet.write(0, i, col_name)
            Blocking_Sheet.write_column(1, i, blocking_data[col_name])
        col_name: str
        for i, col_name in enumerate(parameters.columns):
            Parameters_Sheet.write(0, i, col_name)
            Parameters_Sheet.write_column(1, i, parameters[col_name])
        col_name: str
        for i, col_name in enumerate(summary.columns):
            Summary_Sheet.write(0, i, col_name)
            Summary_Sheet.write_column(1, i, summary[col_name])
    
        # Create empty plot for blocking
        plot = workbook.add_chart({"type" : "scatter"})
        # Plot the blocking
        plot.add_series({"categories" : "=BlockingData!$C$2:$C$10000",
                    "values" : "=BlockingData!$D$2:$D$10000",
                    "name" : "Blocking"})
        plot.set_x_axis({"name" : "Blocker Freq. Offset [MHz]"})
        plot.set_y_axis(({"name" : "Blocker Abs. Power [dBm]"}))
        plot.set_title({'name': 'Blocking vs Freq. Offset', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "1", plot, {'x_scale': 1.2, 'y_scale': 1.4})

        # Create empty plot for frequency vs Sensitivity
        plot_sens = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
        # Plot the Fundamental frequency vs Sensitivity
        plot_sens.add_series({"categories" : "=SensData!$A$2:$A$10000",
                    "values" : "=SensData!$B$2:$B$10000",
                    "name" : "Sens."})
        plot_sens.set_x_axis({"name" : "Frequency [MHz]"})
        plot_sens.set_y_axis(({"name" : "Sensitivity [dBm]"}))
        plot_sens.set_title({'name': 'Sensitivity vs Frequency', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "22", plot_sens, {'x_scale': 1.2, 'y_scale': 1.4})
        
        # shaping and filtering
        Parameters_Sheet.set_column(0, 13, 16)
        Raw_Sheet.set_column(0, 13, 25)
        Raw_Sheet.autofilter(0, 0, 10000, 0)
        Raw_Sheet.autofilter(0, 5, 10000, 0)
        Sens_Sheet.set_column(0, 13, 20)
        Sens_Sheet.autofilter(0, 0, 10000, 0)
        Sens_Sheet.autofilter(0, 2, 10000, 0)
        Blocking_Sheet.set_column(0, 13, 25)
        Blocking_Sheet.autofilter(0, 0, 10000, 0)
        Blocking_Sheet.autofilter(0, 4, 10000, 0)

        workbook.close()

        #replace original xlsx file with new xlsx file containing the plots
        os.remove(self.workbook_name)
        os.rename(output_workbook_name, self.workbook_name)
    
    def initiate(self):
        
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)
        global ber_success
        ber_success = True
        i = 1
        j = 1
        k = 1

        for frequency in self.settings.freq_list_hz:
            
            self.siggen.setFrequency(frequency)

            blocking_raw_measurement_record = {
                    'Frequency [MHz]':frequency/1e6,
                    'Input Power [dBm]':0,
                    self.settings.err_rate_type +' [%]':0,
                    'RSSI':0,
                    'Blocker Freq. Offset [MHz]':0,
                    'Blocker Abs. Power [dBm]':0,     
                }
            
            for sigGen_power in self.settings.siggen_power_list_dBm:
                
                self.siggen.setAmplitude(sigGen_power)
                
                if self.settings.err_rate_type == 'BER':
                    err_percent,done_percent,rssi = self.wstk.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency)
                elif self.settings.err_rate_type == 'PER':
                    err_percent,done_percent,rssi = self.wstk.measurePer(npackets=100,interpacket_delay_s = 0.001,frequency_Hz=frequency,tx_start_function=self.siggen.sendTrigger)
                else:
                    raise TypeError('Not recognized error rate string!')
                if i == 1 and done_percent == 0 and rssi == 0:
                    print(self.settings.err_rate_type +" measurement failed!")
                    ber_success = False
                    break

                blocking_raw_measurement_record['Input Power [dBm]'] = sigGen_power-self.settings.cable_attenuation_dB
                blocking_raw_measurement_record[self.settings.err_rate_type +' [%]'] = err_percent
                blocking_raw_measurement_record['RSSI'] = rssi
                blocking_raw_measurement_record['Blocker Freq. Offset [MHz]'] = " "
                blocking_raw_measurement_record['Blocker Abs. Power [dBm]'] = " "
                
                self.sheet_rawdata.write(i, 0, frequency/1e6)
                self.sheet_rawdata.write(i, 1, sigGen_power-self.settings.cable_attenuation_dB)
                self.sheet_rawdata.write(i, 2, err_percent)
                self.sheet_rawdata.write(i, 3, rssi)
                self.sheet_rawdata.write(i, 4, " ")
                self.sheet_rawdata.write(i, 5, " ")
                i += 1

                record_df = pd.DataFrame(blocking_raw_measurement_record,index=[0])
                record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                self.logger.info("\n"+record_df.to_string())

                if err_percent >= self.settings.err_rate_threshold_percent:

                    self.sheet_sensdata.write(j, 0, frequency/1e6)
                    self.sheet_sensdata.write(j, 1, sigGen_power - self.settings.cable_attenuation_dB)
                    self.sheet_sensdata.write(j, 2, err_percent)
                    self.sheet_sensdata.write(j, 3, rssi)
                    j += 1

                    break

            self.siggen.setAmplitude(sigGen_power + self.settings.desired_power_relative_to_sens_during_blocking_test_dB)
            self.specan.setSigGenOutput_toggle(on_off=True)

            for blocker_offset_freq in self.settings.blocker_offset_freq_list_Hz:
                
                self.specan.setSigGenFreq_Hz(frequency + blocker_offset_freq)

                for blocker_power in self.settings.blocker_power_list_dBm:

                    self.specan.setSigGenPower_dBm(blocker_power)
                    if self.settings.err_rate_type == 'BER':
                        err_percent,done_percent,rssi = self.wstk.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency)
                    elif self.settings.err_rate_type == 'PER':
                        err_percent,done_percent,rssi = self.wstk.measurePer(npackets=100,interpacket_delay_s = 0.001,frequency_Hz=frequency,tx_start_function=self.siggen.sendTrigger)
                    else:
                        raise TypeError('Not recognized error rate string!')
                    if i == 1 and done_percent == 0 and rssi == 0:
                        print(self.settings.err_rate_type + " measurement failed, blocking test cancelled!")
                        ber_success = False
                        break
                   
                    blocking_raw_measurement_record['Input Power [dBm]'] = sigGen_power + self.settings.desired_power_relative_to_sens_during_blocking_test_dB - self.settings.cable_attenuation_dB
                    blocking_raw_measurement_record[self.settings.err_rate_type +' [%]'] = err_percent
                    blocking_raw_measurement_record['RSSI'] = rssi
                    blocking_raw_measurement_record['Blocker Freq. Offset [MHz]'] = blocker_offset_freq/1e6
                    blocking_raw_measurement_record['Blocker Abs. Power [dBm]'] = blocker_power-self.settings.blocker_cable_attenuation_dB
                    
                    self.sheet_rawdata.write(i, 0, frequency/1e6)
                    self.sheet_rawdata.write(i, 1, sigGen_power + self.settings.desired_power_relative_to_sens_during_blocking_test_dB - self.settings.cable_attenuation_dB)
                    self.sheet_rawdata.write(i, 2, err_percent)
                    self.sheet_rawdata.write(i, 3, rssi)
                    self.sheet_rawdata.write(i, 4, blocker_offset_freq/1e6)
                    self.sheet_rawdata.write(i, 5, blocker_power-self.settings.blocker_cable_attenuation_dB)
                    i += 1

                    record_df = pd.DataFrame(blocking_raw_measurement_record,index=[0])
                    record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                    self.logger.info("\n"+record_df.to_string())

                    if err_percent >= self.settings.err_rate_threshold_percent:

                        self.sheet_blockingdata.write(k, 0, frequency/1e6)
                        self.sheet_blockingdata.write(k, 1, sigGen_power + self.settings.desired_power_relative_to_sens_during_blocking_test_dB - self.settings.cable_attenuation_dB)
                        self.sheet_blockingdata.write(k, 2, blocker_offset_freq/1e6)
                        self.sheet_blockingdata.write(k, 3, blocker_power-self.settings.blocker_cable_attenuation_dB)
                        self.sheet_blockingdata.write(k, 4, err_percent)
                        k += 1

                        break

            self.specan.setSigGenOutput_toggle(on_off=False)

        self.wstk._driver.reset()

    def stop(self):
        # if workbook already exists no need to close again
        if not path.isfile(self.workbook_name):
            self.logger.info("excel workbook closed")
            if hasattr(self,'workbook'):
                self.workbook.close()

        try:
            if hasattr(self,'siggen'):
                self.siggen.toggleModulation(False)
                self.siggen.toggleRFOut(False)
                self.siggen.logger.handlers.clear()
                del self.siggen
        # if someone already closed the visa session
        except visaerrors.InvalidSession:
            self.siggen.logger.handlers.clear() 
            self.initialize_siggen() 
            self.siggen.toggleModulation(False) 
            self.siggen.toggleRFOut(False)
            self.siggen.logger.handlers.clear()
            del self.siggen

        try:
            if hasattr(self,'specan'):
                self.specan.setSigGenOutput_toggle(False)
                self.specan.logger.handlers.clear()
                del self.specan
        # if someone already closed the visa session
        except visaerrors.InvalidSession:
            self.specan.logger.handlers.clear() 
            self.initialize_specan_Generator() 
            self.specan.setSigGenOutput_toggle(False)
            self.specan.logger.handlers.clear()
            del self.specan

        try:
            if hasattr(self,'wstk'):
                self.wstk._driver.reset()
                self.wstk.logger.handlers.clear()
                self.wstk.close()
                del self.wstk
        # if someone already closed the visa session
        except visaerrors.InvalidSession:
            self.wstk.logger.handlers.clear() 
            self.wstk._driver.reset()
            self.wstk.logger.handlers.clear()
            self.wstk.close()
            del self.wstk        

    def measure(self)->pd.DataFrame:
        """
        Initiate the measurement.

        :return: The measured data
        :rtype: pandas.DataFrame
        """
        self.initialize_siggen()
        self.initialize_wstk()
        self.initialize_reporter()
        
        if (self.settings.siggen_power_list_dBm[0] - self.settings.cable_attenuation_dB) > 10:
            raise ValueError("Too high input power injected!")

        self.initialize_specan_Generator()

        # if self.settings.measure_with_CTUNE_w_SA:
        #     self.ctune_w_sa()

        if self.settings.measure_with_CTUNE_w_SG:
            self.ctune_w_sg()

        self.initiate()

        self.stop()

        self.Py_to_Excel_plotter()

        if ber_success:
            df = self.get_dataframe(self.backup_csv_filename)
            self.logger.debug(df.to_string())
            self.logger.info("\nDone with measurements")

            return df
       
    def __del__(self):
        self.stop()

class FreqOffset_Sensitivity(Sensitivity):
    
    @dataclass
    class Settings(Sensitivity.Settings):

        freq_offset_start_Hz: int = -100e3   
        freq_offset_stop_Hz: int = 100e3     
        freq_offset_steps: int = 21
        freq_offset_list_Hz: list|None = None

        stop_at_no_signal:bool = True # if the frequency and power values are so out of bounds that the rx cant happen,
                                 # do not sweep the rest of the values, turn this False for 'bathtub curve'
                                 # makes measurement MUCH slower, but sweeps every value

        freq_offset_logger_settings: Logger.Settings = Logger.Settings()
                

    def __init__(self,settings:Settings,chip_name:str,board_name:str):
        """
        Initialize measurement class

        :param Settings settings: Settings dataclass containing all the configuration
        :param str chip_name : Name of IC being tested, only used in reporting
        :param str board_name: Name of board, containg the IC, only used in reporting
        :param str logfile_name: If initialized, separate logfile will be created for this measurement
        :param bool console_logging: Enable console logging, True by default
        """
        self.settings = settings
        self.chip_name = chip_name
        self.board_name = board_name

        timestamp = dt.now().timestamp()
        self.workbook_name = self.board_name + '_FreqOffset_Sensitivity_results_'+str(int(timestamp))+'.xlsx'

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)

        if self.settings.freq_offset_list_Hz is None:
            self.settings.freq_offset_list_Hz = np.linspace(
                                                    self.settings.freq_offset_start_Hz,
                                                    self.settings.freq_offset_stop_Hz,
                                                    self.settings.freq_offset_steps,
                                                    dtype=float
                                                    )
    
    def initialize_reporter(self):
        self.workbook = xlsxwriter.Workbook(self.workbook_name)

        self.sheet_sum = self.workbook.add_worksheet('Summary')
        self.sheet_sum.write(0, 0, 'Chip name: ' + self.chip_name)
        self.sheet_sum.write(1, 0, 'Board name: ' + self.board_name)

        self.sheet_parameters = self.workbook.add_worksheet('Parameters')
        self.sheet_parameters.write(0, 0, 'Modulation')
        self.sheet_parameters.write(0, 1, 'Data Rate [kbps]')
        self.sheet_parameters.write(0, 2, 'Deviation [kHz]')
        self.sheet_parameters.write(0, 3, 'BbT')
        self.sheet_parameters.write(1, 0, self.settings.siggen_modulation_type)
        self.sheet_parameters.write(1, 1, self.settings.siggen_modulation_symbolrate_sps / 1e3)
        self.sheet_parameters.write(1, 2, self.settings.siggen_modulation_deviation_Hz / 1e3)
        self.sheet_parameters.write(1, 3, self.settings.siggen_filter_BbT)

        self.sheet_rawdata = self.workbook.add_worksheet('RawData')
        self.sheet_rawdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_rawdata.write(0, 1, 'Freq. Offset [kHz]')
        self.sheet_rawdata.write(0, 2, 'Input Power [dBm]')
        self.sheet_rawdata.write(0, 3, self.settings.err_rate_type +' [%]')
        self.sheet_rawdata.write(0, 4, 'RSSI')
        
        self.sheet_sensdata = self.workbook.add_worksheet('SensData')
        self.sheet_sensdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_sensdata.write(0, 1, 'Freq. Offset [kHz]')
        self.sheet_sensdata.write(0, 2, 'Sensitivity [dBm]')
        self.sheet_sensdata.write(0, 3, self.settings.err_rate_type +' [%]')
        self.sheet_sensdata.write(0, 4, 'RSSI')

        self.row = 1

        self.backup_csv_filename = "backup_csv_freqoffset-sens_raw.csv"

        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)

    def Py_to_Excel_plotter(self):
        # Import raw vs power data from existing xlsx
        summary = pd.read_excel(self.workbook_name, sheet_name="Summary")
        parameters = pd.read_excel(self.workbook_name, sheet_name="Parameters")
        raw_data = pd.read_excel(self.workbook_name, sheet_name="RawData")
        sens_data = pd.read_excel(self.workbook_name, sheet_name="SensData")
        
        # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
        output_workbook_name = "Plot" + self.workbook_name
        workbook = xlsxwriter.Workbook(output_workbook_name)
        Summary_Sheet = workbook.add_worksheet(name= 'Summary')
        Parameters_Sheet = workbook.add_worksheet(name= 'Parameters')
        Raw_Sheet = workbook.add_worksheet(name= 'RawData')
        Sens_Sheet = workbook.add_worksheet(name= 'SensData')
        Chart_Sheet = workbook.add_worksheet(name= 'Charts')
        # Copy imported data to this new xlsx
        col_name: str
        for i, col_name in enumerate(sens_data.columns):
            Sens_Sheet.write(0, i, col_name)
            Sens_Sheet.write_column(1, i, sens_data[col_name])
        col_name: str
        for i, col_name in enumerate(raw_data.columns):
            Raw_Sheet.write(0, i, col_name)
            Raw_Sheet.write_column(1, i, raw_data[col_name])
        col_name: str
        for i, col_name in enumerate(parameters.columns):
            Parameters_Sheet.write(0, i, col_name)
            Parameters_Sheet.write_column(1, i, parameters[col_name])
        col_name: str
        for i, col_name in enumerate(summary.columns):
            Summary_Sheet.write(0, i, col_name)
            Summary_Sheet.write_column(1, i, summary[col_name])

        # Create empty plot for frequency-offset vs Sensitivity
        plot_sens = workbook.add_chart({"type" : "scatter"})
        # Plot the Fundamental frequency-offset vs Sensitivity
        plot_sens.add_series({"categories" : "=SensData!$B$2:$B$10000",
                    "values" : "=SensData!$C$2:$C$10000",
                    "name" : "Sens."})
        plot_sens.set_x_axis({"name" : "Frequency-offset [kHz]"})
        plot_sens.set_y_axis(({"name" : "Sensitivity [dBm]"}))
        plot_sens.set_title({'name': 'Sensitivity vs Frequency-offset', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "1", plot_sens, {'x_scale': 1.2, 'y_scale': 1.4})
        
        # shaping and filtering
        Parameters_Sheet.set_column(0, 13, 16)
        Raw_Sheet.set_column(0, 13, 16)
        Sens_Sheet.autofilter(0, 0, 10000, 0)
        Sens_Sheet.set_column(0, 13, 16)

        workbook.close()

        #replace original xlsx file with new xlsx file containing the plots
        os.remove(self.workbook_name)
        os.rename(output_workbook_name, self.workbook_name)
    
    def initiate(self):
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)
        global ber_success
        ber_success = True
        i = 1
        k = 1

        for frequency in self.settings.freq_list_hz:

            # self.siggen.setFrequency(frequency)

            freqoffset_sens_raw_measurement_record = {
                    'Frequency [MHz]':frequency/1e6,
                    'Freq. Offset [kHz]':0,
                    'Input Power [dBm]':0,
                     self.settings.err_rate_type + ' [%]':0,
                    'RSSI':0,   
                }

            for freq_offset in self.settings.freq_offset_list_Hz:

                self.siggen.setFrequency(frequency + freq_offset)
                j = 1   #dummy counter to log sensitivity if BER measurement fails between two input-power steps

                for sigGen_power in self.settings.siggen_power_list_dBm:
                    
                    self.siggen.setAmplitude(sigGen_power)

                    if self.settings.err_rate_type == 'BER':
                        err_percent,done_percent,rssi = self.wstk.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=frequency)
                    elif self.settings.err_rate_type == 'PER':
                        err_percent,done_percent,rssi = self.wstk.measurePer(npackets=100,interpacket_delay_s = 0.001,frequency_Hz=frequency,tx_start_function=self.siggen.sendTrigger)
                    else:
                        raise TypeError('Not recognized error rate string!')
                    
                    freqoffset_sens_raw_measurement_record['Freq. Offset [kHz]'] = freq_offset/1e3
                    freqoffset_sens_raw_measurement_record['Input Power [dBm]'] = sigGen_power-self.settings.cable_attenuation_dB
                    freqoffset_sens_raw_measurement_record[self.settings.err_rate_type + ' [%]'] = err_percent
                    freqoffset_sens_raw_measurement_record['RSSI'] = rssi
                    
                    self.sheet_rawdata.write(i, 0, frequency/1e6)
                    self.sheet_rawdata.write(i, 1, freq_offset/1e3)
                    self.sheet_rawdata.write(i, 2, sigGen_power-self.settings.cable_attenuation_dB)
                    self.sheet_rawdata.write(i, 3, err_percent)
                    self.sheet_rawdata.write(i, 4, rssi)
                    i += 1

                    record_df = pd.DataFrame(freqoffset_sens_raw_measurement_record,index=[0])
                    record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                    self.logger.info("\n"+record_df.to_string())

                    if err_percent >= self.settings.err_rate_threshold_percent:

                        self.sheet_sensdata.write(k, 0, frequency/1e6)
                        self.sheet_sensdata.write(k, 1, freq_offset/1e3)
                        self.sheet_sensdata.write(k, 2, sigGen_power-self.settings.cable_attenuation_dB)
                        self.sheet_sensdata.write(k, 3, err_percent)
                        self.sheet_sensdata.write(k, 4, rssi)
                        k += 1
                        if self.settings.stop_at_no_signal:
                            break

                    if done_percent == 0 and j == 1 and rssi == 0:                     
                        print(self.settings.err_rate_type + " measurement failed!")
                        ber_success = False
                        if self.settings.stop_at_no_signal:
                            break

                    if done_percent == 0 and j > 1:

                        self.sheet_sensdata.write(k, 0, frequency/1e6)
                        self.sheet_sensdata.write(k, 1, freq_offset/1e3)
                        self.sheet_sensdata.write(k, 2, self.settings.siggen_power_list_dBm[j-2]-self.settings.cable_attenuation_dB)
                        self.sheet_sensdata.write(k, 3, err_percent)
                        self.sheet_sensdata.write(k, 4, rssi)
                        k += 1
                        if self.settings.stop_at_no_signal:
                            break

                    j += 1

        self.wstk._driver.reset()  

class RSSI_Sweep(Sensitivity):
    
    @dataclass
    class Settings(Sensitivity.Settings):
        
        siggen_freq_start_Hz: int = 868e6   
        siggen_freq_stop_Hz: int = 928e6     
        siggen_freq_steps: int = 31
        siggen_freq_list_Hz: list|None = None

        siggen_logger_settings: Logger.Settings = Logger.Settings()
                

    def __init__(self,settings:Settings,chip_name:str,board_name:str):
        """
        Initialize measurement class

        :param Settings settings: Settings dataclass containing all the configuration
        :param str chip_name : Name of IC being tested, only used in reporting
        :param str board_name: Name of board, containg the IC, only used in reporting
        :param str logfile_name: If initialized, separate logfile will be created for this measurement
        :param bool console_logging: Enable console logging, True by default
        """
        self.settings = settings
        self.chip_name = chip_name
        self.board_name = board_name

        timestamp = dt.now().timestamp()
        self.workbook_name = self.board_name + '_RSSI_Sweep_results_'+str(int(timestamp))+'.xlsx'

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)

        if self.settings.siggen_freq_list_Hz is None:
            self.settings.siggen_freq_list_Hz = np.linspace(
                                                    self.settings.siggen_freq_start_Hz,
                                                    self.settings.siggen_freq_stop_Hz,
                                                    self.settings.siggen_freq_steps,
                                                    dtype=float
                                                    )
            
    def initialize_reporter(self):
        self.workbook = xlsxwriter.Workbook(self.workbook_name)

        self.sheet_sum = self.workbook.add_worksheet('Summary')
        self.sheet_sum.write(0, 0, 'Chip name: ' + self.chip_name)
        self.sheet_sum.write(1, 0, 'Board name: ' + self.board_name)

        self.sheet_rawdata = self.workbook.add_worksheet('RawData')
        self.sheet_rawdata.write(0, 0, 'Radio Frequency [MHz]')
        self.sheet_rawdata.write(0, 1, 'Injected Frequency [MHz]')
        self.sheet_rawdata.write(0, 2, 'Input Power [dBm]')
        self.sheet_rawdata.write(0, 3, 'RSSI')

        self.row = 1

        self.backup_csv_filename = "backup_csv_rssi-sweep_raw.csv"

        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)
    
    def Py_to_Excel_plotter(self):
        # Import raw vs power data from existing xlsx
        summary = pd.read_excel(self.workbook_name, sheet_name="Summary")
        raw_data = pd.read_excel(self.workbook_name, sheet_name="RawData")
        # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
        output_workbook_name = "Plot" + self.workbook_name
        workbook = xlsxwriter.Workbook(output_workbook_name)
        Summary_Sheet = workbook.add_worksheet(name= 'Summary')
        Raw_Sheet = workbook.add_worksheet(name= 'RawData')
        Chart_Sheet = workbook.add_worksheet(name= 'Charts')
        # Copy imported data to this new xlsx
        col_name: str
        for i, col_name in enumerate(raw_data.columns):
            Raw_Sheet.write(0, i, col_name)
            Raw_Sheet.write_column(1, i, raw_data[col_name])
        col_name: str
        for i, col_name in enumerate(summary.columns):
            Summary_Sheet.write(0, i, col_name)
            Summary_Sheet.write_column(1, i, summary[col_name])
    
        # Create empty freq plot
        plot = workbook.add_chart({"type" : "scatter"})
        # Plotting
        plot.add_series({"categories" : "=RawData!$B$2:$B$10000",
                    "values" : "=RawData!$D$2:$D$10000",
                    "name" : "RSSI vs Frequency"})
        plot.set_x_axis({"name" : "Frequency [MHz]"})
        plot.set_y_axis(({"name" : "RSSI"}))
        plot.set_title({'name': 'RSSI vs Frequency', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "1", plot, {'x_scale': 1.2, 'y_scale': 1.4})

        # Create empty power plot
        plot = workbook.add_chart({"type" : "scatter"})
        # Plotting
        plot.add_series({"categories" : "=RawData!$C$2:$C$10000",
                    "values" : "=RawData!$D$2:$D$10000",
                    "name" : "RSSI vs Power"})
        plot.set_x_axis({"name" : "Power input [dBm]"})
        plot.set_y_axis(({"name" : "RSSI"}))
        plot.set_title({'name': 'RSSI vs Power', 'name_font':{'name':'Calibri(Body)','size':12}})
        Chart_Sheet.insert_chart("A" + "22", plot, {'x_scale': 1.2, 'y_scale': 1.4})
        
        # shaping and filtering
        Raw_Sheet.set_column(0, 13, 20)
        Raw_Sheet.autofilter(0, 2, 10000, 0)

        workbook.close()

        #replace original xlsx file with new xlsx file containing the plots
        os.remove(self.workbook_name)
        os.rename(output_workbook_name, self.workbook_name)
    
    def initiate(self):
            
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)
        global ber_success
        ber_success = True
        i = 1

        for frequency in self.settings.freq_list_hz:

            self.wstk.receive(on_off=True, frequency_Hz=frequency, timeout_ms=1000)
            sleep(0.1)
            self.wstk._driver.rx(True)

            rssi_sweep_raw_measurement_record = {
                    'Radio Frequency [MHz]':frequency/1e6,
                    'Injected Frequency [MHz]':0,
                    'Input Power [dBm]':0,
                    'RSSI':0,   
                }

            for siggen_frequency in self.settings.siggen_freq_list_Hz:

                self.siggen.setFrequency(siggen_frequency)

                for sigGen_power in self.settings.siggen_power_list_dBm:
                        
                    self.siggen.setAmplitude(sigGen_power)
                    sleep(0.1)
                    rssi_value = self.wstk.readRSSI()
                    sleep(0.2)

                    rssi_sweep_raw_measurement_record['Injected Frequency [MHz]'] = siggen_frequency/1e6
                    rssi_sweep_raw_measurement_record['Input Power [dBm]'] = sigGen_power-self.settings.cable_attenuation_dB
                    rssi_sweep_raw_measurement_record['RSSI'] = rssi_value
                        
                    self.sheet_rawdata.write(i, 0, frequency/1e6)
                    self.sheet_rawdata.write(i, 1, siggen_frequency/1e6)
                    self.sheet_rawdata.write(i, 2, sigGen_power-self.settings.cable_attenuation_dB)
                    self.sheet_rawdata.write(i, 3, rssi_value)
                    i += 1

                    record_df = pd.DataFrame(rssi_sweep_raw_measurement_record,index=[0])
                    record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                    self.logger.info("\n"+record_df.to_string())

        self.wstk._driver.reset()

class Waterfall(Sensitivity):

    def __init__(self,settings:Sensitivity.Settings,chip_name:str,board_name:str):
        """
        Initialize measurement class

        :param Settings settings: Settings dataclass containing all the configuration
        :param str chip_name : Name of IC being tested, only used in reporting
        :param str board_name: Name of board, containg the IC, only used in reporting
        :param str logfile_name: If initialized, separate logfile will be created for this measurement
        :param bool console_logging: Enable console logging, True by default
        """
        self.settings = settings
        self.chip_name = chip_name
        self.board_name = board_name

        timestamp = dt.now().timestamp()
        self.workbook_name = self.board_name + '_Waterfall_results_'+str(int(timestamp))+'.xlsx'

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)

    def initialize_reporter(self):
        self.workbook = xlsxwriter.Workbook(self.workbook_name)

        self.sheet_sum = self.workbook.add_worksheet('Summary')
        self.sheet_sum.write(0, 0, 'Chip name: ' + self.chip_name)
        self.sheet_sum.write(1, 0, 'Board name: ' + self.board_name)

        self.sheet_parameters = self.workbook.add_worksheet('Parameters')
        self.sheet_parameters.write(0, 0, 'Modulation')
        self.sheet_parameters.write(0, 1, 'Data Rate [kbps]')
        self.sheet_parameters.write(0, 2, 'Deviation [kHz]')
        self.sheet_parameters.write(0, 3, 'BbT')
        self.sheet_parameters.write(1, 0, self.settings.siggen_modulation_type)
        self.sheet_parameters.write(1, 1, self.settings.siggen_modulation_symbolrate_sps / 1e3)
        self.sheet_parameters.write(1, 2, self.settings.siggen_modulation_deviation_Hz / 1e3)
        self.sheet_parameters.write(1, 3, self.settings.siggen_filter_BbT)

        self.sheet_rawdata = self.workbook.add_worksheet('RawData')
        self.sheet_rawdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_rawdata.write(0, 1, 'Input Power [dBm]')
        self.sheet_rawdata.write(0, 2, self.settings.err_rate_type +' [%]')
        self.sheet_rawdata.write(0, 3, 'RSSI')
        
        self.sheet_sensdata = self.workbook.add_worksheet('SensData')
        self.sheet_sensdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_sensdata.write(0, 1, 'Sensitivity [dBm]')
        self.sheet_sensdata.write(0, 2, self.settings.err_rate_type +' [%]')
        self.sheet_sensdata.write(0, 3, 'RSSI')

        self.row = 1

        self.backup_csv_filename = "backup_csv_waterfall_raw.csv"


        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)

    def initiate(self):
        
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)
        i = 1
        j = 1
        global ber_success
        ber_success = True

        for freq in self.settings.freq_list_hz:

            self.siggen.setFrequency(freq)

            waterfall_raw_measurement_record = {
                    'Frequency [MHz]':freq/1e6,
                    'Input Power [dBm]':0,
                    self.settings.err_rate_type +' [%]':0,
                    'RSSI':0,     
                }
            
            k = 1

            for siggen_power in self.settings.siggen_power_list_dBm:

                self.siggen.setAmplitude(siggen_power)
                if self.settings.err_rate_type == 'BER':
                    err_percent,done_percent,rssi = self.wstk.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=freq)
                elif self.settings.err_rate_type == 'PER':
                    err_percent,done_percent,rssi = self.wstk.measurePer(npackets=100,interpacket_delay_s = 0.001,frequency_Hz=freq,tx_start_function=self.siggen.sendTrigger)
                else:
                    raise TypeError('Not recognized error rate string!')
                if i == 1 and done_percent == 0 and rssi == 0:
                    print(self.settings.err_rate_type + " measurement failed!")
                    ber_success = False
                    break

                waterfall_raw_measurement_record['Input Power [dBm]'] = siggen_power-self.settings.cable_attenuation_dB
                waterfall_raw_measurement_record[self.settings.err_rate_type +' [%]'] = err_percent
                waterfall_raw_measurement_record['RSSI'] = rssi

                self.sheet_rawdata.write(i, 0, freq/1e6)
                self.sheet_rawdata.write(i, 1, siggen_power-self.settings.cable_attenuation_dB)
                self.sheet_rawdata.write(i, 2, err_percent)
                self.sheet_rawdata.write(i, 3, rssi)
                i += 1

                record_df = pd.DataFrame(waterfall_raw_measurement_record,index=[0])
                record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                self.logger.info("\n"+record_df.to_string())

                if k == 1 and err_percent >= self.settings.err_rate_threshold_percent:

                        self.sheet_sensdata.write(j, 0, freq/1e6)
                        self.sheet_sensdata.write(j, 1, siggen_power-self.settings.cable_attenuation_dB)
                        self.sheet_sensdata.write(j, 2, err_percent)
                        self.sheet_sensdata.write(j, 3, rssi)
                        j += 1
                        k += 1                       

        self.wstk._driver.reset()