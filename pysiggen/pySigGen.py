import pyvisa
import warnings
import numpy as np
from dataclasses import dataclass
from time import sleep
from common import Logger, Level
import pandas as pd
from RsInstrument import *

@dataclass
class ModulationConfig:
    type:str = "FSK2"
    symbolrate_sps:int = 100000
    deviation_Hz:int = 50000
    bits_per_symbol:int = 1

    #etc
    def __str__(self):
        return (self.type) + "\nbitrate: " + str(self.symbolrate_sps/1e3) + " ksps" + "\ndeviation: " + str(self.deviation_Hz/1e3) + " kHz"

@dataclass
class SigGenSettings:
    frequency_Hz:int = 868000000
    amplitude_dBm:float = -60
    modulation:ModulationConfig= ModulationConfig()
    rf_on:bool =False 
    mod_on:bool =False
    stream_type:str = "PN9"
    filter_type:str = "GAUS"
    filter_BbT:float = 0.5
    custom_on:bool =False
    pattern_repeat = "CONT"
    trigger_type = "BUS"
    per_packet_filename = "pysiggen/packets/std_rail_packet.csv"
    per_packet_siggen_name = "TEMP"

    def __str__(self):
        return str(self.frequency_Hz/1e6) + ' MHz' + '\n' + str(self.amplitude_dBm) +' dBm' + '\nmodulation: ' + str(self.modulation) + ' ' +  '\nMOD on: '+ str(self.mod_on) + '\nRF On: ' + str(self.rf_on) + '\nStream: ' + str(self.stream_type) + '\nFilter: ' + str(self.filter_type) + '\nFilter_BbT: ' + str(self.filter_BbT) + '\nCustom On: ' + str(self.custom_on)
    

# SigGen is a factory class that returns the right sub-classed instrument based on the response to the *IDN? query
# Tries to identify the instrument and use the appropriate sub-class
# If the device cannot be identified use the generic instrument
class SigGen(object):
    def __new__(cls, resource:str, default_timeout_ms:int=1000, auto_detect:bool=True,logger_settings :Logger.Settings = Logger.Settings()):
        if auto_detect:
            # open a VISA session, query instrument and try to identify it
            _rm = pyvisa.ResourceManager()
            _instr = _rm.open_resource(resource_name=resource)
            idn_query_response = _instr.query("*IDN?")
            if logger_settings.module_name is None:
                logger_settings.module_name = __name__
            # VISA session won't be used here anymore, close it
            # Resource Manager shouldn't be closed, because it is a singleton object
            _instr.close()
            # instantiate the right sub-class if the instrument is properly identified
            if "Hewlett" in idn_query_response:
                return HPSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)
            elif "Rohde&Schwarz" in idn_query_response:
                return RS_SigGen(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)
            elif "ANRITSU" in idn_query_response:
                return AnritsuSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)
            else:
                warnings.warn("No specific power supply type identified, using generic instrument.")
                return GenericSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)
        else:
            return GenericSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)


