import warnings
from dataclasses import dataclass
from ..pySpecAn import GenericSpecAn,Anritsu_SignalAnalyzer,  Marker, PowerMarker, TriggerSettings
import numpy
from time import sleep


class Generic:
    @dataclass
    class Settings:
        ref_level_dbm: float = 30
        rbw_hz: int | None = None
        vbw_hz: int | None = None
        mode: str = 'single'
        storage_count: int = 10
        trace_storage_mode:str='OFF'
        detector:str = 'NORM'
        attenuation_db:int|None = None
        y_div_db:int = 10
        ref_offset_db:int = 0
        trigger_settings: TriggerSettings = None
        sweep_time_s:float = None
        sweep_points:int = 10001

    @classmethod
    def apply_setting(cls, sa: GenericSpecAn, settings: Settings):
        if not isinstance(settings, cls.Settings):
            raise ValueError('settings must be instance of:', cls.Settings)
        if not settings.attenuation_db:
            sa.setAttenuationAuto()
        else:
            sa.setAttenuation(settings.attenuation_db)
        sa.setSweepPoints(settings.sweep_points)
        sa.setRefLevel(settings.ref_level_dbm)
        sa.setDetector(settings.detector)
        sa.setRBW(settings.rbw_hz)
        if settings.detector.upper() != "RMS":
            sa.setVBW(settings.vbw_hz)
        sa.setMode(settings.mode)
        if settings.storage_count == 1:
            settings.trace_storage_mode = "OFF"
            warnings.warn('Trace storage mode was overriden to "OFF"')
        sa.setTraceStorageMode(settings.trace_storage_mode)
        sa.setStorageCount(settings.storage_count)
        sa.setDetector(settings.detector)
        if not settings.sweep_time_s:
            sa.setAutoSweepTime()
        else:
            sa.setSweepTime(settings.sweep_time_s)
        sa.setDivision(settings.y_div_db)
        sa.setRefOffset(settings.ref_offset_db)
        sa.configTrigger(settings.trigger_settings)


class SpectrumSweep:
    @dataclass
    class Settings(Generic.Settings):
        frequency_hz: int | None = None
        span_hz: int | None = None
        f_start_hz: int | None = None
        f_stop_hz: int | None = None
        hold_time_s: float = None

    @classmethod
    def apply_settings(cls, sa: GenericSpecAn, settings: Settings):
        if not isinstance(settings, cls.Settings):
            raise ValueError('settings must be instance of:', cls.Settings)

        f_center = settings.frequency_hz and settings.span_hz
        f_range = settings.f_start_hz and settings.f_stop_hz
        if f_center and not (settings.f_start_hz or settings.f_stop_hz):
            sa.setFrequency(settings.frequency_hz)
            sa.setSpan(settings.span_hz)
        elif f_range and not (settings.frequency_hz or settings.span_hz):
            sa.setFullSpan()  # In case we were in zero-span mode
            sa.setFrequencyStart(settings.f_start_hz)
            sa.setFrequencyStop(settings.f_stop_hz)
        else:
            raise ValueError('Either frequency_Hz & span_Hz OR f_start_Hz & f_stop_Hz needs to be defined')
        Generic.apply_setting(sa, settings)

    @classmethod
    def do_sweep(cls, sa: GenericSpecAn, settings: Settings=None, hold_time_s:float=None):
        if settings:
            cls.apply_settings(sa,settings)

        if settings.mode.upper() == "CONTINUOUS" and not hold_time_s:
            raise ValueError("hold_time_s must be defined in CONTINUOUS mode")

        sa.initiate()
        if settings.mode.upper() == "CONTINUOUS":
            sleep(hold_time_s)
        elif settings.mode.upper() == "SINGLE":
            sa.waitUntilIdle()
        sa.stopSweep()


