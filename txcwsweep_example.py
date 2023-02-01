from txcwsweep import TXCWSweep
from common import logger as lg

sweep_settings = TXCWSweep.Settings(
    freq_list_hz = [868e6,915e6],
    psu_present = True,
    pavdd_levels = [3.0,3.3],
    wstk_com_port = "COM5",
    specan_address = 'TCPIP::169.254.250.234::INSTR',
    psu_address = "ASRL8::INSTR",
    specan_detector_type="APE" ,#auto peak at rohde
    specan_logger_settings= lg.Logger.Settings(logging_level=lg.Level.INFO),
    wstk_logger_settings = lg.Logger.Settings(logging_level=lg.Level.INFO)
    
)



measurement = TXCWSweep(settings=sweep_settings,chip_name="EFR32FG23",board_name="BRD4204D")

df = measurement.measure()

print(df.to_string())