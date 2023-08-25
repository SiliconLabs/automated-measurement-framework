import pyvisa
import warnings
import numpy as np
from RsInstrument import *
from dataclasses import dataclass
from time import sleep, time_ns
from datetime import datetime

from common import Logger, Level
@dataclass
class Marker:
    position:float
    position_unit:str
    value:float
    value_unit:str
    def __str__(self):
        return str(self.position)+' '+self.position_unit+'/'+str(self.value)+' '+self.value_unit

@dataclass
class PowerMarker:
    position_hz:float
    power_dbm:float
    power_density_dbm_hz:float

@dataclass
class TriggerSettings:
    source:str  # immediate, video, external, IFpower
    level:float
    slope:str='POSITIVE'
    dropout_s:float=None
    holdoff_s:float=None
    delay_s:float=0

@dataclass
class LimitLinePoint:
    frequency_hz: int
    level_dbm: float
    connected: bool  # Whether to connect to previous point (or start new section)

@dataclass
class measurementSettings:
    frequency_Hz:int
    span_Hz:int
    rbw_Hz:int
    ref_level_dBm:int = 30
    mode:str='single'
    trace_storage_mode:str='OFF'
    detector:str = 'NORM'
    hold_time_s:int = 0
    attenuation_db:int = 40
    div_db:int = 10
    ref_offset_db:int = 0


@dataclass
class OperationStatus:
    calibrating:bool|None = None
    settling:bool|None = None
    sweeping:bool|None = None
    waiting_for_trig:bool|None = None
    file_operation:bool|None = None
    def is_idle(self)->bool:
        return bool(True not in self.__dict__.values())

# SpecAn is a factory class that returns the right sub-classed instrument based on the response to the *IDN? query
# Tries to indetify the instrument and use the appropriate sub-class
# If the device cannot be indetified use the generic instrument
class SpecAn(object):
    def __new__(cls, resource:str, default_timeout_ms:int=1000, auto_detect:bool=True, logger_settings :Logger.Settings = Logger.Settings() ):
        if auto_detect:
            # open a VISA session, query instrument and try to identify it
            _rm = pyvisa.ResourceManager()
            _instr = _rm.open_resource(resource_name=resource)
            idn_query_response = _instr.query("*IDN?")
            # VISA session won't be used here anymore, close it
            # Resource Manager shouldn't be closed, because it is a singleton object
            _instr.close()

            if logger_settings.module_name is None:
                logger_settings.module_name = __name__
            # instantiate the right sub-class if the instrument is properly identified
            if "Rohde&Schwarz" in idn_query_response:
                return RS_SpectrumAnalyzer(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings = logger_settings)
            elif "ANRITSU" in idn_query_response:
                return Anritsu_SignalAnalyzer(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings = logger_settings)
            else:
                warnings.warn("No specific spectrum analyzer type identified, using generic instrument.")
                return GenericSpecAn(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings = logger_settings)
        else:
            return GenericSpecAn(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings = logger_settings)