# Generic Signal generator class
# Contains some default implementation of the various functions that might not work for all generators
#
class GenericSigGen(object):
    def __init__(self, resource_name:str, default_timeout_ms:int=1000,logger_settings :Logger.Settings = Logger.Settings()):
        try:
            self._rm = pyvisa.ResourceManager()
            self.instr = self._rm.open_resource(resource_name=resource_name)
            self.instr.timeout = default_timeout_ms
            self.instr.opc_timeout = 3000
            self.instr.visa_timeout = 3000
            self.instr.read_termination = '\n'
            #self.instr.query_delay=0.2
            self.default_timeout_ms = default_timeout_ms
            self.logger = Logger(logger_settings)
        except:
            self.instr = None
            raise
    def __del__(self):
        try:
            self.instr.close()
            self._rm.close()
        except pyvisa.errors.InvalidSession as error:
            self.logger.warn("Session already closed at destructor, possibly by other instrument")
    def command(self, command_str, query_opc:bool=True, write_delay_ms:float=0,binary_format=False,hex_string=''):
        if binary_format:            
            self.instr.write_binary_values(command_str, bytes.fromhex(hex_string), datatype='b', is_big_endian=True)
            self.logger.debug("SCPI Binary Write: "+str(command_str) + str(hex_string))
        else:
            self.instr.write(command_str)
            self.logger.debug("SCPI Write: "+str(command_str))
        #self.logger.debug("Scpi Errors: "+ str(self.getError()))
        sleep(write_delay_ms/1000) # this delay is necessary to give time for an older instrument to process the write
        if query_opc:
            opc = self.instr.query_ascii_values("*OPC?")[0]
            if opc == 0:
                raise Exception("OPC violation")
    def query_float(self, command_str, timeout_ms:int=0):
        r = self.instr.query_ascii_values(command_str)
        #print(r)
        if len(r)==1:
            return float(r[0])
        else:
            return [float(x) for x in r]
    def query(self,command_str):
        return self.instr.query(command_str)
    def reset(self):
        self.command("*RST",write_delay_ms=2000)
    def setFrequency(self, frequency_Hz:int):
        self.command("FREQ " + str(frequency_Hz)+ " Hz")
    def getFrequency(self):
        frequency_Hz = self.query_float("FREQ?")
        return frequency_Hz
    def setAmplitude(self, amplitude_dBm:float):
        self.logger.error("This function is not implemented")
    def getAmplitude(self):
        self.logger.error("This function is not implemented")
    def setModulation_type(self, type:str):
        self.logger.error("This function is not implemented")
    def getModulation_type(self):
        self.logger.error("This function is not implemented")
    def setSymbolrate(self, symbolrate_sps:int):
        self.logger.error("This function is not implemented")
    def getSymbolrate(self):
        self.logger.error("This function is not implemented")
    def setDeviation(self, deviation_Hz:int):
        self.logger.error("This function is not implemented")
    def getDeviation(self):
        self.logger.error("This function is not implemented")
    
    def setFilter(self, filter_type:str):
        self.logger.error("This function is not implemented")
    def getFilter(self):
        self.logger.error("This function is not implemented")    
    def setFilterBbT(self, filter_BbT:float):
        self.logger.error("This function is not implemented")
    def getFilterBbT(self):
        self.logger.error("This function is not implemented")

    def toggleCustom(self, custom_on:bool):
        self.logger.error("This function is not implemented")

    def toggleRFOut(self, rf_on:bool):
        if rf_on:
            self.command("OUTP:STAT " + "ON")
        else:
            self.command("OUTP:STAT " + "OFF")
    def updateDisplay(self,disp_on:bool):
        self.logger.error("This function is not implemented")
    def setStreamType(self, stream_type:str):
        self.logger.error("This function is not implemented")
    def getStreamType(self):
        self.logger.error("This function is not implemented")
    
    def setTriggerType(self,trigger_type:str): # KEY|BUS|EXT
        self.logger.error("This function is not implemented")

    def setPatternRepeat(self, sing_cont:str): # CONT|SING
        self.logger.error("This function is not implemented")

    def sendTrigger(self,num:int,delay:float=0):
        self.logger.error("This function is not implemented")

    def setBinaryData(self,data_csv_filename:str,bitfile_name:str):
        self.logger.error("This function is not implemented")
    
    def getSettings(self):
        settings = SigGenSettings()
        settings.frequency_Hz = self.getFrequency()
        settings.amplitude_dBm = self.getAmplitude()
        settings.modulation.type = self.getModulation_type()
        settings.modulation.symbolrate_sps = self.getSymbolrate()
        settings.modulation.deviation_Hz = self.getDeviation()
        settings.stream_type = self.getStreamType()
        settings.filter_type = self.getFilter()
        settings.filter_BbT = self.getFilterBbT()
        return settings
    def setStream(self, settings:SigGenSettings):
        self.setFrequency(settings.frequency_Hz)
        self.setAmplitude(settings.amplitude_dBm)
        self.setModulation_type(settings.modulation.type)
        self.setDeviation(settings.modulation.deviation_Hz)
        self.setSymbolrate(settings.modulation.symbolrate_sps)
        self.setBinaryData(settings.per_packet_filename,settings.per_packet_siggen_name)
        self.toggleModulation(settings.mod_on)
        self.toggleRFOut(settings.rf_on)
        self.setStreamType(settings.stream_type)
        self.setPatternRepeat(settings.pattern_repeat)
        self.setTriggerType(settings.trigger_type)
        self.setFilter(settings.filter_type)
        self.setFilterBbT(settings.filter_BbT)
        self.toggleCustom(settings.custom_on)


    def getError(self)->str:
        error = self.instr.query("SYST:ERR?") 
        self.logger.error("SCPI Error: "+str(error))
        return str(error)

