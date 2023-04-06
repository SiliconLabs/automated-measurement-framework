from rxtests_with_excel_plotting import Sensitivity, Blocking, FreqOffset_Sensitivity, RSSI_Sweep, Waterfall
from common import Logger, Level

#################################################################################################################################################
# Select the RX test options here:
Measure_Sensitivity = True                          # Sensitivity measurement 
Measure_Waterfall = False                           # Full waterfall measurement between defined input power levels
Measure_Blocking_w_Sensitivity = False              # Sensitivity and Blocking measurements
Measure_Sensitivity_w_FrequencyOffset = False       # Sensitivity measurement with frequency offsets defined
Measure_RSSI_Sweep = False                          # RSSI sweep versus input power and frequency
# Perform crystal CTUNE tuning before the tests?
CTUNE_Tuning_w_SA = False                           # CTUNE tuning with the spectrum analyzer, for blocking measurements do not use SA for CTUNE tuning, use SG below instead
CTUNE_Tuning_w_SG = False                           # CTUNE tuning with the signal generator
# DUT names
Chip_Name = 'EFR32FG23'                             # Chip name of DUT
Board_Name = 'BRD4204D'                             # Board name of DUT
# Test Equipment and DUT Address Settings
WSTK_COM_Port = 'COM3'                              # WSTK board COM port
SigGen_Address = 'GPIB0::5::INSTR'                  # Signal Generator address
SpecAn_Address = 'TCPIP::169.254.88.77::INSTR'      # Spectrum Analyzer address
# Desired Signal Test Frequencies
Frequency_Start_Hz = 868e6                          # Test frequency start
Frequency_Stop_Hz = 928e6                           # Test frequency stop
Frequency_Num_Steps = 31                            # Number of frequency points between start and stop defined above
Frequency_List_Hz = [876e6, 902e6]                  # List of Test frequencies. This list is used when given, if it is None then list is created from start, stop and steps defined above.
# Inpu power and modulation settings
SigGen_Power_Start_dBm = -100                       # Signal Generator start power, used on the desired signal path
SigGen_Power_Stop_dBm = -113                        # Signal Generator stop power, used on the desired signal path
SigGen_Power_Num_Steps = 27                         # Number of power steps, used on the desired signal path
Modulation_Type = 'FSK2'                            # Modulation type
Symbol_Rate_bps = 100e3                             # Symbol rate in bps
Freq_Deviation_Hz = 50e3                            # Frequency deviation in Hz
# Cable losses
Desired_Path_Cable_Attenuation_dB = 7               # cable loss on the desired signal path
Blocker_Path_Cable_Attenuation_dB = 7               # cable loss on hte blocker signal path
# Blocking test condition
Desired_Pwr_relative_to_Sens_During_Blocking = 3    # during the blocking test the desired signal power is above the sensitivity level by this value 
# Blocker signal frequencies
Blocker_FrequencyOffset_Start_Hz = -8e6             # blocker signal start frequency offset
Blocker_FrequencyOffset_Stop_Hz = 8e6               # blocker signal stop frequency offset
Blocker_FrequencyOffset_Num_Steps = 5               # number of frequency offset points of the blocker signal
Blocker_FrequencyOffset_List_Hz = [-2e6, 2e6]       # List of frequency offset points of the blocker signal. This list is used when given, if it is None then list is created from start, stop and steps defined above.
# Blocker power settings (CW)
Blocker_Power_Start_dBm = -50                       # blocker signal start power
Blocker_Power_Stop_dBm = -5                         # blocker signal stop power
Blocker_Power_Num_Steps = 46                        # number of blocker power levels
Blocker_Power_List_dBm = None                       # List of power points of the blocker signal. This list is used when given, if it is None then list is created from start, stop and steps defined above.
# Offset frequencies for freq-offset sensitivitiy tests
Frequency_Offset_Start_Hz = -2000                   # frequency offset start for offset-Sensitivity test
Frequency_Offset_Stop_Hz = 2000                     # frequency offset stop for offset-Sensitivity test
Frequency_Offset_Steps = 21                         # number of frequency offset steps during offset-Sensitivity test                      
Frequency_Offset_List_Hz = None                     # List of frequency offsets. This list is used when given, if it is None then list is created from start, stop and steps defined above.
# Input frequency settings for RSSI sweep tests
Frequency_SigGen_Start_Hz = 876e6                   # SigGen frequency start for rssi sweep test
Frequency_SigGen_Stop_Hz = 902e6                    # SigGen frequency stop for rssi sweep test
Frequency_SigGen_Steps = 3                          # number of frequency steps during rssi sweep test                   
Frequency_SigGen_List_Hz = None                     # List of SigGen frequencies. This list is used when given, if it is None then list is created from start, stop and steps defined above.
# SA settings during CTUNE tuning
SA_Span_CTUNE = 200e3                               # SA span setting during CTUNE tuning
SA_Rbw_CTUNE = 10e3                                 # SA RBW setting during CTUNE tuning
#################################################################################################################################################