# Generic Spectrum Analyzer class
# Contains some default implementation of the various functions that might not work for all spectrum analyzers
# This class was developed based on Anritsu MS2692A, RS FSV  and RS FPL1007 
class GenericSpecAn(object):

    def __init__(self, resource_name:str, default_timeout_ms:int=1000,logger_settings: Logger.Settings = Logger.Settings()):
        try:
            self._rm = pyvisa.ResourceManager()
            self.instr = self._rm.open_resource(resource_name=resource_name)
            self.instr.timeout = default_timeout_ms
            self.instr.read_termination = '\n'
            # self.instr.opc_timeout = 3000
            # self.instr.visa_timeout = 3000
            # self.instr.instrument_status_checking = True
            self.default_timeout_ms = default_timeout_ms
            self.logger = Logger(logger_settings)
        except ResourceError:
            self.instr = None
            raise
    def __del__(self):
        try:
            self.instr.close()
            self._rm.close()
        except BaseException as error:
            self.logger.warning("Error occued at pySpecAn destructor: ",error)
    def command(self, command_str, query_opc:bool=True, timeout_ms:int=0):
        self.instr.write(command_str)
        opc = None
        start = time_ns()
        timeout = False

        self.logger.debug("SCPI Write: " + command_str)
        
        while not timeout:
            timeout = (time_ns()-start)/1e6 > timeout_ms
            try:
                
                if query_opc:
                    opc = self.instr.query_ascii_values("*OPC?")[0]
                    if opc == 0:
                        raise Exception("OPC violation")
                    else:
                        break
            except pyvisa.errors.VisaIOError as err:
                if err.abbreviation.upper()=='VI_ERROR_TMO':
                    pass
                else:
                    raise err
    def query_float(self, command_str, timeout_ms:int=0):
        r = self.instr.query_ascii_values(command_str)
        if len(r)==1:
            return float(r[0])
        else:
            return [float(x) for x in r]
    def query_int(self, command_str, timeout_ms:int=0):
        r = self.instr.query_ascii_values(command_str)
        if len(r)==1:
            return int(r[0])
        else:
            return [int(x) for x in r]
    def setFrequency(self, frequency_Hz:float):
        self.command( "FREQ:CENT " + str(frequency_Hz))
    def setFrequencyStart(self, freq_start_Hz:float):
        self.command( "FREQ:STAR " + str(freq_start_Hz))
    def getFrequencyStart(self)->float:
        return self.query_float("FREQ:STAR?")
    def setFrequencyStop(self, freq_stop_Hz:float):
        self.command( "FREQ:STOP " + str(freq_stop_Hz))
    def getFrequencyStop(self)->float:
        return self.query_float("FREQ:STOP?")
    def setSpan(self, span_Hz:float):
        self.command("FREQ:SPAN " + str(span_Hz))
    def getSpan(self):
        return self.query_float("FREQ:SPAN?")
    def setRBW(self, rbw_Hz:float):
        if rbw_Hz is None:
            self.command("BAND:AUTO ON")
        else:
            self.command("BAND " + str(rbw_Hz))
    def setVBW(self, vbw_Hz:float):
        if vbw_Hz is None:
            self.command("BAND:VID:AUTO ON")
        else:
            self.command("BAND:VID " + str(vbw_Hz))
    def setRefLevel(self, ref_level_dBm:float):
        self.command("DISPlay:WINDow:TRACe:Y:SCALe:RLEVel " + str(ref_level_dBm))
    def setAttenuation(self,attenuation_db):
        self.command("POW:ATT " + str(attenuation_db))
    def setAttenuationAuto(self):
        self.command("POW:ATT:AUTO ON")
    def setDivision(self,div_db):
        self.command("DISPlay:WINDow:TRACe:Y:SCALe:PDIVision " + str(div_db))
    def setRefOffset(self, ref_offset_db:float):
        self.command("DISPlay:WINDow:TRACe:Y:SCALe:RLEVel:OFFSET " + str(ref_offset_db))
    def configTrigger(self, trigger_settings:TriggerSettings):
        if trigger_settings is None:
            source = 'IMMEDIATE'
        else:
            source = trigger_settings.source
        self.command("TRIG:SOUR "+source)
        if trigger_settings and trigger_settings.source.upper() not in ('IMMEDIATE', 'IMM'):
            self.command(f"TRIG:{trigger_settings.source}:LEV {trigger_settings.level}DBM")
            self.command("TRIG:SLOPE "+trigger_settings.slope)
            if trigger_settings.dropout_s:
                self.command("TRIG:DTIME "+str(trigger_settings.dropout_s))
            if trigger_settings.holdoff_s:
                self.command("TRIG:HOLDOFF "+str(trigger_settings.holdoff_s))
            sources_with_offset = ("EXT", "VID")
            if trigger_settings.source.upper().startswith(sources_with_offset):
                self.command(f"TRIG:{trigger_settings.source}:DEL {trigger_settings.delay_s}")
            elif trigger_settings.delay_s:
                raise ValueError(f"Trigger offset is only supported for {sources_with_offset} sources")



    def initiate(self):
        self.command("INIT")
    def setMode(self, mode:str):
        if mode.upper() == 'CONTINUOUS':
            command_str = "INIT:CONT ON"
        elif mode.upper() == 'SINGLE':
            command_str = "INIT:CONT OFF"
        else:
            raise ValueError('Unknown operation mode')
        self.command(command_str)
    def getMaxMarker(self)->Marker:
        span = self.getSpan()
        self.command("CALC:MARK1:MAX")
        pos = self.query_float("CALC:MARK1:X?")
        val = self.query_float("CALC:MARK1:Y?")
        if span==0:
            return Marker(position=pos, position_unit='s', value=val, value_unit='dBm')
        else:
            return Marker(position=pos, position_unit='Hz', value=val, value_unit='dBm')
    def setMarkerState(self, marker_id:int, enabled:bool):
        self.command(f"CALC:MARK{marker_id}:STAT {'ON' if enabled else 'OFF'}")
    def addMarker(self, position:float, marker_id:int=1, unit:str="HZ"):
        self.command(f"CALC:MARK{marker_id}:X {position}{unit}")


    def updateDisplay(self, on_off:bool):
        if on_off:
            command_str = "SYST:DISP:UPD ON"
        else:
            command_str = "SYST:DISP:UPD OFF"
        self.command(command_str)

    # Detector setting
    # NORMal Simultaneous detection for positive and negative peaks
    # POSitive Positive peak detection
    # NEGative Negative peak detection
    # SAMPle Sample detection
    # AVERage Average value detection 
    # RMS
    def setDetector(self,detection_mode_str):
        self.command("DET " + detection_mode_str)

    def setStorageCount(self, storage_count:int):         
        command_str = "AVER:COUN " + str(storage_count)
        self.command(command_str)

    def setTraceStorageMode(self,trace_storage_mode_str,trace_num=1):
       self.logger.error("Called unimplemented function setTraceStorageMode ")

    def reset(self):
        self.command("*RST",timeout_ms=10000)

    def stopSweep(self):
        self.command('ABOR')



    def allMarkersOff(self):
        self.command("CALC:MARK:AOFF")

    def setFullSpan(self):
        self.command("FREQ:SPAN:FULL")
    def setSweepTime(self, sweep_time_s:float):
        self.command(f'SWE:TIME {sweep_time_s}')
    def getSweepTime(self):
        self.logger.error("Called unimplemented function getSweepTime")
        return 0.0
    def setSweepPoints(self, value:int):
        self.command(f"SWE:POIN {value}")
    def setAutoSweepTime(self):
        self.command('SWE:TIME:AUTO ON')
    def waitUntilIdle(self, timeout_s:float=float("inf"), polling_interval_ms=500):
        self.logger.error("Called unimplemented function waitUntilIdle ")
    def setZeroSpanMode(self):
        self.logger.error("Called unimplemented function setZeroSpanMode ")
    def disableMeasurements(self):
        self.logger.error("Called unimplemented function setZeroSpanMode ")

