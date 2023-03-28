from rxtests import Sensitivity
from common import Logger, Level

sens_settings = Sensitivity.Settings(

    measure_with_CTUNE_w_SA = False,  # measurement with including CTUNE tuning with Spectrum Analyzer?
    measure_with_CTUNE_w_SG = True, # measurement with including CTUNE tuning with Signal Generator?
    
    freq_list_hz = [868e6, 915e6],
    wstk_com_port = "COM3",
    siggen_address = 'GPIB0::5::INSTR',
    specan_address = 'TCPIP::169.254.88.77::INSTR', # for CTUNE with SA case

    specan_span_hz = 200e3, # SA settings for CTUNE in CW mode
    specan_rbw_hz = 10e3,   # SA settings for CTUNE in CW mode

    cable_attenuation_dB = 7,

    siggen_power_start_dBm = -118,
    siggen_power_stop_dBm = -123,
    siggen_power_steps = 11,

    siggen_modulation_type = "FSK2",
    siggen_modulation_symbolrate_sps = 2400,
    siggen_modulation_deviation_Hz = 1200,

    siggen_logger_settings= Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
    
)

measurement = Sensitivity(settings=sens_settings,chip_name="EFR32FG23",board_name="BRD4204D")

df = measurement.measure()

#print(df.to_string())