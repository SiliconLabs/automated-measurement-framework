from rxtests import Sensitivity
from common import Logger, Level

sens_settings = Sensitivity.Settings(
    
    freq_list_hz = [868e6, 876e6, 902e6, 915e6, 928e6],
    wstk_com_port = "COM3",
    siggen_address = 'GPIB0::5::INSTR',
    cable_attenuation_dB = 1,

    siggen_power_start_dBm = -107,
    siggen_power_stop_dBm = -112,
    siggen_power_steps = 11,

    siggen_modulation_type = "FSK2",
    siggen_modulation_symbolrate_sps = 100e3,
    siggen_modulation_deviation_Hz = 50e3,

    siggen_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
    
)

measurement = Sensitivity(settings=sens_settings,chip_name="EFR32FG23",board_name="BRD4204D")

df = measurement.measure()

print(df.to_string())