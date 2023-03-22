import pyspecan.pySpecAn
from pywstk import pyRAIL
from pyspecan.pySpecAn import SpecAn
from time import sleep
from pyspecan.measurements.telec_t245_measurements import TelecT245MeasurementSuite
from dataclasses import dataclass
from typing import Callable

WSTK_COM_PORT = "COM5"
SPEC_AN_PORT = "TCPIP::169.254.88.77::INSTR"
CTUNE_OVERRIDE = 87

@dataclass
class TestConfigItem:
    name: str
    name_4char: str
    freq_list_hz: list
    pa_config: pyRAIL.PA_Config
    power_dbm: float
    tx_length_bytes: int
    phy_init_func: Callable[[object], None]
    tx_delay_ms: int

    carrier_bw_n: float
    unit_channel_bw_hz: float


config_list = [
    TestConfigItem(name='FSK 2b',
                   name_4char='FS2b',
                   freq_list_hz=[925.3e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600, rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=0),
                   tx_delay_ms=20,
                   carrier_bw_n=2,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=1.0',
                   name_4char='F510',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=1),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=1.1',
                   name_4char='F511',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=2),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=1.2',
                   name_4char='F512',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=3),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=1.3',
                   name_4char='F513',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=4),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=1.4',
                   name_4char='F514',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=5),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=1.5',
                   name_4char='F515',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=6),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='FSK 5 BT=2.0',
                   name_4char='FS20',
                   freq_list_hz=[925.0e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_SUBGIG_POWERSETTING_TABLE", milliVolts=3600,
                                              rampTime_us=10),
                   power_dbm=11.9,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_fsk_config(self, radio_config_id=7),
                   tx_delay_ms=7,
                   carrier_bw_n=3,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='OFDM Option2 MCS6',
                   name_4char='O2M6',
                   freq_list_hz=[925.1e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_OFDM_PA_POWERSETTING_TABLE", milliVolts=3600, rampTime_us=10),
                   power_dbm=14.3,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_ofdm_config(self,radio_config_id=8, mcs=6),
                   tx_delay_ms=3,
                   carrier_bw_n=4,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='OFDM Option3 MCS6',
                   name_4char='O3M6',
                   freq_list_hz=[925.3e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_OFDM_PA_POWERSETTING_TABLE", milliVolts=3600, rampTime_us=10),
                   power_dbm=13.8,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_ofdm_config(self,radio_config_id=9, mcs=6),
                   tx_delay_ms=5,
                   carrier_bw_n=2,
                   unit_channel_bw_hz=200e3,
                   ),
    TestConfigItem(name='OFDM Option4 MCS6',
                   name_4char='O4M6',
                   freq_list_hz=[925.2e6, ],
                   pa_config=pyRAIL.PA_Config(paMode="RAIL_TX_POWER_MODE_OFDM_PA_POWERSETTING_TABLE", milliVolts=3600, rampTime_us=10),
                   power_dbm=13.7,
                   tx_length_bytes=250,
                   phy_init_func=lambda self: pyRAIL.WSTK_RAILTest.set_wisun_ofdm_config(self,radio_config_id=10, mcs=6),
                   tx_delay_ms=8,
                   carrier_bw_n=1,
                   unit_channel_bw_hz=200e3,
                   ),
               ]


def run_test(configs):
    dut = pyRAIL.WSTK_RAILTest(COMport=WSTK_COM_PORT, reset=True)
    sa = SpecAn(resource=SPEC_AN_PORT, auto_detect=True)

    if CTUNE_OVERRIDE is not None:
        dut._driver.setCtune(CTUNE_OVERRIDE)

    for config in configs:
        for freq_hz in config.freq_list_hz:
            # Misc
            freq_str = str(round(freq_hz / 1e6, 1)).replace(".", "p")
            filename_base = f'{config.name_4char}p{config.power_dbm*10:.0f}f{freq_str}'
            print(f"\r\nTesting {config.name} f={freq_hz / 1e6} Hz...")

            # Global Measurement Init
            measurement_suite = TelecT245MeasurementSuite(sa=sa, frequency_hz=freq_hz, carrier_bw_n=config.carrier_bw_n, unit_channel_bw_hz=config.unit_channel_bw_hz)
            measurement_suite.screenshot_base_name=filename_base

            # Global DUT Init
            dut.setSingleTransmitData(data=bytes([]), packet_length_override=4)
            config.phy_init_func(dut)
            transmit_settings = {'pa_config': config.pa_config, 'frequency_Hz': freq_hz, 'power_dBm': config.power_dbm,
                                 'power_format': "DBM", 'tx_delay_ms': config.tx_delay_ms}

            # Transmit CW Tone
            transmit_settings["mode"] = "CW"
            dut.transmit(**transmit_settings)

            # Wait for stable output
            sleep(5)

            # Measure frequency tolerance
            frequency_tolerance_ppm = measurement_suite.measure_frequency_tolerance()
            print(f"Frequency tolerance: {frequency_tolerance_ppm[0]} ppm")

            # Transmit continuous stream
            transmit_settings["mode"] = "PN9"
            dut.transmit(**transmit_settings)

            # Measure antenna power (average burst power)
            antenna_power_raw = measurement_suite.measure_antenna_power()
            print(f"Antenna Power: {antenna_power_raw} dBm")

            # Measure OBW
            obw_hz = measurement_suite.measure_obw()
            print(f"Occupied bandwidth: {obw_hz / 1000} KHz")

            # Measure ACP
            acp_raw = measurement_suite.measure_acp()
            print(f"ACP raw: {acp_raw}")

            # Measure OOB emissions
            spurs_raw = measurement_suite.measure_tx_oob_emissions(measure_rms=False)
            print(f"OOB TX Emissions (peak): {[res['max_marker'].value for res in spurs_raw]}")
            spurs_raw = measurement_suite.measure_tx_oob_emissions(measure_rms=True)
            print(f"OOB TX Emissions (RMS): {[res['max_marker'].value for res in spurs_raw]}")

            # Measure in-band spurious emissions
            iib_spurs_max, _ = measurement_suite.measure_tx_in_band_emissions_telec()
            print(f"In-band TX spurious emission (max): {iib_spurs_max}")

            # Measure RX secondary "radiated" emissions
            dut.startReceive(on_off=True, frequency_Hz=freq_hz)
            rx_secondary_spurs = measurement_suite.measure_rx_secondary_emissions(measure_rms=False)
            print(f"RX Secondary emissions: {rx_secondary_spurs}")

            rx_secondary_spurs = measurement_suite.measure_rx_secondary_emissions(measure_rms=True)
            print(f"RX Secondary emissions: {rx_secondary_spurs}")

            dut.stop()


if __name__ == '__main__':
    run_test(config_list[0:2]+config_list[8:])