class HPSigGen(GenericSigGen):
    def __init__(self, resource_name:str, default_timeout_ms:int=1000,logger_settings :Logger.Settings = Logger.Settings()):
        try:
            self._rm = pyvisa.ResourceManager()
            self.instr = self._rm.open_resource(resource_name=resource_name)
            self.instr.timeout = default_timeout_ms
            self.instr.opc_timeout = 3000
            self.instr.visa_timeout = 3000
            self.instr.read_termination = '\n'
            #self.instr.query_delay=0.2
            self.default_timeout_ms = default_timeout_ms
            self.logger = Logger(logger_settings)
        except:
            self.instr = None
            raise
    def __del__(self):
        try:
            self.instr.close()
            self._rm.close()
        except pyvisa.errors.InvalidSession as error:
            self.logger.warn("Session already closed at destructor, possibly by other instrument")
    def command(self, command_str, query_opc:bool=True, write_delay_ms:float=0,binary_format=False,hex_string=''):
        if binary_format:            
            self.instr.write_binary_values(command_str, bytes.fromhex(hex_string), datatype='b', is_big_endian=True)
            self.logger.debug("SCPI Binary Write: "+str(command_str) + str(hex_string))
        else:
            self.instr.write(command_str)
            self.logger.debug("SCPI Write: "+str(command_str))
        #self.logger.debug("Scpi Errors: "+ str(self.getError()))
        sleep(write_delay_ms/1000) # this delay is necessary to give time for an older instrument to process the write
        if query_opc:
            opc = self.instr.query_ascii_values("*OPC?")[0]
            if opc == 0:
                raise Exception("OPC violation")
    def query_float(self, command_str, timeout_ms:int=0):
        r = self.instr.query_ascii_values(command_str)
        #print(r)
        if len(r)==1:
            return float(r[0])
        else:
            return [float(x) for x in r]
    def query(self,command_str):
        return self.instr.query(command_str)
    def setFrequency(self, frequency_Hz:int):
        self.command("FREQ " + str(frequency_Hz)+ " Hz")
    def getFrequency(self):
        frequency_Hz = self.query_float("FREQ?")
        return frequency_Hz
    def setAmplitude(self, amplitude_dBm:float):
        self.command("POW:AMPL " + str(amplitude_dBm)+" dBm")
    def getAmplitude(self):
        amplitude_dBm = self.query_float("POW:AMPL?")
        return amplitude_dBm
    def setModulation_type(self, type:str):
        self.command("RADio:CUSTOM:MODulation " + str(type) )
    # def setModulation_state(self):
    #     self.command("RADio:CUSTOM " + "ON", write_delay_ms=10000)
    def getModulation_type(self):
        type = self.query_float("RADio:CUSTOM:MODulation")
        return type
    def setSymbolrate(self, symbolrate_sps:int):
        self.command("RADio:CUSTOM:SRATe " + str(symbolrate_sps))
    def getSymbolrate(self):
        symbolrate_sps = self.query_float("RADio:DMODulation:CUSTOM:SRATe")
        return symbolrate_sps
    def setDeviation(self, deviation_Hz:int):
        self.command("RADio:CUSTOM:MODulation:FSK:DEViation " + str(deviation_Hz))
    def getDeviation(self):
        deviation_Hz = self.query_float("DEV")
        return deviation_Hz
    
    def setFilter(self, filter_type:str):
        self.command("RADio:CUSTom:FILTer " + filter_type)
    def getFilter(self):
        filter_type = self.query_float("RADio:CUSTom:FILTer?")
        return filter_type     
    def setFilterBbT(self, filter_BbT:float):
        self.command(":RADio:CUSTom:BBT " + str(filter_BbT))
    def getFilterBbT(self):
        filter_BbT = self.query_float(":RADio:CUSTom:BBT?")
        return filter_BbT

    def toggleCustom(self, custom_on:bool):
        if custom_on:
            self.command(":RADio:CUSTom:STATe ON")
        else:
            self.command(":RADio:CUSTom:STATe OFF")

    def toggleModulation(self, mod_on:bool):
        if mod_on:
            self.command("OUTP:MOD " + "ON")
        else:
            self.command("OUTP:MOD " + "OFF")
    def toggleRFOut(self, rf_on:bool):
        if rf_on:
            self.command("OUTP:STAT " + "ON")
        else:
            self.command("OUTP:STAT " + "OFF")
    def updateDisplay(self,disp_on:bool):
        if disp_on:
            self.command("DISPlay:REMote " + "ON")
        else:
            self.command("DISPlay:REMote " + "OFF")
        self.command("DISPlay:REMote " + "ON")
    def setStreamType(self, stream_type:str):
        self.command("RADio:CUSTom:DATA " + str(stream_type))
        errors = self.getError()
        if errors.find("Illegal")>0:
           self.logger.error("If file stream was added, you probably forgot the \"\"")
    def getStreamType(self):
        stream_type = self.query_float("RADio:CUSTom:DATA?")
        return stream_type  
    
    def setTriggerType(self,trigger_type:str): # KEY|BUS|EXT
        self.command("RADio:CUSTom:TRIGger " + trigger_type)

    def setPatternRepeat(self, sing_cont:str): # CONT|SING
        self.command("RADio:CUSTom:REPeat " + sing_cont)

    def sendTrigger(self,num:int,delay:float=0):
        for i in range(num):
            self.command("*TRG")
            sleep(delay)
    #only tested in hp E4432b, documented in : http://www.doe.carleton.ca/~nagui/labequip/synth/manuals/e4400324.pdf
    def setBinaryData(self,data_csv_filename:str,bitfile_name:str, data_speed:int):
        try:
            bin_df = pd.read_csv(data_csv_filename)
        except FileNotFoundError:
            self.logger.warn("Packet file not found! If using PN stream, ignore")
            return
        # define a lambda function to convert each hex value to a string
        to_hex_string = lambda x: x[2:]
        # apply the lambda function to each value in the 'mosi' column and concatenate them together
        hex_data = ''.join(bin_df['mosi'].apply(to_hex_string))
        length_in_bits = int(len(hex_data)*4)

        # During testing, we dected errors when the sent packet was too short in time
        # Because of this, each packet gets padded out to be about 5 ms long, which should be more than enough
        # We have to add 8 bits at a time, otherwise we get an error
        required_bitnum = int(data_speed/1000) * 5
        while (length_in_bits < required_bitnum):
            hex_data += '00'
            length_in_bits += 8
        self.logger.debug(f"Padded the packet to be {length_in_bits} bits long")

        self.setStreamType("PN9") 
        #format: MEM:DATA:BIT "filename",bit_count, binary data
        command = "MEMory:DATA:BIT " + "\"" + bitfile_name+ "\","+ str(length_in_bits)+","
        self.command(command,binary_format=True,hex_string=hex_data) #@BIT\"
    
    def getSettings(self):
        settings = SigGenSettings()
        settings.frequency_Hz = self.getFrequency()
        settings.amplitude_dBm = self.getAmplitude()
        settings.modulation.type = self.getModulation_type()
        settings.modulation.symbolrate_sps = self.getSymbolrate()
        settings.modulation.deviation_Hz = self.getDeviation()
        settings.stream_type = self.getStreamType()
        settings.filter_type = self.getFilter()
        settings.filter_BbT = self.getFilterBbT()
        return settings
    def setStream(self, settings:SigGenSettings):
        self.setFrequency(settings.frequency_Hz)
        self.setAmplitude(settings.amplitude_dBm)
        self.setModulation_type(settings.modulation.type)
        self.setSymbolrate(settings.modulation.symbolrate_sps)
        self.setBinaryData(settings.per_packet_filename,settings.per_packet_siggen_name,settings.modulation.symbolrate_sps * settings.modulation.bits_per_symbol)
        self.toggleModulation(settings.mod_on)
        self.toggleRFOut(settings.rf_on)
        self.setDeviation(settings.modulation.deviation_Hz)
        self.setStreamType(settings.stream_type)
        self.setPatternRepeat(settings.pattern_repeat)
        self.setFilter(settings.filter_type)
        self.setFilterBbT(settings.filter_BbT)
        self.toggleCustom(settings.custom_on)
        self.setTriggerType(settings.trigger_type)


    def getError(self)->str:
        error = self.instr.query("SYST:ERR?") 
        self.logger.error("SCPI Error: "+str(error))
        return str(error)