sensitivity_settings = Sensitivity.Settings(
    measure_with_CTUNE_w_SA = CTUNE_Tuning_w_SA,    
    measure_with_CTUNE_w_SG = CTUNE_Tuning_w_SG,    
    freq_start_hz = Frequency_Start_Hz,
    freq_stop_hz = Frequency_Stop_Hz,
    freq_num_steps = Frequency_Num_Steps,
    freq_list_hz = Frequency_List_Hz,                 
    wstk_com_port = WSTK_COM_Port,
    siggen_address = SigGen_Address,           
    specan_address = SpecAn_Address, 
    specan_span_hz = SA_Span_CTUNE, 
    specan_rbw_hz = SA_Rbw_CTUNE,   
    cable_attenuation_dB = Desired_Path_Cable_Attenuation_dB,   
    siggen_power_start_dBm = SigGen_Power_Start_dBm, 
    siggen_power_stop_dBm = SigGen_Power_Stop_dBm,   
    siggen_power_steps = SigGen_Power_Num_Steps,        
    siggen_modulation_type = Modulation_Type,            
    siggen_modulation_symbolrate_sps = Symbol_Rate_bps,   
    siggen_modulation_deviation_Hz = Freq_Deviation_Hz,      
    siggen_logger_settings = Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

blocking_settings = Blocking.Settings(
    measure_with_CTUNE_w_SA = CTUNE_Tuning_w_SA,    
    measure_with_CTUNE_w_SG = CTUNE_Tuning_w_SG,     
    freq_start_hz = Frequency_Start_Hz,
    freq_stop_hz = Frequency_Stop_Hz,
    freq_num_steps = Frequency_Num_Steps,
    freq_list_hz = Frequency_List_Hz,                 
    wstk_com_port = WSTK_COM_Port,
    siggen_address = SigGen_Address,             
    specan_address = SpecAn_Address, 
    cable_attenuation_dB = Desired_Path_Cable_Attenuation_dB,                   
    siggen_power_start_dBm = SigGen_Power_Start_dBm,              
    siggen_power_stop_dBm = SigGen_Power_Stop_dBm,               
    siggen_power_steps = SigGen_Power_Num_Steps,                    
    siggen_modulation_type = Modulation_Type,            
    siggen_modulation_symbolrate_sps = Symbol_Rate_bps,    
    siggen_modulation_deviation_Hz = Freq_Deviation_Hz,      
    desired_power_relative_to_sens_during_blocking_test_dB = Desired_Pwr_relative_to_Sens_During_Blocking,
    blocker_cable_attenuation_dB = Blocker_Path_Cable_Attenuation_dB,
    blocker_offset_start_freq_Hz = Blocker_FrequencyOffset_Start_Hz,
    blocker_offset_stop_freq_Hz = Blocker_FrequencyOffset_Stop_Hz,
    blocker_offset_freq_steps = Blocker_FrequencyOffset_Num_Steps,
    blocker_offset_freq_list_Hz = Blocker_FrequencyOffset_List_Hz,            
    blocker_start_power_dBm = Blocker_Power_Start_dBm,             
    blocker_stop_power_dBm = Blocker_Power_Stop_dBm,                
    blocker_power_steps = Blocker_Power_Num_Steps,                   
    blocker_power_list_dBm = Blocker_Power_List_dBm,
    siggen_logger_settings = Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

FreqOffset_sensitivity_settings = FreqOffset_Sensitivity.Settings(
    measure_with_CTUNE_w_SA = CTUNE_Tuning_w_SA,    
    measure_with_CTUNE_w_SG = CTUNE_Tuning_w_SG,    
    freq_start_hz = Frequency_Start_Hz,
    freq_stop_hz = Frequency_Stop_Hz,
    freq_num_steps = Frequency_Num_Steps,
    freq_list_hz = Frequency_List_Hz,                 
    wstk_com_port = WSTK_COM_Port,
    siggen_address = SigGen_Address,           
    specan_address = SpecAn_Address, 
    specan_span_hz = SA_Span_CTUNE, 
    specan_rbw_hz = SA_Rbw_CTUNE,   
    cable_attenuation_dB = Desired_Path_Cable_Attenuation_dB,   
    siggen_power_start_dBm = SigGen_Power_Start_dBm, 
    siggen_power_stop_dBm = SigGen_Power_Stop_dBm,   
    siggen_power_steps = SigGen_Power_Num_Steps,        
    siggen_modulation_type = Modulation_Type,            
    siggen_modulation_symbolrate_sps = Symbol_Rate_bps,   
    siggen_modulation_deviation_Hz = Freq_Deviation_Hz,   
    freq_offset_start_Hz = Frequency_Offset_Start_Hz,
    freq_offset_stop_Hz = Frequency_Offset_Stop_Hz,   
    freq_offset_steps = Frequency_Offset_Steps,
    freq_offset_list_Hz = Frequency_Offset_List_Hz, 
    freq_offset_logger_settings = Logger.Settings(logging_level=Level.INFO),
    siggen_logger_settings = Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

rssi_sweep_settings = RSSI_Sweep.Settings(
    measure_with_CTUNE_w_SA = CTUNE_Tuning_w_SA,    
    measure_with_CTUNE_w_SG = CTUNE_Tuning_w_SG,    
    freq_start_hz = Frequency_Start_Hz,
    freq_stop_hz = Frequency_Stop_Hz,
    freq_num_steps = Frequency_Num_Steps,
    freq_list_hz = Frequency_List_Hz,                 
    wstk_com_port = WSTK_COM_Port,
    siggen_address = SigGen_Address,           
    specan_address = SpecAn_Address, 
    specan_span_hz = SA_Span_CTUNE, 
    specan_rbw_hz = SA_Rbw_CTUNE,   
    cable_attenuation_dB = Desired_Path_Cable_Attenuation_dB,   
    siggen_power_start_dBm = SigGen_Power_Start_dBm, 
    siggen_power_stop_dBm = SigGen_Power_Stop_dBm,   
    siggen_power_steps = SigGen_Power_Num_Steps,     
    siggen_freq_start_Hz = Frequency_SigGen_Start_Hz, 
    siggen_freq_stop_Hz = Frequency_SigGen_Stop_Hz,
    siggen_freq_steps = Frequency_SigGen_Steps, 
    siggen_freq_list_Hz = Frequency_SigGen_List_Hz,    
    siggen_modulation_type = Modulation_Type,            
    siggen_modulation_symbolrate_sps = Symbol_Rate_bps,   
    siggen_modulation_deviation_Hz = Freq_Deviation_Hz,      
    siggen_logger_settings = Logger.Settings(logging_level=Level.INFO),
    specan_logger_settings = Logger.Settings(logging_level=Level.INFO),
    wstk_logger_settings = Logger.Settings(logging_level=Level.INFO)
)

measurement_sensitivity = Sensitivity(settings=sensitivity_settings,chip_name=Chip_Name,board_name=Board_Name)
measurement_blocking = Blocking(settings=blocking_settings,chip_name=Chip_Name,board_name=Board_Name)
measurement_FreqOffset_sensitivity = FreqOffset_Sensitivity(settings=FreqOffset_sensitivity_settings,chip_name=Chip_Name,board_name=Board_Name)
measurement_waterfall = Waterfall(settings=sensitivity_settings,chip_name=Chip_Name,board_name=Board_Name)
measurement_rssi_sweep = RSSI_Sweep(settings=rssi_sweep_settings,chip_name=Chip_Name,board_name=Board_Name)

if Measure_Sensitivity:
    df = measurement_sensitivity.measure()
if Measure_Blocking_w_Sensitivity:
    df = measurement_blocking.measure()
if Measure_Sensitivity_w_FrequencyOffset:
    df = measurement_FreqOffset_sensitivity.measure()
if Measure_Waterfall:
    df = measurement_waterfall.measure()
if Measure_RSSI_Sweep:
    df = measurement_rssi_sweep.measure()

#print(df.to_string())