class Anritsu_SignalAnalyzer(GenericSpecAn):

    @dataclass
    class ScreenshotSettings:
        save_screenshot: bool = True
        filename_base: str = "Copy"
        append_timestamp: bool = True
        storage_device: str = "E"
        format: str = "PNG"

    def reset(self):
        self.setAppSwitch("SA")
        self.command("*RST",timeout_ms=10000)
        self.command("*CLS")

    #Trace storage mode setting
    # OFF Does not store data (Default value)
    # MAXHold Stores the maximum value.
    # LAVerage Stores the average value.
    # MINHold Stores the minimum value
    def setTraceStorageMode(self,trace_storage_mode_str,trace_num=1):
       self.command("TRAC:STOR:MODE " + trace_storage_mode_str)
       
    def getAllMarkers(self) -> list[Marker]:
        span = float(self.instr.query_ascii_values("FREQ:SPAN?")[0])
        position_unit = "s" if span==0 else "Hz"
        markers_raw = self.query_float("CALC:MARK:READ?")

        markers=[]
        for pos, val in zip(*[iter(markers_raw)] * 2):  # Iterate by pairs
            markers.append(Marker(position=pos,position_unit=position_unit,value=val, value_unit='dBm'))
        return markers
    def getPowerMarker(self, marker_id) -> PowerMarker:
        pos = self.query_float(f"CALC:MARK{marker_id}:X?")
        power = self.query_float(f"CALC:PMAR{marker_id}:Y?")
        return PowerMarker(position_hz=pos, power_dbm=power[0], power_density_dbm_hz=power[2])
    def getPeakList(self, threshold_dbm:float|None=None, resolution_db:float|None=None):
        if resolution_db is not None:
            self.command(f"CALC:MARK:PEAK:RES {resolution_db}DB")
        if threshold_dbm is not None:
            if self.getMaxMarker().value<threshold_dbm:
                return []
            self.command("CALC:MARK:PEAK:THR:MODE ABOV")
            self.command(f"CALC:MARK:PEAK:THR {threshold_dbm:.2f}DBM")
        self.setMarkerTableDisplay(True)
        self.command("CALC:MARK:WIDT:TYPE SPOT")
        self.command("CALC:MARK:PEAK:SORT:COUN 10")  # 10 is max
        self.command(f"CALC:MARK:PEAK:THR:STAT {'ON' if threshold_dbm is not None else 'OFF'}")
        self.command("CALC:MARK:PEAK:SORT:Y")
        return self.getAllMarkers()
    def setMarkerZoneWidth(self, value:float, unit:str="HZ", marker_id:int=1):
        self.command(f'CALC:MARK{marker_id}:WIDT:TYPE {"ZONE" if value else "SPOT"}')
        if value:
            self.command(f"CALC:MARK:WIDT {value:.2f}{unit}")
    def getMarkerZoneWidth(self, marker_id)->float:
        return self.query_float(f"CALC:MARK{marker_id}:WIDT?")
    def setMarkerIntegration(self, enabled:bool):
        self.command(f'CALC:PMAR:MODE {"ON" if enabled else "OFF"}')
    def getPowerMarkerPeakList(self, bw_hz:float, limit_dbm:float|None):
        res = []
        self.allMarkersOff()
        self.setMarkerIntegration(True)
        self.setMarkerTableDisplay(True)
        last_pos = None
        for marker_id in range(1, 11):
            self.setMarkerState(marker_id=marker_id, enabled=True)
            self.setMarkerZoneWidth(value=bw_hz, marker_id=marker_id)
            self.command(f"CALC:MARK{marker_id}:MAX:POW")
            for i in range (1, marker_id):
                self.command(f"CALC:MARK{marker_id}:MAX:NEXT")
            marker = self.getPowerMarker(marker_id)
            if marker_id > 1 and ((limit_dbm is not None and marker.power_dbm<limit_dbm) or marker.position_hz == last_pos):
                self.setMarkerState(marker_id=marker_id, enabled=False)
                break
            else:
                last_pos = marker.position_hz
                res.append(marker)
        return res
    def getTraceData(self) ->list[float]:
        return self.query_float("TRAC? TRAC1")
    
    def save_screenshot(self, settings: ScreenshotSettings=ScreenshotSettings(), verbose:bool=True):
        if settings.format:
            self.command(f'MMEM:STOR:SCR:MODE {settings.format}')
        if settings.append_timestamp:
            append = "_" + datetime.now().strftime("%Y%m%d%H%M%S")[2:]
        else:
            append = ""
        base = settings.filename_base
        if len(base + append) > 32:
            base = base[:32-len(append)]
            warnings.warn("Screenshot filename has been truncated!")
        file_name = base + append
        if verbose:
            print(f'Saving screenshot as {file_name}.{settings.format}')
        self.command(f'MMem:STOR:SCR "{file_name}",{settings.storage_device}')

    def setStorageCount(self, storage_count:int):
        if storage_count < 2:
            raise ValueError("storage_count must be >=2")
        self.command(f'AVER:COUN {storage_count}')

    def getOperationStatus(self) ->OperationStatus:
        s = self.query_int("STAT:OPER:COND?")
        status = OperationStatus()
        status.calibrating = bool(s & (1<<0))
        status.settling = bool(s & (1<<1))
        status.sweeping = bool(s & (1<<3))
        status.waiting_for_trig = bool(s & (1<<5))
        status.file_operation = bool(s & (1<<8))
        return status
    
    def waitUntilIdle(self, timeout_s:float=float("inf"), polling_interval_ms=500):
        start = time_ns()
        while True:
            if self.getOperationStatus().is_idle():
                return
            elif (time_ns() - start) / 1e9 > timeout_s:
                raise TimeoutError
            else:
                sleep(polling_interval_ms*1e-3)

    def getSweepTime(self):
        return self.query_float("SWE:TIME?")

    def configureOBWMeasurement(self, method:str="NPERcent", threshold:float=99, enabled:bool=True):
        '''

        :param enabled:
        :param method: either "NPERcent" or "XDB"
        :param threshold:
        :return:
        '''
        self.command(f'OBW {"ON" if enabled else "OFF"}')
        if enabled:
            self.command(f'OBW:METH ' + method)
            if method.upper()=="NPERCENT":
                self.command(f'OBW:PERC {threshold:.2f}')
            elif method.upper()=="XDB":
                self.command(f'OBW:XDB  {threshold:.2f}')

    def fetchOBW(self)->float:
        #self.command("INIT:OBW")
        return self.query_float("FETC:OBW?")[0]
    
    def configureACPMeasurement(self, carrier_bw_hz:int, adj_bw_hz:int, offset_hz:int|list, max_channel_diff=1, ref_power_method:str="BSIDes",enabled:bool=True):
        self.command(f'ACP {"ON" if enabled else "OFF"}')
        if not 1<=max_channel_diff<=3:
            raise ValueError("max_channel_diff needs to be >=1 and <=3")
        if enabled:
            self.command(f'ACP:CARR:RCAR:METH {ref_power_method}')
            self.command(f'ACP:CARR:LIST:BAND {int(carrier_bw_hz)}')
            self.command(f'ACP:OFFS:BAND {int(adj_bw_hz)}')
            if type(offset_hz) is not list:
                offset_hz = [offset_hz] * 3
            else:
                if len(offset_hz) != max_channel_diff:
                    raise ValueError("Length of offset_hz list must be equal to max_channel_diff")
                offset_hz += [offset_hz[-1]]*(3-len(offset_hz))  # Filling last elements
            self.command(f'ACP:OFFS:LIST {offset_hz[0]}, {offset_hz[1]}, {offset_hz[2]}')
            self.command('ACP:OFFS:LIST:STAT ON'+", ON"*(max_channel_diff-1)+", OFF"*(3-max_channel_diff))
    def fetchACP(self)->float:
        return self.query_float("FETC:ACP?")
    def disableMeasurements(self):
        self.command("CONF:SAN")
    def setZeroSpanMode(self):
        self.command("FREQ:SPAN:ZERO")
    def configureBurstAveragePowerMeasurement(self, start_time_s=0, stop_time_s=None, enabled:bool=True):
        self.command(f'BPOW {"ON" if enabled else "OFF"}')
        if enabled:
            self.command(f'BPOW:BURS:STAR {start_time_s}')
            self.command(f'BPOW:BURS:STOP {stop_time_s}')
    def fetchBurstAveragePower(self)->float:
        return self.query_float("FETC:BPOW?")
    def deleteAllLimitLines(self):
        self.command("CALC:LLIN:ALL:DEL")
    def disableAllLimitStates(self):
        for i in range(1,7):
            self.command(f"CALC:LLIN{i}:STAT OFF")
    def setLimitLine(self, points:list[LimitLinePoint], line_id=1, display_state:bool=True):
        self.command(f"CALC:LLIN{line_id}:DEL")

        self.command(f"CALC:LLIN{line_id}:CMOD:AMPL ABS")  # Set amplitude specification mode to absolute
        self.command(f"CALC:LLIN{line_id}:CMOD:FREQ ABS")  # Set frequency specification mode to relative
        self.command(f"CALC:LLIN{line_id}:DATA " + ",".join(f'{p.frequency_hz:.0f},{p.level_dbm},{"1" if p.connected else "0"}' for p in points))
        self.command(f"CALC:LLIN{line_id}:DISP ON")
        self.command(f"CALC:LLIN{line_id}:STAT OFF")
        if display_state:
            # Cycle status display state. Without this, the displayed result could be invalid
            self.command(f"CALC:LLIN{line_id}:STAT ON")
            self.command(f"CALC:LLIN{line_id}:STAT OFF")
            self.command(f"CALC:LLIN{line_id}:STAT ON")
    def setFullSpanLimitLine(self, level_dbm:float, line_id=1, display_state:bool=True):
        self.setLimitLine([LimitLinePoint(frequency_hz=0, level_dbm=level_dbm, connected=False),
                           LimitLinePoint(frequency_hz=int(100e9), level_dbm=level_dbm, connected=True)], line_id=line_id, display_state=display_state)
    def setMarkerTableDisplay(self, enabled:bool):
        self.command(f"CALC:MARK:TABL {'ON' if enabled else 'OFF'}")
    def configureChannelPowerMeasurement(self, channel_center_freq_hz:int, channel_width_hz:int, filter:str="RECT", enabled:bool=True):
        self.setMarkerTableDisplay(False)
        self.command(f'CHP {"ON" if enabled else "OFF"}')
        if enabled:
            self.command(f"CHP:FREQ:CENT {channel_center_freq_hz}")
            self.command(f"CHP:BAND:INT {channel_width_hz}")
            self.command(f"CHP:FILT:TYPE {filter}")
        pass
    def fetchChannelPower(self):
        return self.query_float("FETC:CHP?")
    def setAppSwitch(self, APP:str):
        if APP == "SA":
            command_str = "INST SPECT"
        elif APP == "SG":
            command_str = "INST SG"
        elif APP == "PN":
            command_str = "INST PNOISE"
        else: 
            print("\nwrong application switch selected")
        self.command(command_str)   
    # def getAppSwitch(self):
    #     return self.instr.query_ascii_values("INST?")
        
    # def sigGenControl(self, on_off:bool):
    #     if on_off:
    #         command_str = "CALC:SGC ON"
    #     else:
    #         command_str = "CALC:SGC OFF"
    #     self.command(command_str)
    # def getsigGenControl(self):
    #     return self.instr.query_ascii_values("CALC:SGC?")

    def setSigGenOutput_toggle(self, on_off:bool):
        if on_off:
            command_str = "OUTP ON"
        else:
            command_str = "OUTP OFF"
        self.command(command_str)
    def getSigGenOutput_toggle(self):
        return self.instr.query_ascii_values("OUTP?")

    def setSigGenPower_dBm(self, pwr_dBm:float):
        self.command("POW " + str(pwr_dBm) + "DBM")
    def getSigGenPower_dBm(self):
        return self.instr.query_ascii_values("POW?")
    
    def setSigGenFreq_Hz(self, freq_Hz:float):
        self.command("FREQ " + str(freq_Hz))
    def getSigGenFreq_Hz(self):
        return self.instr.query_ascii_values("FREQ?")

    
