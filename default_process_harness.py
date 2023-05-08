from txcwsweep import TXCWSweep
from rxtests_with_excel_plotting import Sensitivity, Waterfall
from common import Logger,Level

harness_logger_settings = Logger.Settings(module_name = 'default_harness',logging_level=Level.DEBUG)
harness_logger = Logger(harness_logger_settings)

freq_list = [2405e6,2450e6,2478e6]
wstk_com_port = "COM6"
specan_address = 'TCPIP::169.254.88.77::INSTR'
psu_address = "ASRL8::INSTR"
siggen_address = 'GPIB0::5::INSTR'
specan_detector_type="APE" #auto peak at rohde


chip_name = "EFR32BG22"
board_name = "BRD4183A"

#info_logging = Logger.Settings(logging_level=Level.INFO)

tx_sweep_settings = TXCWSweep.Settings(

    freq_list_hz = freq_list,
    psu_present = True,
    pavdd_levels = [3.3],   

    max_pwr_state=15,
    min_pwr_state=0,
    pwr_num_steps=16,

    harm_order_up_to=5,

    specan_detector_type=specan_detector_type ,#auto peak at rohde
    specan_rbw_hz=100e3,
    specan_ref_level_dbm=8,
    specan_ref_offset=2.7,

    wstk_com_port = wstk_com_port,
    specan_address = specan_address,
    psu_address = psu_address,

    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.DEBUG),

)

rx_sens_settings =  Sensitivity.Settings(
    #ctune_initial=28,

    measure_with_CTUNE_w_SA = True,    
    measure_with_CTUNE_w_SG = False,    

    freq_list_hz = freq_list,                 
    wstk_com_port = wstk_com_port,
    siggen_address = siggen_address,           
    specan_address = specan_address, 
    #specan_span_hz = SA_Span_CTUNE, 
    #specan_rbw_hz = SA_Rbw_CTUNE,   
    cable_attenuation_dB = 2.7,   
    siggen_power_start_dBm = -80, 
    siggen_power_stop_dBm = -110,   
    siggen_power_steps = 40,        
    siggen_modulation_type = 'FSK2',            
    siggen_modulation_symbolrate_sps = 250e3,   
    siggen_modulation_deviation_Hz = 125e3,     
    logger_settings= Logger.Settings(logging_level=Level.DEBUG),
    siggen_logger_settings = Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)

)

rx_waterfall_settings =  Sensitivity.Settings(
    #ctune_initial=28,

    measure_with_CTUNE_w_SA = True,    
    measure_with_CTUNE_w_SG = False,    

    freq_list_hz = freq_list,                 
    wstk_com_port = wstk_com_port,
    siggen_address = siggen_address,           
    specan_address = specan_address, 
    #specan_span_hz = SA_Span_CTUNE, 
    #specan_rbw_hz = SA_Rbw_CTUNE,   
    cable_attenuation_dB = 2.7,   
    siggen_power_start_dBm = -30, 
    siggen_power_stop_dBm = -100,   
    siggen_power_steps = 80,        
    siggen_modulation_type = 'FSK2',            
    siggen_modulation_symbolrate_sps = 250e3,   
    siggen_modulation_deviation_Hz = 125e3,     
    logger_settings= Logger.Settings(logging_level=Level.DEBUG),
    siggen_logger_settings = Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)

)

harness_logger.info("---Default QI Process Measurement Harness Started---")

tx_measurements = TXCWSweep(tx_sweep_settings,chip_name,board_name)
rx_sens = Sensitivity(rx_sens_settings,chip_name,board_name)
rx_waterfall = Waterfall(rx_waterfall_settings,chip_name,board_name)


harness_logger.info("Press Enter to Proceed with TX Measurements?")
input()
harness_logger.info("Starting TX CW Sweep Measurement!")
tx_df = tx_measurements.measure()
harness_logger.info(tx_df)

tx_measurements.initialize_psu()

harness_logger.info("Press Enter to Proceed with RX Measurements?")
input()
harness_logger.info("Starting Sensitivity Measurement!")
rx_sens_df = rx_sens.measure()
harness_logger.info(rx_sens_df)

harness_logger.info("Starting Waterfall Measurement!")
rx_waterfall_df = rx_waterfall.measure()
harness_logger.info(rx_waterfall_df)

harness_logger.info("---All Measurements Done!---")