class RS_SigGen(GenericSigGen): # written to R & S SBV100A
    def reset(self):
        self.command("*CLS")
        self.command("*RST",write_delay_ms=2000)
    def init(self): # this is to set the generator in a state that we want it to be in, it has a lot of unwanted functionality for this framework
        self.command("BB:DM:CLIST:SEL 'amf_clist'")
        self.command("SOURce:POW:MODE FIX") 
        self.command("BB:DM:PRAM ON")
        self.command("BB:DM:PRAM:SOUR INT") #power ramping settings to turn CW between packetsoff
        self.command("BB:DM:PRAM:SHAP COS")
        self.command("BB:DM:PRAM:TIME 0.25")
        self.command("BB:DM:COD OFF")

    def setFrequency(self, frequency_Hz:int):
        self.command("FREQ " + str(frequency_Hz)+ " Hz")
    def setAmplitude(self, amplitude_dBm:float):
        
        self.command("SOURce:POW:POW " + str(amplitude_dBm))
    def getAmplitude(self):
        amplitude_dBm = self.query_float("SOURce:POW:POW?")
        return amplitude_dBm
    def setFrequencyMode(self,mode:str):
        self.command("FREQ:MODE "+ mode)
    def toggleModulation(self, mod_on:bool):
        if mod_on:
            self.command("BB:DM:STAT " + "ON")
        else:
            self.command("BB:DM:STAT " + "OFF")
    def setModulation_type(self, type:str):
        self.command("BB:DM:FORM " + str(type) )
    def getModulation_type(self):
        type = self.query("BB:DM:FORM?")
        return type
    def setSymbolrate(self, symbolrate_sps:int):
        self.command("BB:DM:SRATE " + str(symbolrate_sps))
    def getSymbolrate(self):
        symbolrate_sps = self.query_float("BB:DM:SRATE?")
        return symbolrate_sps
    def setDeviation(self, deviation_Hz:int):
        self.command("BB:DM:FSK:DEViation " + str(deviation_Hz))
    def getDeviation(self):
        deviation_Hz = self.query_float("BB:DM:FSK:DEViation?")
        return deviation_Hz
    def setBinaryData(self,data_csv_filename:str,bitfile_name:str):
        try:
            bin_df = pd.read_csv(data_csv_filename)
        except FileNotFoundError:
            self.logger.warn("Packet file not found! If using PN stream, ignore")
            return
        # define a lambda function to convert each hex value to a string
        to_hex_string = lambda x: x[2:]
        # apply the lambda function to each value in the 'mosi' column and concatenate them together
        hex_data = ''.join(bin_df['mosi'].apply(to_hex_string))
        length_in_bits = int(len(hex_data)*4)
        #format: MEM:DATA:BIT "filename",bit_count, binary data
        command = ":BB:DM:DLISt:DATA "
        self.command(command,binary_format=True,hex_string=hex_data) #@BIT\"
        
        #print(self.query_float("BB:DM:CLIST:POIN?"))

    def setStreamType(self, stream_type:str): #PN9 PN11 PN15 PN16 PN20 PN21 PN23 or 'FILENAME@BIT'
        stream_type = stream_type.upper()

        if  "PN" in stream_type:
            self.command("BB:DM:SOUR PRBS")
            self.command("BB:DM:PRBS " + stream_type.replace("PN",'')) #remove PN
        elif "@BIT" in stream_type: #to be compatible with the HP generator format
            self.command("BB:DM:SOUR DLISt")
            stream_type = stream_type.replace("@BIT",'')
            stream_type = stream_type.replace("\"",'')
            self.command("BB:DM:DLIST:SEL '"+stream_type+"'")
            self.command("BB:DM:CLIST:SEL 'amf_clist'") #control list is a must in this gen
            #self.setBinaryData()
        errors = self.getError()
        # if errors.find("Illegal")>0:
        #     self.logger.error("If file stream was added, you probably forgot the \"\"")
    def getStreamType(self):
        stream_type = self.query("BB:DM:SOUR?")
        return stream_type
    def setPatternRepeat(self,repeat_type:str): # AUTO | RETRigger | AAUTo | ARETrigger | SINGle
        if repeat_type == "CONT":
            self.command("BB:DM:SEQ AUTO")
        else:
            self.command("BB:DM:SEQ " + repeat_type)

    def setTriggerType(self,trigger_type:str):
        if trigger_type=="EXT":
            self.command("BB:DM:TRIGger:SOURce EXT")
        else:
            self.command("BB:DM:TRIGger:SOURce INT")
    def sendTrigger(self,num:int,delay:float=0):
        for i in range(num):
            self.command("BB:DM:TRIG:EXEC")
            sleep(delay)
    def setFilter(self,filter_type:str): # RCOSine | COSine | GAUSs | LGAuss | CONE  etc.... check manual
        self.command("BB:DM:FILTer:TYPE "+ filter_type)
    def getFilter(self):
        filter_type = self.query("BB:DM:FILTer:TYPE?")
        return filter_type 
    def setFilterBbT(self, filter_BbT:float):
        self.command("DM:FILT:PAR " + str(filter_BbT))
    def getFilterBbT(self):
        filter_BbT = self.query_float("DM:FILT:PAR?")
        return filter_BbT
    def setPacketLength(self,data_csv_filename:str,bits_per_symbol:int=1): # Rohde specific function, sets packet lenght dependent siggen parameters
        try:
            bin_df = pd.read_csv(data_csv_filename)
        except FileNotFoundError:
            self.logger.warn("Packet file not found! If using PN stream, ignore")
            return
        # define a lambda function to convert each hex value to a string
        to_hex_string = lambda x: x[2:]
        # apply the lambda function to each value in the 'mosi' column and concatenate them together
        hex_data = ''.join(bin_df['mosi'].apply(to_hex_string))
        length_in_bits = int(len(hex_data)*4)

        data_list = "16" # only the burst line has to be high, whose values is 16

        symbols_packet_length = int(length_in_bits/bits_per_symbol) #in symbols

        for i in range(symbols_packet_length-1):
            data_list+=",16" # send 'packet_length' number of '16's
        self.command("BB:DM:CLIST:DATA "+ data_list)
        self.command("BB:DM:TRIG:SLEN " + str(symbols_packet_length))
    def toggleCustom(self,on_off:bool):
        pass
    def setStream(self, settings:SigGenSettings):
        self.init()
        self.setFrequency(settings.frequency_Hz)
        self.setAmplitude(settings.amplitude_dBm)
        self.setModulation_type(settings.modulation.type)
        self.setDeviation(settings.modulation.deviation_Hz)
        self.setSymbolrate(settings.modulation.symbolrate_sps)
        self.setStreamType(settings.stream_type)
        self.setBinaryData(settings.per_packet_filename,settings.per_packet_siggen_name)
        self.setPacketLength(settings.per_packet_filename,settings.modulation.bits_per_symbol)
        self.toggleModulation(settings.mod_on)
        self.toggleRFOut(settings.rf_on)
        self.setPatternRepeat(settings.pattern_repeat)
        self.setTriggerType(settings.trigger_type)
        self.setFilter(settings.filter_type)
        self.setFilterBbT(settings.filter_BbT)
        self.toggleCustom(settings.custom_on)
    pass


