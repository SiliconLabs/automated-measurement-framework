
"""
Automated Measurement Framework - DC-DC spur measurement example

This script is intended as an example for the Automated Measurement Framework. Information about the example can be found in the README file
in this folder.

"""

#################################################################################################################################################

try:
    from pywstk.pyRAIL import WSTK_RAILTest
except ModuleNotFoundError:
    # This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

from pywstk.pyRAIL import WSTK_RAILTest
from pydoc import visiblename
from pyspecan.pySpecAn import SpecAn, Anritsu_SignalAnalyzer
from pyspecan.measurements.generic_measurements import SpectrumSweep, MeasurementSuite
import numpy as np
from pypsu import pyPSU
from matplotlib import pyplot as plt
import xlsxwriter
from time import sleep
from datetime import datetime as dt
import pandas as pd
from os import remove,path
from dataclasses import dataclass, field
from common import Logger, Level
import atexit
from pyvisa import errors as visaerrors
import itertools
import warnings

#################################################################################################################################################

class TxDcDcSpurTest:
    """
    Sweeping and measuring most parameters of an EFR device transmitting
    a carrier wave signal. 

    Required instruments: 
    - SiLabs EFR with RAILTest configured
    - Spectrum Analyzer
    - Optional Lab Power Supply
    """

    @dataclass
    class Settings:
        """
        All configurable settings for this measurement.

        Sweepable variables can be configured by a list.

        :param list freq_list_hz: Custom list of frequencies

        :param str psu_address: VISA address of PSU, if serial is used, it is a COM port, check PyVISA documentation
        :param list psu_voltages_v: Custom list of voltages

        :param list power_levels: Custom ist of power values
        
        :param str specan_address: VISA address of Spectrum Analyzer,can check PyVISA documentation

        :param str dut_com_port: COM port of the RAILTest device
        """
        #Frequency range settings
        freq_list_hz: list|None = None

        #DUT settings
        dut_com_port: str = ""
        dut_logger_settings: Logger.Settings = Logger.Settings()

        #Power settings
        power_level_list: list = field(default_factory=lambda: [254, ])
        power_format:str = 'raw'

        #Supply settings
        psu_address: str|None = None
        psu_voltage_list_v: list = field(default_factory=lambda: [3.0, ])
        psu_logger_settings: Logger.Settings = Logger.Settings()
        
        #SA settings 
        specan_address: str = ""
        specan_logger_settings: Logger.Settings = Logger.Settings()

        dcdc_spur_meas_span_hz:int = 1e6
        dcdc_spur_meas_freq_offset_hz:int = 550e3

        dcdc_spur_search_peak_excursion_db: float = 10

        logger_settings: Logger.Settings = Logger.Settings()

    _screenshot_base_name = ""
    @property
    def screenshot_base_name(self):
        return self._screenshot_base_name

    @screenshot_base_name.setter
    def screenshot_base_name(self, new_screenshot_base_name:str):
        max_len = 32-len("_xxx_YYMMDDhhmmss")
        if len(new_screenshot_base_name) > max_len:
            new_screenshot_base_name = new_screenshot_base_name[:max_len]
            warnings.warn("Screenshot filename has been truncated!")
        self._screenshot_base_name=new_screenshot_base_name

    def _get_screenshot_setting(self, test_name:str) -> Anritsu_SignalAnalyzer.ScreenshotSettings:
        file_name = f'{self.screenshot_base_name}_{test_name}_{self.test_datetime.strftime("%Y%m%d%H%M%S")[2:]}'
        return Anritsu_SignalAnalyzer.ScreenshotSettings(append_timestamp=False, filename_base=file_name)

    tx_power_meas_sweep_settings = SpectrumSweep.Settings(
        mode="SINGLE",
        span_hz=int(1e6),
        rbw_hz=int(100e3),
        ref_level_dbm=20,
        trace_storage_mode="OFF",
    )

    dcdc_spur_meas_sweep_settings = SpectrumSweep.Settings(
        mode="SINGLE",
        span_hz=int(1e3),
        rbw_hz=int(3e3),
        vbw_hz=int(3e3),
        ref_level_dbm=-20,
        attenuation_db=30,
        trace_storage_mode="MAXHold",
        storage_count=20,
    )

    def __init__(self, settings:Settings, chip_name:str, board_name:str):
        """
        Initialize measurement class

        :param Settings settings: TXCWSweep.Settings dataclass containing all the configuration
        :param str chip_name : Name of IC being tested, only used in reporting
        :param str board_name: Name of board, containg the IC, only used in reporting
        """
        self.settings = settings
        self.chip_name = chip_name
        self.board_name = board_name

        self.test_datetime = dt.now()

        if self.settings.logger_settings.module_name is None:
            self.settings.logger_settings.module_name = __name__

        self.logger = Logger(self.settings.logger_settings)
        atexit.register(self.__del__)

        self.psu = None
        self.specan = None
        self.dut = None

        self.initialize_psu()
        self.initialize_specan()
        self.initialize_dut()

        self.results_dataframe = pd.DataFrame()

        self.dcdc_spur_meas_sweep_settings.span_hz = settings.dcdc_spur_meas_span_hz

    def initialize_psu(self):
        if self.settings.psu_address:
            self.psu = pyPSU.PSU(self.settings.psu_address,logger_settings = self.settings.psu_logger_settings)
            self.psu.selectOutput(1)
            self.psu.setVoltage(self.settings.psu_voltage_list_v[0])
            self.psu.toggleOutput(True)

    def initialize_specan(self):
        self.specan = SpecAn(resource=self.settings.specan_address,logger_settings=self.settings.specan_logger_settings)
        self.specan.reset()
        #self.specan.updateDisplay(on_off=True)

    def initialize_dut(self):
        self.dut = WSTK_RAILTest(self.settings.dut_com_port, reset=True,logger_settings=self.settings.dut_logger_settings)

    def initiate(self):
        psu_voltages_v = self.settings.psu_voltage_list_v if self.psu is not None else [None, ]
        for env_voltage in psu_voltages_v:
            if env_voltage is not None:
                self.psu.toggleOutput(True)
                self.psu.setVoltage(env_voltage)
                sleep(0.1)
            self.dut._driver.reset()
            self.dut._driver.flushIO()
            for power, freq_hz in itertools.product(self.settings.power_level_list, self.settings.freq_list_hz):
                voltage_str = f'v{str(round(env_voltage, 1)).replace(".", "p")}' if env_voltage is not None else ""
                power_str =f'p{power:.0f}' # TODO: Handle dBm values
                freq_str = f'f{str(round(freq_hz / 1e6, 1)).replace(".", "p")}'
                self.screenshot_base_name = voltage_str+power_str+freq_str

                # Start transmitting CW signal
                self.dut.transmit(mode="CW", frequency_Hz=freq_hz, power_dBm=power, power_format="RAW")

                # Measure current
                current_ma = self.psu.measCurrent() * 1000 if self.psu is not None else np.NaN

                # Measure TX Power
                sweep_settings = self.tx_power_meas_sweep_settings
                sweep_settings.frequency_hz = freq_hz
                SpectrumSweep.do_sweep(self.specan, sweep_settings)
                tx_peak = MeasurementSuite(self.specan, screenshot_settings=self._get_screenshot_setting("TXP")).measure_peak()
                tx_power_dbm=tx_peak.value

                # Measure DC-DC spurs

                sweep_settings = self.dcdc_spur_meas_sweep_settings
                sweep_settings.frequency_hz = tx_peak.position - self.settings.dcdc_spur_meas_freq_offset_hz
                SpectrumSweep.do_sweep(self.specan, sweep_settings)
                dcdc_spurs_lower = MeasurementSuite(self.specan, screenshot_settings=self._get_screenshot_setting("SPL")).measure_peak_list(resolution_db=10)
                max_spur_lower = max(dcdc_spurs_lower, key=lambda x: x.value)

                sweep_settings.frequency_hz = tx_peak.position + self.settings.dcdc_spur_meas_freq_offset_hz
                SpectrumSweep.do_sweep(self.specan, sweep_settings)
                dcdc_spurs_higher = MeasurementSuite(self.specan, screenshot_settings=self._get_screenshot_setting("SPH")).measure_peak_list(resolution_db=10)
                max_spur_higher = max(dcdc_spurs_higher, key=lambda x: x.value)

                results = {
                    "Env_Voltage_V": [env_voltage],
                    "Power_Setting": [power],
                    "Frequency_Hz": [freq_hz],
                    "TX_Power_dBm": [tx_power_dbm],
                    "TX_Current_mA": [current_ma],
                    "Lower_DC-DC_Spur_Power_dBm": [max_spur_lower.value],
                    "Higher_DC-DC_Spur_Power_dBm:": [max_spur_higher.value],
                    "Lower_DC-DC_Spur_Freq_Offset_Hz": [max_spur_lower.position-tx_peak.position],
                    "Higher_DC-DC_Spur_Freq_Offset_Hz:": [max_spur_higher.position-tx_peak.position]
                }
                record_df = pd.DataFrame.from_dict(results)
                self.results_dataframe = pd.concat([self.results_dataframe, record_df])

            self.psu.toggleOutput(False)
            return self.results_dataframe

    def stop(self):
        try:
            if hasattr(self, 'psu') and self.psu is not None:
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

    def measure(self)->pd.DataFrame:
        """
        Initiate the measurement.

        :return: The measured data
        :rtype: pandas.DataFrame
        """

        self.initiate()

        self.stop()

        self.logger.info("\nDone with measurements")
        self.results_dataframe.to_excel(f'{path.splitext(path.basename(__file__))[0]}_{self.test_datetime.strftime("%Y%m%d%H%M%S")[2:]}.xlsx', sheet_name='Sheet1')
        return self.results_dataframe

    def __del__(self):
        self.stop()


if __name__ == '__main__':
    test_settings = TxDcDcSpurTest.Settings(
        freq_list_hz=[426662500, ],

        dut_com_port="COM18",
        dut_logger_settings=Logger.Settings(logging_level=Level.INFO),

        power_level_list=[10, 120, 240, ],  # np.linspace(0,240,241,dtype=float),
        power_format= "RAW",

        psu_address="ASRL19::INSTR",
        psu_voltage_list_v=[2.5, ],
        psu_logger_settings=Logger.Settings(logging_level=Level.INFO),

        specan_address='TCPIP::169.254.88.77::INSTR',
        specan_logger_settings=Logger.Settings(logging_level=Level.INFO),

        dcdc_spur_meas_span_hz = int(1e6),
        dcdc_spur_meas_freq_offset_hz=int(550e3),

        dcdc_spur_search_peak_excursion_db=10
    )

    measurement = TxDcDcSpurTest(settings=test_settings, chip_name="EFR32FG23", board_name="BRD4265B")

    res = measurement.measure()
    print(res)