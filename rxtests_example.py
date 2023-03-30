from rxtests import Sensitivity, Blocking
from common import Logger, Level

# Select the RX test options here:
Measure_Sensitivity_Only = False            # Measurement Option: Sensitivity only with possible CTUNE tuning
Measure_Sensitivity_And_Blocking = True     # Measurement Option: Sensitivity and Blocking with possible CTUNE tuning

# Settings for Sensitivity-only tests
sens_settings = Sensitivity.Settings(

    measure_with_CTUNE_w_SA = False,    # measurement with including CTUNE tuning with Spectrum Analyzer?
    measure_with_CTUNE_w_SG = False,    # measurement with including CTUNE tuning with Signal Generator?
    
    freq_list_hz = [876e6, 902e6],                  # test frequencies
    wstk_com_port = "COM3",
    siggen_address = 'GPIB0::5::INSTR',             # SigGen address
    specan_address = 'TCPIP::169.254.88.77::INSTR', # Spectrum Analyzer address, used for CTUNE with SA case

    specan_span_hz = 200e3, # SA settings for CTUNE in CW mode
    specan_rbw_hz = 10e3,   # SA settings for CTUNE in CW mode

    cable_attenuation_dB = 7,   # desired signal path cable loss

    siggen_power_start_dBm = -100,  # start SigGen power
    siggen_power_stop_dBm = -110,   # stop SigGen power
    siggen_power_steps = 11,        # power steps of SigGen during sensitivity test
    siggen_modulation_type = "FSK2",            # modulation format
    siggen_modulation_symbolrate_sps = 100e3,   # symbol rate
    siggen_modulation_deviation_Hz = 50e3,      # frequency deviation

    siggen_logger_settings= Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
    
)

# Settings for Sensitivity and Blocking tests
blocking_settings = Blocking.Settings(

    measure_with_CTUNE_w_SA = False,    # DO NOT CHANGE, during blocking test this must be 'False'
    measure_with_CTUNE_w_SG = True,     # include CTUNE tuning before sensitivity and blocking tests?

    freq_list_hz = [876e6, 902e6],                  # test frequencies
    wstk_com_port = "COM3",
    siggen_address = 'GPIB0::5::INSTR',             # SigGen address
    specan_address = 'TCPIP::169.254.88.77::INSTR', # Spectrum Analyzer address, its Generator function used

    cable_attenuation_dB = 7,                   # desired signal path cable loss

    siggen_power_start_dBm = -114,              # start SigGen desired signal path power
    siggen_power_stop_dBm = -124,               # stop SigGen desired signal path power
    siggen_power_steps = 11,                    # power steps of SigGen during sensitivity test
    siggen_modulation_type = "FSK2",            # modulation format
    siggen_modulation_symbolrate_sps = 2400,    # symbol rate
    siggen_modulation_deviation_Hz = 1200,      # frequency deviation

    desired_power_relative_to_sens_during_blocking_test_dB = 3, # during the blocking test the desired signal power is above the senitivity level by this value

    blocker_offset_freq_list_Hz = [-2e6, 2e6],  # blocker offset test frequencies

    blocker_cable_attenuation_dB = 7,           # blocker signal path cable loss
    
    blocker_start_power_dBm = -37,              # start Generator blocker path power
    blocker_stop_power_dBm = -22,                # stop Generator blocker path power
    blocker_power_steps = 16,                   # power steps of Generator during blocking test

    siggen_logger_settings= Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings= Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
 
)

measurement_sens_only = Sensitivity(settings=sens_settings,chip_name="EFR32FG23",board_name="BRD4204D")
measurement_sens_n_blocking = Blocking(settings=blocking_settings,chip_name="EFR32FG23",board_name="BRD4204D")

if Measure_Sensitivity_Only:
    df = measurement_sens_only.measure()

if Measure_Sensitivity_And_Blocking:
    df = measurement_sens_n_blocking.measure()

#print(df.to_string())