import pyvisa
import warnings
import numpy as np
from dataclasses import dataclass
from time import sleep
from common import Logger, Level
@dataclass
class PSUSettings:
    limit_A:float = 3
    limit_V:float = 0
    mode:str='constant_voltage'
    output_1:bool =False 
    output_2:bool =False

    def __str__(self):
        return str(self.limit_V) +'V' +'/'+ str(self.limit_A)+'A '+'\nmode: '+ str(self.mode)+' '+'\noutput 1: '+str(self.output_1)+ ' output 2: '+str(self.output_2)
    

# PSU is a factory class that returns the right sub-classed instrument based on the response to the *IDN? query
# Tries to indetify the instrument and use the appropriate sub-class
# If the device cannot be indetified use the generic instrument
class PSU(object):
    def __new__(cls, resource:str, default_timeout_ms:int=1000, auto_detect:bool=True, logger_settings :Logger.Settings = Logger.Settings()):
        if auto_detect:
            # open a VISA session, query instrument and try to identify it
            _rm = pyvisa.ResourceManager()
            _instr = _rm.open_resource(resource_name=resource)
            idn_query_response = _instr.query("*IDN?")
            if logger_settings.module_name is None:
                logger_settings.module_name = __name__
            # Instrument session won't be used here anymore, close it
            # Resource Manager shouldn't be closed, because it is a singleton object
            _instr.close()
            # instantiate the right sub-class if the instrument is properly identified
            if "Agilent" in idn_query_response:
                return GenericPSU(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)
            else:
                warnings.warn("No specific power supply type identified, using generic instrument.")
                return GenericPSU(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)
        else:
            return GenericPSU(resource_name=resource, default_timeout_ms=default_timeout_ms,logger_settings=logger_settings)

# Generic Power Supply class
# Contains some default implementation of the various functions that might not work for all power supplies
# This class was developed based on Agilent E3646A
class GenericPSU(object):
    def __init__(self, resource_name:str, default_timeout_ms:int=1000,logger_settings :Logger.Settings = Logger.Settings()):
        try:
            self._rm = pyvisa.ResourceManager()
            self.instr = self._rm.open_resource(resource_name=resource_name)
            self.instr.timeout = default_timeout_ms
            self.instr.opc_timeout = 3000
            self.instr.visa_timeout = 3000
            self.instr.read_termination = '\n'
            self.instr.query_delay=0.2
            self.default_timeout_ms = default_timeout_ms
            self.settings = PSUSettings()
            self.logger = Logger(logger_settings)
            
        except:
            self.instr = None
            raise
    def __del__(self):
        try:
            self.toggleOutput(False)
            self.instr.close()
            self._rm.close()
        except pyvisa.errors.InvalidSession as error:
            self.logger.warn("Session already closed at destructor, possibly by other instrument")
    def command(self, command_str, query_opc:bool=True, write_delay_ms:float=0.5):
        self.instr.write(command_str)
        self.logger.debug("SCPI Write: " + command_str)
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
    def setVoltage(self, voltage_V:float):
        self.command("VOLT " + str(voltage_V))
        self.settings.limit_V = voltage_V
    def setCurrent(self, current_A:float):
        self.command("CURR " + str(current_A))
        self.settings.limit_A = current_A
    def getVoltage(self):
        voltage = self.query_float("VOLT?")
        return voltage
    def getCurrent(self):
        current = self.query_float("CURR?")
        return current
    def measCurrent(self):
        meas_current = self.query_float("MEAS:CURR?")
        return meas_current
    def selectOutput(self, output:int=1):
        if output == 1 or output == 2:
            self.command("INST:SEL OUT" + str(output))
            if output == 1:
                self.settings.output_1 = True
            if output == 2:
                self.settings.output_2 = True
        else: 
            self.logger.error("Wrong output is selected!")
    def toggleOutput(self, on_off:bool=True):
        if on_off:
            self.command("OUTP ON")
        else:
            self.command("OUTP OFF")
    def getSettings(self,settings:PSUSettings):
        pass
    def geterror(self):
        error = self.instr.query("SYST:ERR?") 
        sleep(0.5)
        self.logger.error(error)

            



 