# Rohde&Schwarz Spectrum Analyzer
# Using the RsInstrument package provided by R&S 
# This class was developed based on RS FPL1007 and RS FSV
class RS_SpectrumAnalyzer(GenericSpecAn):
    def __init__(self, resource_name:str, default_timeout_ms:int=1000,logger_settings: Logger.Settings = Logger.Settings()):
        try:
            self.instr = RsInstrument(resource_name=resource_name, id_query=True, reset=True)
            self.instr.opc_timeout = 3000
            self.instr.visa_timeout = 3000
            self.instr.instrument_status_checking = True
            self.default_timeout_ms = default_timeout_ms

            if logger_settings.module_name is None:
                logger_settings.module_name = __name__
            self.logger = Logger(logger_settings)
        except ResourceError:
            self.instr = None
            raise
    def __del__(self):
        try:
            self.instr.close()
            self._rm.close()
        except:
            pass
    def command(self, command_str, query_opc:bool=True, timeout_ms:int=0):
        self.instr.write_str(command_str)
        self.logger.debug("SCPI Write: " + command_str)
        if timeout_ms==0:
            self.instr.query_opc(self.default_timeout_ms)
        else:
            self.instr.query_opc(timeout_ms)
    def reset(self):
        self.command("*RST",timeout_ms=10000)
        self.command("*CLS")
    def setFrequency(self, frequency_Hz:float):
        command_str = "FREQ:CENT " + str(frequency_Hz/1e9) + " GHz"
        self.command(command_str)
    def setSpan(self, span_Hz:float):
        command_str = "FREQ:SPAN " + str(span_Hz/1e6) + " MHz"
        self.command(command_str)
    def setRBW(self, rbw_Hz:float):
        command_str = "BAND " + str(rbw_Hz/1e3) + " kHz"
        self.command(command_str)
    def setVBW(self, vbw_Hz:float):
        command_str = "BAND:VID " + str(vbw_Hz/1e3) + " kHz"
        self.command(command_str)
    def setRefLevel(self, ref_level_dBm:float):
        command_str = "DISPlay:WINDow:TRACe:Y:SCALe:RLEVel " + str(ref_level_dBm) + "DBM"
        self.command(command_str)
    def setAttenuation(self,attenuation_db):
        self.command("INP:ATT " + str(attenuation_db)+"dB")
    def setTraceStorageMode(self,trace_storage_mode_str,trace_num=1):
        try:
            self.command("DISP:TRAC"+str(trace_num)+":MODE " + trace_storage_mode_str)
        except:
            pass
    def setDivision(self,div_db):
        self.command("DISP:TRAC:Y:MODE ABS ")
        self.command("DISP:TRAC:Y:RPOS 100PCT")
        self.command("DISP:TRAC:Y " + str(div_db*10)+"dB")
    def setSweepPoints(self, npoints:int):
        command_str = "SWE:POIN " + str(npoints)
        self.command(command_str)

    # def setSweepCount(self, nsweeps:int = 1):           
    #     command_str = "SWE:COUN " + str(npoints)
    #     self.command(command_str)

    def initiate(self, timeout_ms:int=0):
        self.command("INIT", timeout_ms=timeout_ms)
    def updateDisplay(self, on_off:bool):
        if on_off:
            command_str = "SYST:DISP:UPD ON"
        else:
            command_str = "SYST:DISP:UPD OFF"
        self.command(command_str)
    def configTrigger(self, trigger_settings:TriggerSettings):
        self.command("TRIG:SOUR "+trigger_settings.source)
        if trigger_settings.source.upper() not in ('IMMEDIATE', 'IMM'):
            self.command("TRIG:LEVEL:IQPOWER "+str(trigger_settings.level))
            self.command("TRIG:SLOPE "+trigger_settings.slope)
            self.command("TRIG:DTIME "+str(trigger_settings.dropout_s))
            self.command("TRIG:HOLDOFF "+str(trigger_settings.offset_s))
    def getMaxMarker(self)->Marker:
        span = self.instr.query("FREQ:SPAN?")
        self.instr.write_str("CALC1:MARK1:MAX")
        pos = self.instr.query_float("CALC1:MARK1:X?")
        val = self.instr.query_float("CALC1:MARK1:Y?")
        if span==0:
            return Marker(position=pos, position_unit='s', value=val, value_unit='dBm')
        else:
            return Marker(position=pos, position_unit='Hz', value=val, value_unit='dBm')
        
    def getSweepTime(self):
        return self.instr.query_float("SWE:TIME?")