class ZeroSpanSweep:
    @dataclass
    class Settings(Generic.Settings):
        frequency_hz:int|None = None

    @classmethod
    def apply_settings(cls, sa: GenericSpecAn, settings: Settings):
        if not isinstance(settings, cls.Settings):
            raise ValueError('settings must be instance of:', cls.Settings)
        sa.setZeroSpanMode()
        sa.setFrequency(settings.frequency_hz)
        Generic.apply_setting(sa, settings)

    @classmethod
    def do_sweep(cls, sa: GenericSpecAn, settings: Settings=None, hold_time_s:float=None):
        if settings:
            cls.apply_settings(sa,settings)

        if settings.mode.upper() == "CONTINUOUS" and not hold_time_s:
            raise ValueError("hold_time_s must be defined in CONTINUOUS mode")

        sa.initiate()
        if settings.mode.upper() == "CONTINUOUS":
            sleep(hold_time_s)
        elif settings.mode.upper() == "SINGLE":
            sa.waitUntilIdle()
        sa.stopSweep()

@dataclass
class MeasurementSuite:
    sa:Anritsu_SignalAnalyzer
    screenshot_settings:Anritsu_SignalAnalyzer.ScreenshotSettings|None = None

    def clear_measurements(self):
        self.sa.disableMeasurements()
        self.sa.allMarkersOff()
        self.sa.deleteAllLimitLines()
        self.sa.disableAllLimitStates()
        self.sa.setMarkerTableDisplay(False)

    def clear_before_execution(measurement_function):
        def inner(self, *args, **kwargs):
            MeasurementSuite.clear_measurements(self)
            res = measurement_function(self, *args, **kwargs)
            return res
        return inner

    def screenshot_after_execution(measurement_function):
        def inner(self, *args, **kwargs):
            res = measurement_function(self, *args, **kwargs)
            if self.screenshot_settings:
                self.sa.save_screenshot(self.screenshot_settings)
            return res
        return inner

    @clear_before_execution
    @screenshot_after_execution
    def measure_peak(self) -> Marker:
        self.sa.setMarkerZoneWidth(value=0)
        max_marker = self.sa.getMaxMarker()
        return max_marker

    @clear_before_execution
    @screenshot_after_execution
    def measure_peak_list(self, threshold_dbm:float|None=None, resolution_db:float|None=None) -> list[Marker]:
        self.sa.setMarkerZoneWidth(value=0)
        max_marker = self.sa.getPeakList(threshold_dbm=threshold_dbm, resolution_db=resolution_db)
        return max_marker

    @clear_before_execution
    @screenshot_after_execution
    def measure_integrated_power_peaks(self, bw_hz:float, limit_dbm:float|None=None) -> list[PowerMarker]:
        return self.sa.getPowerMarkerPeakList(bw_hz=bw_hz,limit_dbm=limit_dbm)

    @clear_before_execution
    @screenshot_after_execution
    def measure_obw(self, method:str="NPERcent", threshold:float=99) -> float:
        self.sa.configureOBWMeasurement(enabled=True, method=method, threshold=threshold)
        obw_hz = self.sa.fetchOBW()
        return obw_hz

    @clear_before_execution
    @screenshot_after_execution
    def measure_acp(self, carrier_bw_hz:int, acp_bw_hz:int, offset_hz:int|list, max_channel_diff=1, ref_power_method:str="BSIDes") -> float:
        self.sa.configureACPMeasurement(carrier_bw_hz=carrier_bw_hz, adj_bw_hz=acp_bw_hz,
                                   offset_hz=offset_hz, max_channel_diff=max_channel_diff, ref_power_method=ref_power_method)
        acp_raw = self.sa.fetchACP()
        return acp_raw

    @clear_before_execution
    @screenshot_after_execution
    def measure_burst_average_power(self, start_time_s=0, stop_time_s=None):
        self.sa.configureBurstAveragePowerMeasurement(start_time_s=start_time_s, stop_time_s=stop_time_s)
        burst_average_power_dbm = self.sa.fetchBurstAveragePower()
        return burst_average_power_dbm

    @clear_before_execution
    @screenshot_after_execution
    def measure_channel_power(self, channel_center_freq_hz, channel_width_hz, filter:str="RECT"):
        self.sa.configureChannelPowerMeasurement(channel_center_freq_hz=channel_center_freq_hz, channel_width_hz=channel_width_hz, filter=filter)
        channel_power_raw = self.sa.fetchChannelPower()  # total power in channel, spectral density
        return channel_power_raw
