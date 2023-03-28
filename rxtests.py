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

        :param float cable_attenuation_dB: total cable loss in the test setup between SigGen and DUT

        :param float siggen_power_start_dBm: Start SigGen power, cable loss not included
        :param float siggen_power_stop_dBm: Stop SigGen power, cabel loss not included
        :param int siggen_power_steps: Number of discrete SigGen power steps between stop and start values
        :param list siggen_power_list_dBm: Custom list of SigGen powers
                
        :param str wstk_com_port: COM port of the RAILTest device
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
        siggen_stream_type = "PN9" #see all available stream modes by searching for "RADio:CUSTom:DATA" in https://www.keysight.com/zz/en/assets/9018-40178/programming-guides/9018-40178.pdf
        siggen_filter_type = "Gaussian" #Gaussian or Nyquist
        siggen_filter_BbT = 0.5
        siggen_custom_on = True
        siggen_logger_settings: Logger.Settings = Logger.Settings()

        #WSTK settings
        wstk_com_port: str = ""
        wstk_logger_settings: Logger.Settings = Logger.Settings()

        # Tested chip and board names 


    def __init__(self,settings:Settings,chip_name:str,board_name:str):
        """
        Initialize measurement class

        :param Settings settings: TXCWSweep.Settings dataclass containing all the configuration
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
        self.siggen.setStreamType(self.settings.siggen_stream_type)
        self.siggen.toggleCustom(self.settings.siggen_custom_on)
        self.siggen.toggleModulation(True)
        self.siggen.toggleRFOut(True)
        if self.settings.siggen_power_list_dBm is None:
            self.settings.siggen_power_list_dBm = np.linspace(
                                                    self.settings.siggen_power_start_dBm,
                                                    self.settings.siggen_power_stop_dBm,
                                                    self.settings.siggen_power_steps,
                                                    dtype=float
                                                    )

    def initialize_wstk(self):
        self.wstk = WSTK_RAILTest(self.settings.wstk_com_port,logger_settings=self.settings.wstk_logger_settings)

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
        self.sheet_rawdata.write(0, 2, 'BER [%]')
        self.sheet_rawdata.write(0, 3, 'RSSI')
        
        self.sheet_sensdata = self.workbook.add_worksheet('SensData')
        self.sheet_sensdata.write(0, 0, 'Frequency [MHz]')
        self.sheet_sensdata.write(0, 1, 'Sensitivity [dBm]')
        self.sheet_sensdata.write(0, 2, 'BER [%]')

        self.row = 1

        self.backup_csv_filename = "backup_csv_rx_raw.csv"


        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)

    def initiate(self):

        i = 1
        j = 1
        for freq in self.settings.freq_list_hz:

            self.siggen.setFrequency(freq)

            rx_raw_measurement_record = {
                    'Frequency [MHz]':freq/1e6,
                    'Input Power [dBm]':0,
                    'BER [%]':0,
                    'RSSI':0,     
                }
            
            rx_sens_measurement_record = {
                            'Frequency [MHz]':freq/1e6,
                            'Input Power [dBm]':0,
                            'BER [%]':0,
                            'RSSI':0,     
                        }

            for siggen_power in self.settings.siggen_power_list_dBm:

                self.siggen.setAmplitude(siggen_power)
                ber_percent,done_percent,rssi = self.wstk.measureBer(nbytes=10000,timeout_ms=1000,frequency_Hz=freq)

                rx_raw_measurement_record['Input Power [dBm]'] = siggen_power-self.settings.cable_attenuation_dB
                rx_raw_measurement_record['BER [%]'] = ber_percent
                rx_raw_measurement_record['RSSI'] = rssi

                self.sheet_rawdata.write(i, 0, freq/1e6)
                self.sheet_rawdata.write(i, 1, siggen_power-self.settings.cable_attenuation_dB)
                self.sheet_rawdata.write(i, 2, ber_percent)
                self.sheet_rawdata.write(i, 3, rssi)
                i += 1

                record_df = pd.DataFrame(rx_raw_measurement_record,index=[0])
                record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                self.logger.info("\n"+record_df.to_string())

                if ber_percent >= 0.1:
                        
                        rx_sens_measurement_record['Input Power [dBm]'] = siggen_power-self.settings.cable_attenuation_dB
                        rx_sens_measurement_record['BER [%]'] = ber_percent
                        rx_sens_measurement_record['RSSI'] = rssi

                        self.sheet_sensdata.write(j, 0, freq/1e6)
                        self.sheet_sensdata.write(j, 1, siggen_power-self.settings.cable_attenuation_dB)
                        self.sheet_sensdata.write(j, 2, ber_percent)
                        self.sheet_sensdata.write(j, 3, rssi)
                        j += 1

                        break                       

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

        self.initiate()

        self.stop()

        df = self.get_dataframe(self.backup_csv_filename)
        self.logger.debug(df.to_string())
        self.logger.info("\nDone with measurements")

        return df
    
    def __del__(self):
        self.stop()
