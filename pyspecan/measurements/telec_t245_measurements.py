import pyspecan.pySpecAn
from .generic_measurements import SpectrumSweep, ZeroSpanSweep, MeasurementSuite
from dataclasses import dataclass
from ..pySpecAn import Anritsu_SignalAnalyzer, TriggerSettings, LimitLinePoint
from datetime import datetime
import warnings
import numpy

@dataclass
class TelecT245MeasurementSuite:
    sa:Anritsu_SignalAnalyzer
    frequency_hz: int
    carrier_bw_n: int
    unit_channel_bw_hz: int = 200e3
    attenuation_db: int = 31  # 13 dBm average power + 8 dB PAPR -> -10 dBm peak at mixer

    _average_power_dbm = None
    _screenshot_base_name=""

    @property
    def iib_exclude_region_low_hz(self):
        return self.frequency_hz - self.unit_channel_bw_hz * (1 + self.carrier_bw_n / 2)

    @property
    def iib_exclude_region_high_hz(self):
        return self.frequency_hz + self.unit_channel_bw_hz * (1 + self.carrier_bw_n / 2)

    @property
    def screenshot_base_name(self):
        return self._screenshot_base_name

    @screenshot_base_name.setter
    def screenshot_base_name(self, new_screenshot_base_name:str):
        max_len = 32-len("_xxxx_YYMMDDhhmmss")
        if len(new_screenshot_base_name) > max_len:
            new_screenshot_base_name = new_screenshot_base_name[:max_len]
            warnings.warn("Screenshot filename has been truncated!")
        self._screenshot_base_name=new_screenshot_base_name

    def _get_screenshot_setting(self, test_name:str) -> Anritsu_SignalAnalyzer.ScreenshotSettings:
        file_name = f'{self.screenshot_base_name}_{test_name}_{datetime.now().strftime("%Y%m%d%H%M%S")[2:]}'
        return Anritsu_SignalAnalyzer.ScreenshotSettings(append_timestamp=False, filename_base=file_name)

    def measure_frequency_tolerance(self, sweep_overrides: dict={}):
        expected_obw_hz = self.carrier_bw_n * self.unit_channel_bw_hz
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            frequency_hz=int(self.frequency_hz),
            span_hz=int(expected_obw_hz*3),
            rbw_hz=int(expected_obw_hz / 100),
            ref_level_dbm=20,
            attenuation_db=self.attenuation_db,
            trace_storage_mode="MAXHold",
            storage_count=10,
            detector="POSitive",
            y_div_db=10,
            sweep_points=10001
        )
        sweep_settings.__dict__.update(sweep_overrides)

        SpectrumSweep.do_sweep(self.sa, sweep_settings)

        max_marker = MeasurementSuite(self.sa, self._get_screenshot_setting("FTOL")).measure_peak()
        freq_error_ppm = (max_marker.position-self.frequency_hz)/self.frequency_hz*1e6
        return freq_error_ppm, max_marker

    def measure_obw(self, sweep_overrides: dict={}):
        expected_obw_hz = self.carrier_bw_n * self.unit_channel_bw_hz
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            frequency_hz=int(self.frequency_hz),
            span_hz=int(expected_obw_hz*3),
            rbw_hz=int(expected_obw_hz / 100),
            ref_level_dbm=20,
            attenuation_db=self.attenuation_db,
            trace_storage_mode="MAXHold",
            storage_count=10,
            detector="POSitive",
            y_div_db=10,
            sweep_points=10001
        )
        sweep_settings.__dict__.update(sweep_overrides)
        SpectrumSweep.do_sweep(self.sa, sweep_settings)
        obw_hz = MeasurementSuite(self.sa, self._get_screenshot_setting("OBW")).measure_obw(method="NPERcent", threshold=99)

        return obw_hz

    def measure_acp(self, sweep_overrides: dict={}):
        carrier_bw_hz = self.carrier_bw_n * self.unit_channel_bw_hz
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            frequency_hz=int(self.frequency_hz),
            span_hz=int((carrier_bw_hz+self.unit_channel_bw_hz*4)),
            rbw_hz=int(1e3),
            vbw_hz=int(3e3),
            ref_level_dbm=20,
            attenuation_db=self.attenuation_db,
            trace_storage_mode="OFF",
            detector="POSitive",
            y_div_db=10,
            sweep_points=10001
        )
        sweep_settings.__dict__.update(sweep_overrides)
        SpectrumSweep.do_sweep(self.sa, sweep_settings)

        acp_raw = MeasurementSuite(self.sa, self._get_screenshot_setting("ACP")).measure_acp(carrier_bw_hz=int(carrier_bw_hz),
                                                                                 acp_bw_hz=int(self.unit_channel_bw_hz-sweep_settings.rbw_hz),
                                                                                 offset_hz=int((carrier_bw_hz+self.unit_channel_bw_hz)/2))
        return acp_raw

    def measure_antenna_power(self, avg_time_s:float = 100e-3, sweep_overrides: dict={}):

        sweep_settings = ZeroSpanSweep.Settings(
            mode="SINGLE",
            frequency_hz=int(self.frequency_hz),
            rbw_hz=int(1e6),
            vbw_hz=int(3e6),
            ref_level_dbm=20,
            attenuation_db=self.attenuation_db,
            trace_storage_mode="OFF",
            detector="SAMPle",
            y_div_db=10,
            sweep_time_s= avg_time_s,
            sweep_points=10001
        )
        sweep_settings.__dict__.update(sweep_overrides)
        ZeroSpanSweep.do_sweep(self.sa, sweep_settings)
        ant_power_dbm = MeasurementSuite(self.sa, self._get_screenshot_setting("APOW")).measure_burst_average_power(start_time_s=0, stop_time_s=avg_time_s)
        self._average_power_dbm=ant_power_dbm  # Save average power for in-band TX spurious emission relxation
        return ant_power_dbm

    def measure_tx_oob_emissions(self, measure_rms=True, sweep_overrides: dict={}):
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            ref_level_dbm=0,
            attenuation_db=self.attenuation_db,
            trace_storage_mode="MAXHold" if measure_rms else "OFF",
            storage_count=10,
            sweep_time_s=0.5 if measure_rms else None,
            sweep_points=1001,
            detector="RMS" if measure_rms else "POSitive",
            y_div_db=10
        )

        @dataclass
        class MeasItem:
            f_start_mhz:float
            f_stop_mhz:float
            rbw_khz:float
            limit_dbm: float

        # Define ranges outside neighborhood
        meas_list = [MeasItem(  30,  710,  100, -36),
                     MeasItem( 710,  900, 1000, -55),
                     MeasItem( 900,  915,  100, -55),
                     MeasItem( 930, 1000,  100, -55),
                     MeasItem(1000, 1215, 1000, -45),
                     MeasItem(1215, 5000, 1000, -30)]
        results = []
        for meas_id, meas_item in enumerate(meas_list):
            sweep_settings.f_start_hz = meas_item.f_start_mhz * 1e6
            sweep_settings.f_stop_hz = meas_item.f_stop_mhz * 1e6
            sweep_settings.rbw_hz = meas_item.rbw_khz * 1e3
            sweep_settings.__dict__.update(sweep_overrides)
            SpectrumSweep.do_sweep(self.sa, sweep_settings)

            max_marker = MeasurementSuite(self.sa, screenshot_settings=None).measure_peak()  # Suppress screenshot
            self.sa.setFullSpanLimitLine(level_dbm=meas_item.limit_dbm)
            self.sa.save_screenshot(settings=self._get_screenshot_setting(f'OOB{meas_id}')) # Save screenshot with limit lines
            results.append({'f_start_hz': sweep_settings.f_start_hz,
                            'f_stop_hz': sweep_settings.f_stop_hz,
                            'max_marker': max_marker})
        return results

    def measure_rx_secondary_emissions(self, measure_rms=True, sweep_overrides: dict={}):
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            ref_level_dbm=0,
            attenuation_db=self.attenuation_db,
            trace_storage_mode="MAXHold" if measure_rms else "OFF",
            storage_count=10,
            sweep_time_s=0.5 if measure_rms else None,
            sweep_points=1001,
            detector="RMS" if measure_rms else "POSitive",
            y_div_db=10
        )

        @dataclass
        class MeasItem:
            f_start_mhz:float
            f_stop_mhz:float
            rbw_khz:float
            limit_dbm: float

        # Define ranges outside neighborhood
        meas_list = [MeasItem(  30,  710,  100, -54),
                     MeasItem( 710,  900, 1000, -55),
                     MeasItem( 900,  915,  100, -55),
                     MeasItem( 915,  930,  100, -54),
                     MeasItem( 930, 1000,  100, -55),
                     MeasItem(1000, 5000, 1000, -47),
                     ]
        results = []
        for meas_id, meas_item in enumerate(meas_list):
            sweep_settings.f_start_hz = meas_item.f_start_mhz * 1e6
            sweep_settings.f_stop_hz = meas_item.f_stop_mhz * 1e6
            sweep_settings.rbw_hz = meas_item.rbw_khz * 1e3
            sweep_settings.__dict__.update(sweep_overrides)
            SpectrumSweep.do_sweep(self.sa, sweep_settings)

            max_marker = MeasurementSuite(self.sa, screenshot_settings=None).measure_peak()  # Suppress screenshot
            self.sa.setFullSpanLimitLine(level_dbm=meas_item.limit_dbm)
            self.sa.save_screenshot(settings=self._get_screenshot_setting(f'RXS{meas_id}')) # Save screenshot with limit lines
            results.append({'f_start_hz': sweep_settings.f_start_hz,
                            'f_stop_hz': sweep_settings.f_stop_hz,
                            'max_marker': max_marker})
        return results

    def _get_ib_spur_zoom_freqs_and_markers_integrated(self, trace_data_raw: list, sweep_settings: SpectrumSweep.Settings):
        trace_data = numpy.array(trace_data_raw)
        f_step = (sweep_settings.f_stop_hz - sweep_settings.f_start_hz) / (sweep_settings.sweep_points - 1)
        filter_bw_n = 100e3 // f_step + 1

    def _get_ib_spur_zoom_freqs_and_markers_peak(self, trace_data_raw:list, threshold_dbm:float, sweep_settings:SpectrumSweep.Settings):
        trace_data = numpy.array(trace_data_raw)

        f_step = (sweep_settings.f_stop_hz - sweep_settings.f_start_hz) / (sweep_settings.sweep_points - 1)
        sorted_ids = numpy.argsort(-trace_data)

        markers_hz = []
        zoom_freqs_hz = numpy.array([])

        for pos, level in zip(sorted_ids, trace_data[sorted_ids]):
            f = sweep_settings.f_start_hz + pos * f_step
            if f < 915e6 or f > 930e6 or self.iib_exclude_region_low_hz < f < self.iib_exclude_region_high_hz:
                # Not in in-band spurious emission region
                continue
            if zoom_freqs_hz.size > 0 and min(abs(zoom_freqs_hz-f)) < 100e3/2:
                # There is already a zoom frequency nearby
                continue
            if level < threshold_dbm:
                # Pass if level is below limit but add markers if no markers were stored yet for this side (i.e. store highest value)
                if len(markers_hz)==0 or f < self.iib_exclude_region_low_hz < min(markers_hz) or max(markers_hz) < self.iib_exclude_region_high_hz < f:
                    markers_hz.append(f)
                continue
            if self.iib_exclude_region_low_hz - 50e3 < f < self.iib_exclude_region_low_hz :
                zoom_freq = self.iib_exclude_region_low_hz - 50e3
            elif self.iib_exclude_region_high_hz < f < self.iib_exclude_region_high_hz + 50e3:
                zoom_freq = self.iib_exclude_region_high_hz + 50e3
            else:
                zoom_freq = f
            markers_hz.append(f)
            zoom_freqs_hz = numpy.append(zoom_freqs_hz, zoom_freq)
        return list(zoom_freqs_hz), markers_hz

    def measure_tx_in_band_emissions_telec(self, sweep_overrides: dict={}):
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            ref_level_dbm=20,
            rbw_hz=int(3e3),
            vbw_hz=int(3e3),
            attenuation_db=self.attenuation_db,
            trace_storage_mode="OFF",
            detector="POSitive",
            y_div_db=10,
            sweep_points=2001,
            sweep_time_s=10
        )

        sweep_settings.__dict__.update(sweep_overrides)

        screenshot_id = 0
        zoomed_power_levels = []
        carrier_peak_total_power_dbm = None
        relaxation_db = None

        ## Measure peak spurious levels without any compensation first (limit is -36dBm/100kHz -> -51.2dBm/3kHz)
        limit_dbm_3khz = -51.2  #dBm/3kHz
        sweep_settings.f_start_hz = 915e6
        sweep_settings.f_stop_hz = 930e6
        SpectrumSweep.do_sweep(self.sa, sweep_settings)

        # Get markers for screenshot and frequencies for zoomed measurements
        trace_data_raw = self.sa.getTraceData()
        zoom_freqs_hz, markers_hz = self._get_ib_spur_zoom_freqs_and_markers_peak(trace_data_raw=trace_data_raw,sweep_settings=sweep_settings,threshold_dbm=limit_dbm_3khz)
        # Always measure carrier channel and adjacent regions
        zoom_freqs_hz = set([self.frequency_hz,
                         self.iib_exclude_region_low_hz-50e3,
                         self.iib_exclude_region_high_hz + 50e3]+ zoom_freqs_hz)

        MeasurementSuite(self.sa).clear_measurements()
        self.sa.setLimitLine([LimitLinePoint(frequency_hz=int(915e6-1), level_dbm=limit_dbm_3khz, connected=False),
                              LimitLinePoint(frequency_hz=int(self.iib_exclude_region_low_hz), level_dbm=limit_dbm_3khz, connected=True),
                              LimitLinePoint(frequency_hz=int(self.iib_exclude_region_high_hz), level_dbm=limit_dbm_3khz, connected=False),
                              LimitLinePoint(frequency_hz=int(930e6+1), level_dbm=limit_dbm_3khz, connected=True)
                              ], display_state=False)
        for marker_id, freq in enumerate(markers_hz,start=1):
            self.sa.addMarker(position=freq,marker_id=marker_id)
        self.sa.setMarkerTableDisplay(True)
        self.sa.setMarkerZoneWidth(value=0)
        self.sa.save_screenshot(settings=self._get_screenshot_setting(f'IBT{screenshot_id}')) # Save screenshot with limit lines
        screenshot_id += 1

        markers = self.sa.getAllMarkers()

        # Measure with 100 KHz span from now on with center frequency specified
        sweep_settings.f_start_hz = sweep_settings.f_stop_hz = None
        sweep_settings.sweep_time_s = 5
        sweep_settings.sweep_points = 10001

        for f in zoom_freqs_hz:
            sweep_settings.frequency_hz = f
            sweep_settings.span_hz = self.unit_channel_bw_hz * self.carrier_bw_n if f == self.frequency_hz else 100e3

            SpectrumSweep.do_sweep(self.sa, sweep_settings)
            channel_power_dbm, _ = MeasurementSuite(self.sa, screenshot_settings=self._get_screenshot_setting(
                f'IBT{screenshot_id}')).measure_channel_power(channel_center_freq_hz=f, channel_width_hz=sweep_settings.span_hz)
            screenshot_id += 1

            if f == self.frequency_hz:
                carrier_peak_total_power_dbm = channel_power_dbm

                if self._average_power_dbm is not None:
                    relaxation_db = self._average_power_dbm - channel_power_dbm
            else:
                zoomed_power_levels.append({'freq_hz': f, 'power_dbm': channel_power_dbm})

        raw_results = {"markers": markers,
                       "zoomed_power_levels": zoomed_power_levels,
                       "carrier_peak_total_power_dbm": carrier_peak_total_power_dbm,
                       "relaxation": relaxation_db}

        max_spur_level_dbm = max([p["power_dbm"] for p in zoomed_power_levels])+relaxation_db if relaxation_db is not None else None

        return max_spur_level_dbm, raw_results

    def measure_tx_in_band_emissions_rms(self, sweep_overrides: dict={}):
        sweep_settings = SpectrumSweep.Settings(
            mode="SINGLE",
            ref_level_dbm=20,
            rbw_hz=int(3e3),
            attenuation_db=self.attenuation_db,
            trace_storage_mode="OFF",
            detector="RMS",
            y_div_db=10,
            sweep_points=2001,
            sweep_time_s=10
        )
        sweep_settings.__dict__.update(sweep_overrides)
        screenshot_id = 0
        zoom_freqs_hz = []
        zoomed_power_levels = []
        markers = []
        zoom_threshold_dbm = -36-3  # dBm/100kHz

        for f_start_hz, f_stop_hz in [[915e6, self.iib_exclude_region_low_hz], [self.iib_exclude_region_high_hz, 930e6]]:
            sweep_settings.f_start_hz = f_start_hz
            sweep_settings.f_stop_hz = f_stop_hz
            SpectrumSweep.do_sweep(self.sa, sweep_settings)
            power_peaks = MeasurementSuite(self.sa, screenshot_settings=self._get_screenshot_setting(
                f'IBR{screenshot_id}')).measure_integrated_power_peaks(bw_hz=100e3, limit_dbm=zoom_threshold_dbm)
            screenshot_id += 1

            markers += power_peaks
            zoom_freqs_hz += [m.position for m in power_peaks]

        zoom_freqs_hz = set([self.iib_exclude_region_low_hz-50e3, self.iib_exclude_region_high_hz + 50e3]+ zoom_freqs_hz)

        # Measure with 100 KHz span from now on with center frequency specified
        sweep_settings.f_start_hz = sweep_settings.f_stop_hz = None
        sweep_settings.sweep_time_s = 5
        sweep_settings.sweep_points = 10001
        sweep_settings.span_hz = 100e3

        for f in zoom_freqs_hz:
            sweep_settings.frequency_hz = f

            SpectrumSweep.do_sweep(self.sa, sweep_settings)
            channel_power_dbm, _ = MeasurementSuite(self.sa, screenshot_settings=self._get_screenshot_setting(
                f'IBR{screenshot_id}')).measure_channel_power(channel_center_freq_hz=f, channel_width_hz=sweep_settings.span_hz)
            screenshot_id += 1

            zoomed_power_levels.append({'freq_hz': f, 'power_dbm': channel_power_dbm})

        raw_results = {"markers": markers, "zoomed_power_levels": zoomed_power_levels}

        max_spur_level_dbm = max([p["power_dbm"] for p in zoomed_power_levels])

        return max_spur_level_dbm, raw_results