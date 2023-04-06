from pydoc import visiblename

from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pyspecan.pySpecAn import SpecAn, RS_SpectrumAnalyzer
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




class TXCWSweep():
    """
    Sweeping and measuring most parameters of an EFR device transmitting
    a carrier wave signal. 

    Required instruments: 
    - SiLabs EFR with RAILTest configured
    - Spectrum Analyzer
    - Optional Lab Power Supply
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
        :param int harm_order_up_to: Number of harmonics to measure, fundamental included

        :param bool psu_present: Power supply presence variable, default False, meaning internal 3.3V is used
        :param str psu_address: VISA address of PSU, if serial is used, it is a COM port, check PyVISA documentation
        :param float pavdd_min: Minimum supply voltage
        :param float pavdd_max: Maximum supply voltage
        :param int pavdd_num_steps: Number of discrete voltage steps between stop and start values
        :param list pavdd_levels: Custom list of voltages
        
        :param int min_pwr_state: Maximum power setting for EFR internal amplifier
        :param int max_pwr_state: Minimum power setting for EFR internal amplifier
        :param int pwr_num_steps: Number of amplifier power values between stop and start values
        :param list pwr_levels: Custom ist of power values
        
        :param str specan_address: VISA address of Spectrum Analyzer,can check PyVISA documentation
        :param int specan_span_hz: SA span in Hz
        :param int specan_rbw_hz: SA resolution bandwidth in Hz
        :param int specan_ref_level_dbm: SA reference level in dBm
        :param str specan_detector_type: SA detector type, directly passed to pySpecAn
        :param float specan_ref_offset: SA reference offset

        :param str wstk_com_port: COM port of the RAILTest device
        """
        #Frequency range settings
        freq_start_hz: int = 868e6
        freq_stop_hz: int = 928e6
        freq_num_steps: int = 2
        freq_list_hz: list|None = None
        harm_order_up_to: int = 3

        logger_settings: Logger.Settings = Logger.Settings()

        #Supply settings
        psu_present: bool = False
        psu_address: str = "ASRL8::INSTR"
        pavdd_min: float = 2.0
        pavdd_max: float = 3.6
        pavdd_num_steps: int = 4
        pavdd_levels: list|None = None
        psu_logger_settings: Logger.Settings = Logger.Settings()
        
        #Power settings
        min_pwr_state: int = 0 
        max_pwr_state: int = 240
        pwr_num_steps: int = 24
        pwr_levels: list|None = None
        pwr_format:str = 'raw'
        
        #SA settings 
        specan_address: str = 'TCPIP::169.254.250.234::INSTR'
        specan_span_hz: int = 10e6
        specan_rbw_hz: int = 1e6
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
        self.workbook_name = self.board_name + '_Raw_PAVDD_Freq_vs_Power-Harmonic-Current_results_'+str(int(timestamp))+'.xlsx'

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)


    def initialize_psu(self):
        if self.settings.pavdd_levels is None:
            self.settings.pavdd_levels = np.linspace(
                                                    self.settings.pavdd_min,
                                                    self.settings.pavdd_max,
                                                    self.settings.pavdd_num_steps,
                                                    dtype=float
                                                    )
        else:
            self.settings.pavdd_max = max(self.settings.pavdd_levels)
        if self.settings.psu_present:
            self.psu = pyPSU.PSU(self.settings.psu_address,logger_settings = self.settings.psu_logger_settings)
            self.psu.selectOutput(1)
            self.psu.toggleOutput(True)
            self.psu.setVoltage(self.settings.pavdd_max)
        else:
            self.settings.pavdd_levels = [3.3]
            self.settings.pavdd_max = max(self.settings.pavdd_levels)

    def initialize_specan(self):
        self.specan = SpecAn(resource=self.settings.specan_address,logger_settings=self.settings.specan_logger_settings)
        self.specan.reset()
        self.specan.updateDisplay(on_off=True)
        self.specan.setMode('single')
        self.specan.setSpan(self.settings.specan_span_hz)
        self.specan.setRBW(self.settings.specan_rbw_hz)
        self.specan.setRefLevel(self.settings.specan_ref_level_dbm)
        self.specan.setDetector(self.settings.specan_detector_type)
        self.specan.setRefOffset(self.settings.specan_ref_offset)

    def initialize_wstk(self):
        self.wstk = WSTK_RAILTest_Driver(self.settings.wstk_com_port,logger_settings=self.settings.wstk_logger_settings)

        self.wstk.reset()
        self.wstk.rx(on_off=False)
        self.wstk.setTxTone(on_off=True, mode="CW")

        if self.settings.freq_list_hz is None:
            self.settings.freq_list_hz = np.linspace(
                                                    self.settings.freq_start_hz,
                                                    self.settings.freq_stop_hz,
                                                    self.settings.freq_num_steps,
                                                    dtype=float
                                                    )
        if self.settings.pwr_levels is None:
            self.settings.pwr_levels = np.linspace(self.settings.min_pwr_state, self.settings.max_pwr_state, self.settings.pwr_num_steps, dtype=int)

    def initialize_reporter(self):
        self.workbook = xlsxwriter.Workbook(self.workbook_name)
        self.sheet_sum = self.workbook.add_worksheet('Summary')
        self.sheet_sum.write(0, 0, 'Chip name: ' + self.chip_name)
        self.sheet_sum.write(1, 0, 'Board name: ' + self.board_name)

        harmonics = []
        for i in range(1, self.settings.harm_order_up_to + 1):
            harmonics.append(i)
        self.sheet_sum.write(2, 0, 'Harmonic orders measured: ' + str(harmonics))
        self.sheet_sum.write(3, 0, 'Raw power levels swept: ' + str(self.settings.pwr_levels))
        self.sheet_sum.write(5, 0, 'Test frequencies [MHz]:')
        for i, f in enumerate(self.settings.freq_list_hz):
            self.sheet_sum.write(6+i, 0, str(f/1e6))
        self.sheet_sum.write(5, 3, 'Test supply voltages [V]:')
        for j, V in enumerate(self.settings.pavdd_levels):
            self.sheet_sum.write(6+j, 3, str(V))

        self.worksheet = self.workbook.add_worksheet('RawData')
        self.worksheet.write(0, 0, 'Frequency [MHz]')
        self.worksheet.write(0, 1, 'PA raw values')
        self.worksheet.write(0, 2, 'PAVDD [V]')
        self.worksheet.write(0, 3, 'TX current [mA]')
        self.worksheet.write(0, 4, 'Fundamental [dBm]')
        for r in range(5, self.settings.harm_order_up_to+4):
            w = r - 3 
            self.worksheet.write(0, r, 'Harmonic #%d [dBm]' % w)
        self.row = 1

        self.backup_csv_filename = "backup_csv.csv"


        if path.exists(self.backup_csv_filename):
            remove(self.backup_csv_filename)

    def initiate(self):
        for freq in self.settings.freq_list_hz:

            self.wstk.setTxTone(on_off=False, mode="CW")
            self.wstk.setDebugMode(on_off=True)
            self.wstk.freqOverride(freq)
            self.wstk.setTxTone(on_off=True, mode="CW")

            for pavdd in self.settings.pavdd_levels:
                if self.settings.psu_present:
                    self.psu.setVoltage(pavdd)
                    sleep(0.1)
                # measured power levels at fundamental and harmonics
                meas_sum2D = np.empty((len(self.settings.pwr_levels), self.settings.harm_order_up_to))
                measured_power_curr = np.empty(len(self.settings.pwr_levels))
                # power level iterations
                for k,pl in enumerate(self.settings.pwr_levels):
                
                    n = 1
                    tx_measurement_record = {
                        'Frequency [MHz]':freq,
                        'PAVDD [V]':pavdd,
                        'PA raw values':pl,
                        'TX current [mA]':0,
                        'Fundamental [dBm]':0,      
                    }
                    
                    while n <= self.settings.harm_order_up_to:
                        
                        self.specan.setFrequency(n * freq)

                    
                        measured_power = np.empty(len(self.settings.pwr_levels))

                        
                        self.wstk.setTxTone(on_off=False, mode="CW")
                        self.wstk.setPower(value=pl, format=self.settings.pwr_format)
                        self.wstk.setTxTone(on_off=True, mode="CW")
                        self.specan.initiate()
                        marker = self.specan.getMaxMarker()
                        measured_power[k] = marker.value
                        meas_sum2D[k,n-1] = marker.value
                        
                        if n == 1:
                            if self.settings.psu_present:
                                i = self.psu.measCurrent() * 1000
                                #print(pl, i)
                                measured_power_curr[k] = i
                                tx_measurement_record['TX current [mA]'] = i
                            else:
                                measured_power_curr[k] = 0
                            
                            
                            tx_measurement_record['Fundamental [dBm]'] = marker.value
                        else:
                            tx_measurement_record['Harmonic #'+str(n) +' [dBm]'] = marker.value
                        n += 1 

                    record_df = pd.DataFrame(tx_measurement_record,index=[0])
                    record_df.to_csv(self.backup_csv_filename, mode='a', header=not path.exists(self.backup_csv_filename),index=False)
                    self.logger.info("\n"+record_df.to_string())
                voltage = np.empty(len(self.settings.pwr_levels))
                freqs_sheet = np.empty(len(self.settings.pwr_levels))
                for i in range(len(self.settings.pwr_levels)):
                    voltage[i] = pavdd
                    freqs_sheet[i] = freq/1e6
                if type(self.settings.pwr_levels) == list:
                    results = np.c_[(freqs_sheet.T, self.settings.pwr_levels, voltage.T, measured_power_curr.T, meas_sum2D)]
                else:
                    results = np.c_[(freqs_sheet.T, self.settings.pwr_levels.T, voltage.T, measured_power_curr.T, meas_sum2D)]
                column = 0
                for col, data in enumerate(results.T):
                    self.worksheet.write_column(self.row, col, data)  
                self.row = self.row + len(self.settings.pwr_levels) 

    def stop(self):
        # if workbook already exists no need to close again
        if not path.isfile(self.workbook_name):
            self.logger.info("excel workbook closed")
            if hasattr(self,'workbook'):
                self.workbook.close()

        if self.settings.psu_present:
            try:
                if hasattr(self,'psu'):
                    self.psu.toggleOutput(False)
                    self.psu.logger.handlers.clear()
                    del self.psu
            # if someone already closed the visa session
            except visaerrors.InvalidSession:
                self.psu.logger.handlers.clear() # clear psu logger otherwise it will duplicate log
                self.initialize_psu() #reinitialize psu session, ugly I know, sorry
                self.psu.toggleOutput(False) # turn off output
                self.psu.logger.handlers.clear()
                del self.psu
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
        
        self.initialize_psu()
        self.initialize_specan()
        self.initialize_wstk()
        self.initialize_reporter()

        self.initiate()

        self.stop()

        df = self.get_dataframe(self.backup_csv_filename)
        Py_to_Excel_plotter(self.workbook_name,self.settings.harm_order_up_to)
        self.logger.debug(df.to_string())
        self.logger.info("\nDone with measurements")

        return df
    def __del__(self):
        self.stop()

    # # number of frequency sweep points or discrete frequencies can be added below in "frequencies" list
    # freq_start = 868e6
    # freq_stop = 928e6
    # freq_number_steps = 2
    # #frequencies = np.linspace(freq_start, freq_stop, freq_number_steps, dtype=float)
    # frequencies = [868e6,920e6]

    # # number of PAVDD measurement sweep points or discrete PA supply voltage levels can be added below in "pavdd_levels" list
    # psu_present = True
    # PAVDD_min = 2.0
    # PAVDD_max = 3.6
    # PAVDD_number_steps = 2
    # #pavdd_levels = np.linspace(PAVDD_min, PAVDD_max, PAVDD_number_steps, dtype=float)
    # pavdd_levels = [3.3,3.4]
    # PAVDD_max = max(pavdd_levels)

    # if not  psu_present:
    #     pavdd_levels = [3.3]
    #     PAVDD_max = max(pavdd_levels)

    # # number of raw power sweep measurement points or discrete raw power values can be added below in "power_levels" list
    # min_pwr_state = 0
    # max_pwr_state = 240
    # pwr_number_steps = 24
    # power_levels = np.linspace(min_pwr_state, max_pwr_state, pwr_number_steps, dtype=int)
    # #power_levels = [10, 100, 240]

    # # highest harmonic order to measure
    # harm_order_up_to = 3

    # # SA settings
    # specan_address = 'TCPIP::169.254.250.234::INSTR'
    # span = 10e6
    # RBW = 1e6
    # ref_level = 20
    # detector_type = "RMS"
    # ref_offset = 0.3
    # specan = SpecAn(resource=specan_address)

    # specan.command("SYST:DISP:UPD ON")
    # specan.setMode('single')
    # specan.setSpan(span)
    # specan.setRBW(RBW)
    # specan.setRefLevel(ref_level)
    # specan.setDetector(detector_type)
    # specan.setRefOffset(ref_offset)

    # if psu_present:
    #     psu = pyPSU.PSU("ASRL8::INSTR")
    #     psu.selectOutput(1)
    #     psu.toggleOutput(True)
    #     psu.setVoltage(PAVDD_max)
    #     sleep(0.1)


    

    # timestamp = dt.now().timestamp()
    # workbook_name = board_name + '_Raw_PAVDD_Freq_vs_Power-Harmonic-Current_results_'+str(int(timestamp))+'.xlsx'
    # workbook = xlsxwriter.Workbook(workbook_name)
    # sheet_sum = workbook.add_worksheet('Summary')
    # sheet_sum.write(0, 0, 'Chip name: ' + chip_name)
    # sheet_sum.write(1, 0, 'Board name: ' + board_name)

    # harmonics = []
    # for i in range(1, harm_order_up_to + 1):
    #     harmonics.append(i)
    # sheet_sum.write(2, 0, 'Harmonic orders measured: ' + str(harmonics))
    # sheet_sum.write(3, 0, 'Raw power levels swept: ' + str(power_levels))
    # sheet_sum.write(5, 0, 'Test frequencies [MHz]:')
    # for i, f in enumerate(frequencies):
    #     sheet_sum.write(6+i, 0, str(f/1e6))
    # sheet_sum.write(5, 3, 'Test supply voltages [V]:')
    # for j, V in enumerate(pavdd_levels):
    #     sheet_sum.write(6+j, 3, str(V))

    # worksheet = workbook.add_worksheet('RawData')
    # worksheet.write(0, 0, 'Frequency [MHz]')
    # worksheet.write(0, 1, 'PA raw values')
    # worksheet.write(0, 2, 'PAVDD [V]')
    # worksheet.write(0, 3, 'TX current [mA]')
    # worksheet.write(0, 4, 'Fundamental [dBm]')
    # for r in range(5, harm_order_up_to+4):
    #     w = r - 3 
    #     worksheet.write(0, r, 'Harmonic #%d [dBm]' % w)
    # row = 1

    # backup_csv_filename = "backup_csv.csv"


    # if path.exists(backup_csv_filename):
    #     remove(backup_csv_filename)
    # exec_timestamp_start = dt.now().timestamp()

    
    
    # #wstk.reset()


    # # use pandas data frame instead??
    # Py_to_Excel_plotter(workbook_name, harm_order_up_to)

    # final_df  = pd.read_csv(
    #     backup_csv_filename,
    #     index_col = [0, 1,2]
    # )
    # print(final_df.to_string())
    # print("\nDone with measurements")