# Tested with Anritsu MS2692A 
# This class only implements CW generator functionality (intended for blocking tests)
class AnritsuSigGen(GenericSigGen):

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

    def reset(self):
        self.command("*RST",write_delay_ms=2000)

    def init(self):
        self.logger.warn("You are initializing a CW generator, all modulation settings are ignored.")
        self.setAppSwitch("SG")

    def setFrequency(self, frequency_Hz:int):
        self.command("FREQ " + str(frequency_Hz))
    def getFrequency(self):
        return self.instr.query_ascii_values("FREQ?")

    def setAmplitude(self, amplitude_dBm: float):
        self.command("POW " + str(amplitude_dBm) + "DBM")
    def getAmplitude(self):
        return self.instr.query_ascii_values("POW?")
    
    def toggleRFOut(self, rf_on:bool):
        if rf_on:
            command_str = "OUTP ON"
        else:
            command_str = "OUTP OFF"
        self.command(command_str)
    
    def getError(self)->str:
        error = self.instr.query("SYST:ERR?") 
        self.logger.error("SCPI Error: "+str(error))
        return str(error)
    

    def setStream(self, settings:SigGenSettings):
        self.init()
        self.setFrequency(settings.frequency_Hz)
        self.setAmplitude(settings.amplitude_dBm)
        self.toggleRFOut(settings.rf_on)

    # Only needed for compatiblity 
    def toggleModulation(self, mod_on:bool):
        pass

    def reset(self):
        self.command("*CLS")
        self.command("*RST",write_delay_ms=2000)

    pass