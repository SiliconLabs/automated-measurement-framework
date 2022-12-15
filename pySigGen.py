import pyvisa
import warnings
import numpy as np
from dataclasses import dataclass
from time import sleep

@dataclass
class ModulationConfig:
    type:str = "FSK2"
    symbolrate_sps:int = 100000
    deviation_Hz:int = 50000

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
    filter_type:str = "Gaussian"
    filter_BbT:float = 0.5
    custom_on:bool =False

    def __str__(self):
        return str(self.frequency_Hz/1e6) + ' MHz' + '\n' + str(self.amplitude_dBm) +' dBm' + '\nmodulation: ' + str(self.modulation) + ' ' +  '\nMOD on: '+ str(self.mod_on) + '\nRF On: ' + str(self.rf_on) + '\nStream: ' + str(self.stream_type) + '\nFilter: ' + str(self.filter_type) + '\nFilter_BbT: ' + str(self.filter_BbT) + '\nCustom On: ' + str(self.custom_on)
    

# SigGen is a factory class that returns the right sub-classed instrument based on the response to the *IDN? query
# Tries to identify the instrument and use the appropriate sub-class
# If the device cannot be identified use the generic instrument
class SigGen(object):
    def __new__(cls, resource:str, default_timeout_ms:int=1000, auto_detect:bool=True):
        if auto_detect:
            # open a VISA session, query instrument and try to identify it
            _rm = pyvisa.ResourceManager()
            _instr = _rm.open_resource(resource_name=resource)
            idn_query_response = _instr.query("*IDN?")
            # VISA session won't be used here anymore, close it
            _instr.close()
            _rm.close()
            # instantiate the right sub-class if the instrument is properly identified
            if "Hewlett" in idn_query_response:
                return GenericSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms)
            else:
                warnings.warn("No specific power supply type identified, using generic instrument.")
                return GenericSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms)
        else:
            return GenericSigGen(resource_name=resource, default_timeout_ms=default_timeout_ms)

# Generic Power Supply class
# Contains some default implementation of the various functions that might not work for all power supplies
# This class was developed based on Agilent E3646A
class GenericSigGen(object):
    def __init__(self, resource_name:str, default_timeout_ms:int=1000):
        try:
            self._rm = pyvisa.ResourceManager()
            self.instr = self._rm.open_resource(resource_name=resource_name)
            self.instr.timeout = default_timeout_ms
            self.instr.opc_timeout = 3000
            self.instr.visa_timeout = 3000
            self.instr.read_termination = '\n'
            #self.instr.query_delay=0.2
            self.default_timeout_ms = default_timeout_ms
        except:
            self.instr = None
            raise
    def __del__(self):
        self.instr.close()
        self._rm.close()
    def command(self, command_str, query_opc:bool=True, write_delay_ms:float=0):
        self.instr.write(command_str)
        sleep(write_delay_ms) # this delay is necessary to give time for an older instrument to process the write
        if query_opc:
            opc = self.instr.query_ascii_values("*OPC?")[0]
            if opc == 0:
                raise Exception("OPC violation")
    def query_float(self, command_str, timeout_ms:int=0):
        r = self.instr.query_ascii_values(command_str)
        if len(r)==1:
            return float(r[0])
        else:
            return [float(x) for x in r]
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
        if str(filter_type) == "Gaussian":
            self.command("RADio:CUSTom:FILTer GAUSsian") 
        elif str(filter_type) == "Nyquist":
            self.command("RADio:CUSTom:FILTer RNYQuist") 
        else:
            raise ValueError("Wrong Filter type issued!") 
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
    # def updateDisplay(self):
    #     self.command("DISPlay:REMote " + "ON")
    def setStreamType(self, stream_type:str):
        self.command("RADio:CUSTom:DATA " + str(stream_type))
    def getStreamType(self):
        stream_type = self.query_float("RADio:CUSTom:DATA?")
        return stream_type  
    
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
        self.toggleModulation(settings.mod_on)
        self.toggleRFOut(settings.rf_on)
        self.setStreamType(settings.stream_type)
        self.setFilter(settings.filter_type)
        self.setFilterBbT(settings.filter_BbT)
        self.toggleCustom(settings.custom_on)

    def getError(self):
        error = self.instr.query("SYST:ERR?") 
        print(error)
#Agielnt PSU class, overwrites and new functions for Agilent specific SCPI
class AnritsuSigGen(GenericSigGen):
    pass
    # def __init__(self, resource_name:str, default_timeout_ms:int=1000):
    #     try:
    #         self._rm = pyvisa.ResourceManager()
    #         self.instr = self._rm.open_resource(resource_name=resource_name)
    #         self.instr.timeout = default_timeout_ms
    #         self.instr.opc_timeout = 3000
    #         self.instr.visa_timeout = 3000
    #         self.instr.read_termination = '\n'
    #         #self.instr.query_delay=0.2
    #         self.default_timeout_ms = default_timeout_ms
    #     except:
    #         self.instr = None
    #         raise
    # def __del__(self):
    #     self.instr.close()
    #     self._rm.close()
    # def command(self, command_str, query_opc:bool=True, write_delay_ms:float=0.5):
    #     self.instr.write(command_str)
    #     #sleep(write_delay_ms) # this delay is necessary to give time for an older instrument to process the write
    #     if query_opc:
    #         opc = self.instr.query_ascii_values("*OPC?")[0]
    #         if opc == 0:
    #             raise Exception("OPC violation")
    # def query_float(self, command_str, timeout_ms:int=0):
    #     r = self.instr.query_ascii_values(command_str)
    #     if len(r)==1:
    #         return float(r[0])
    #     else:
    #         return [float(x) for x in r]
    
            



 



