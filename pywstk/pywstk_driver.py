import serial
from copy import deepcopy
from dataclasses import dataclass
from pyparsing import nestedExpr
import time
from common import Logger, Level

class RAILError(Exception):
    def __init__(self, errorCode:str, errorMessage:str):
        self.message = 'RAILError - errorCode: '+errorCode+', errorMessage: '+errorMessage
        super().__init__(self.message)

@dataclass
class RAILTest_response:
    response_type:str
    response_content:dict

class WSTK_RAILTest_Driver:
    def __init__(self, COMport:str, baudRate:int=115200, format:str="8N1", timeout_ms:int=1000,logger_settings :Logger.Settings = Logger.Settings()):  # typically 115200, 8N1
        self.port = serial.Serial()
        self._read_buffer = ''  # internal buffer to avoid some problems caused by RAILTest dumps
        self.port.port = COMport
        self.port.baudrate = baudRate
        bits = int(format[0])
        parity = format[1]
        stop_bits = int(format[2])

        if logger_settings.module_name is None:
            logger_settings.module_name = __name__

        if logger_settings.logfile_name is not None:
            logger_settings.logfile_name +="_driver"
        self.logger = Logger(logger_settings)
        if bits==8:
            self.port.bytesize == serial.EIGHTBITS
        else:
            raise ValueError("Wrong UART data format: only 8 bit long data is supported")
        if parity.upper()=='N':
            self.port.parity = serial.PARITY_NONE
        else:
            raise ValueError("Wrong UART data format: parity setting must be 'None'")
        if stop_bits==1:
            self.stop_bits = 1
        else:
            raise ValueError("Wrong UART data format: only 1 stop bit is supported")
        self.port.timeout = timeout_ms/1000
        self.port.open()
        self.flushIO()
        self.reset()
        self.setTxTransitions('idle','idle') #setting after tx transitions to idle(not rx)
    def __del__(self):
        self.port.close()
    def _write(self, data:str):
        self.port.write((data+'\n').encode("utf-8"))
    def _read(self, termination_char:str|None='>', timeout_ms:int=1000):  # this is the real deal: '>' can be probably used as termination character
        keep_reading = True
        start = time.time_ns()
        timeout = False
        while keep_reading:
            r = self.port.read(self.port.in_waiting)
            self._read_buffer += r.decode('latin-1')  # store in internal buffer
            timeout = (time.time_ns()-start)/1e6 > timeout_ms
            if termination_char==None:
                keep_reading = not timeout
            else:
                keep_reading = not((termination_char in self._read_buffer) or timeout)
        if termination_char==None:
            return_buffer = deepcopy(self._read_buffer)  # return the full content of the internal buffer
            self._read_buffer = ''  # reset internal buffer
        else:
            return_buffer = self._read_buffer[:self._read_buffer.find(termination_char)+1]  # return up to the termination char
            self._read_buffer = self._read_buffer[self._read_buffer.find(termination_char)+1:]  # clear the returned part from the buffer


        return_buffer_log=''.join(return_buffer.splitlines()) #remowing newlines for clean logging
        return_buffer_log = return_buffer_log.replace('\0','',-1) # removing unwanted null characters
        self.logger.debug(return_buffer_log+ "\n")

        if timeout and termination_char!=None:
            raise TimeoutError('pywstk_driver._read Timeout')
        return return_buffer
    def _command(self, cmd:str, timeout_ms:int=1000, wait_time_s:float = 0.0):
        self._write(cmd)
        time.sleep(wait_time_s)
        response = self._read(timeout_ms=timeout_ms)
        return response
    def flushIO(self):
        self.port.flushInput()
        self.port.flushOutput()
    def close(self):
        self.port.close()
    @staticmethod
    def parseResponse(response:str)->list[RAILTest_response]:
        nested_list_str = response[response.find('{'):response.rfind('}')+1]  # extract everything between first {}
        opened = 0
        beginning_end = []
        for k,c in enumerate(nested_list_str):  # find {} sections
            if c=='{':
                if opened==0:
                    b = k
                opened+=1
            elif c=='}':
                if opened==1:
                    e = k
                    beginning_end.append((b,e))
                opened-=1
        parser = nestedExpr(opener='{', closer='}')  # create parser to parse further the nested {} blocks
        responses = []
        for b,e in beginning_end:  # iterate over {} sections
            r = nested_list_str[b:e+1]
            nested_list = parser.parseString(r).asList()  # parse the nested {} blocks
            response_type = nested_list[0][0][0]
            response_content = {}
            for item in nested_list[0][1:]:
                content = ' '.join(item).split(':')
                response_content[str(content[0])] = str(content[1])
            responses.append(RAILTest_response(response_type=response_type, response_content=response_content))
        return responses
    @staticmethod
    def handleRAILerror(response:str, expected:str):
        try:
            responses = WSTK_RAILTest_Driver.parseResponse(response)
            response_found=False
            error_found = None
            response_types = ""
            if len(responses):
                for r in responses:
                    response_types+=r.response_type
                    if r.response_type ==  "("+expected+")":  # look for the expected response
                        response_found=True
                    if 'error' in r.response_content.keys():  # check if any error occured during executing the RAIL command
                        error_found = r.response_content['error']
                    if r.response_type ==  "(assert)":  # look for assert
                        error_found ="Assert: "+ r.response_content['message']

                if error_found:
                    raise ValueError(error_found)
                if not response_found:  # raise error if RAIL response does not correspond to the right command
                    error_str = "Wrong response: must start with ("+expected+")"+", got "+response_types + " instead!"
                    raise ValueError(error_str)
            else:
                error_str = "No responses found: "+response
                raise ValueError(error_str)
            return responses  # this is to avoid parsing 2 times
        except:
            print(response)  # this is just to output the response that caused the error
            raise  # raising error further
    def driverCall(driver_function)->str:  # generic driver call method to wrap specific calls and do error checking/handling
        def wrapper(self, *args, **kwargs):
            # execute the input function that contains the specific driver call
            # must return the driver command's name and the response in orther to be able to check for errors
            command, response = driver_function(self, *args, **kwargs)
            # parse responses and check for errors, this is to avoid parsing 2 times
            responses = WSTK_RAILTest_Driver.handleRAILerror(response=response, expected=command)
            # can be extended further with other functionalities, if needed
            return responses  # return the entire response for further processing in higher layers
        return wrapper  # will be decorated later
    # *************************************************************************************************
    # Driver calls: methods that perform single calls to the driver ***********************************
    # It is recommended to name the method identical to the driver method
    @driverCall
    def reset(self)->str:
        response = self._command('reset',timeout_ms=10000, wait_time_s=0.5)
        return 'reset', response
    @driverCall
    def status(self)->str:
        status_message = self._command('status')  # query status
        return 'status', status_message
    @driverCall
    def setDebugMode(self, on_off:bool)->str:
        if on_off:
            debug_mode = '1'
        else:
            debug_mode = '0'
        response = self._command('setDebugMode '+debug_mode)
        return 'setDebugMode', response
    @driverCall
    def freqOverride(self, frequency_Hz:float)->str:
        frequency = int(round(frequency_Hz))
        response = self._command('freqOverride '+str(frequency))
        return 'freqOverride', response
    @driverCall
    def setPower(self, value:float, format:str='')->str:
        if format.upper()=='' or format.upper()=='DBM':
            v = str(int(value*10))
        elif format.upper()=='RAW':
            v = str(int(value)) + ' raw'
        else:
            raise ValueError("setTxpower: unknown format specifier. Format must be 'dBm', 'raw' or left empty")
        response = self._command('setPower '+v)
        return 'setPower', response
    @driverCall
    def setTxTone(self, on_off:bool, mode:str, antenna:int=0)->str:
        if on_off:
            enable = '1'
        else:
            enable = '0'
        if mode.upper()=='CW':
            tone_mode = 0
        elif mode.upper()=='PHASENOISE':
            tone_mode = 1
        else:
            raise ValueError('setTxTone: unknown tx mode')
        response = self._command('setTxTone ' +str(enable)+' '+str(antenna)+' '+str(tone_mode))
        return 'setTxTone', response
    @driverCall
    def tx(self, npackets:int)->str:
        response = self._command('tx '+str(npackets),)
        return 'tx', response
    @driverCall
    def setTxStream(self, on_off:bool, mode:str, antenna:int)->str:
        if on_off:
            enable = 1
        else:
            enable = 0
        if mode.upper()=='PN9':
            stream_mode = 1
        elif mode.upper()=='ALTERNATING':
            stream_mode = 2
        elif mode.upper()=='PHASENOISE':
            stream_mode = 3
        elif mode.upper()=='CW':
            stream_mode = 0
        else:
            raise ValueError('setTxStream: unknown tx stream mode')
        response = self._command('setTxStream '+str(enable)+' '+str(stream_mode)+' '+str(antenna))
        return 'setTxStream', response
    @driverCall
    def setTxLength(self, length:int)->str:
        response = self._command('setTxLength '+str(length))
        return 'setTxLength', response
    @driverCall
    def setTxPayload(self, data:bytes, offset:int=0)->str:
        data_bytes_str = ' '.join([str(int(x)) for x in data])
        response = self._command('setTxPayload '+str(offset)+' '+data_bytes_str)
        return 'setTxPayload', response
    @driverCall
    def printTxPacket(self):
        response = self._command('printTxPacket')
        return 'printTxPacket', response
    @driverCall
    def rx(self, on_off:bool)->str:
        if on_off:
            receive_mode = 1
        else:
            receive_mode = 0
        response = self._command('rx '+str(receive_mode),)  # rx takes some time to execute
        return 'rx', response
    @driverCall
    def getRssi(self)->str:
        response = self._command('getRssi')
        return 'getRssi', response
    @driverCall    
    def berRx(self, on_off:bool)->str:
        if on_off:
            receive_mode = 1
        else:
            receive_mode = 0
        response = self._command('berRx '+str(receive_mode))
        return 'berRx', response
    @driverCall    
    def setBerConfig(self, nbytes:int)->str:
        response = self._command('setBerConfig '+str(nbytes))
        return 'setBerConfig', response
    @driverCall    
    def berStatus(self)->str:
        response = self._command('berStatus')
        return 'berStatus', response
    # ******************************************************
    # Application Configuration commands *******************
    @driverCall
    def resetCounters(self)->str:
        response = self._command('resetCounters')
        return 'resetCounters', response
    @driverCall
    def getVersion(self)->str:
        response = self._command('getVersion')
        return 'getVersion', response
    @driverCall
    def getVersionVerbose(self)->str:
        response = self._command('getVersionVerbose')
        return 'getVersionVerbose', response
    # ... TBD
    # *******************************************************
    # Receive and Trasmit ***********************************
    @driverCall
    def setTxTransition(self, txSucess:str, txError:str)->str:
        response = self._command('setTxTransitions '+txSucess+' '+txError)
        return 'setTxTransition', response
    @driverCall
    def getTxTransitions(self)->str:
        response = self._command('getTxTranstitions')
        return 'getTxTransitions', response
    @driverCall
    def getPower(self)->str:
        response = self._command('getPower')
        return 'getPower', response
    @driverCall
    def getPowerConfig(self)->str:
        response = self._command('getPowerConfig')
        return 'getPowerConfig', response
    @driverCall
    def setPowerConfig(self, paMode:str|int, milliVolts:int, rampTime_us:int):
        response = self._command('setPowerConfig '+str(paMode)+' '+str(milliVolts)+' '+str(rampTime_us))
        return 'setPowerConfig', response
    @driverCall
    def startAvgRssi(self, averageTime_us:int=1000, channel:int=-1)->str:
        if channel<0:
            response = self._command('startAvgRssi '+str(averageTime_us))
        else:
            response = self._command('startAvgRssi '+str(averageTime_us)+' '+str(channel))
        return 'startAvgRssi', response
    @driverCall
    def getAvgRssi(self):
        response = self._command('getAvgRssi')
        return 'getAvgRssi', response
    @driverCall
    def fifoReset(self, rx:int, tx:int):
        response = self._command('fifoReset '+str(tx)+' '+str(rx),)
        return 'fifoReset', response
    # ******************************************************
    # Diagnostic and test commands *************************
    @driverCall
    def getCtune(self)->str:
        response = self._command('getCtune')
        return 'getCtune', response
    @driverCall    
    def setCtune(self, value:int)->str:
        response = self._command('setCtune '+str(value))
        return 'setCtune', response
    @driverCall    
    def setTxTransitions(self, tx_success:str, tx_error:str)->str:
        response = self._command('setTxTransitions '+tx_success+' '+tx_error)
        return 'setTxTransitions', response
    @driverCall
    def getSetFemProtectionConfig(self, packet_duty_cycle: int = 0, stream_power_dbm: float = 0)->str:
        response = self._command('getSetFemProtectionConfig '+str(packet_duty_cycle)+' '+str(int(stream_power_dbm*10)))
        return 'getSetFemProtectionConfig', response
    @driverCall
    def setconfigindex(self, configId: int = 0)->str:
        response = self._command('setconfigindex '+str(configId))
        return 'setconfigindex', response
    @driverCall
    def set802154phr(self, phr_format: int, opt1: int, opt2: int=0)->str:
        """
        Set PHR (first 1, 2 or 4 bytes) in Tx buffer according to the 'format' input parameter.
        PHR 'frameLength' field is derived from TxLength set previously with 'setTxLength'
        For PHR fields info, refer to 802.15.4 specification.
        :param phr_format:
            0=misc IEEE802154 modulations, PHR 1byte
            1=SUN FSK, PHR 2bytes
            2=SUN OFDM, PHR 4bytes
            3=SUN OQPSK, PHR 4bytes
        :param opt1:
            For SUN_OFDM : rate
            For SUN_OQPSK: spreadingMode
            For SUN_FSK  : fcsTtype
            For LEG_OQPSK: none
        :param opt2:
            For SUN_OFDM : scrambler
            For SUN_OQPSK: rateMode
            For SUN_FSK  : whitening
            For LEG_OQPSK: none
        :return:
        """
        response = self._command('set802154phr '+str(phr_format)+" "+str(opt1)+" "+str(opt2))
        return 'set802154phr', response
    @driverCall
    def setPeripheralEnable(self, on_off:bool)->str:
        if on_off:
            peripheral_enable = 1
        else:
            peripheral_enable = 0
        response = self._command('setPeripheralEnable '+str(peripheral_enable))
        return 'setPeripheralEnable', response
    @driverCall
    def setTxDelay(self, tx_delay_ms:int)->str:
        response = self._command('setTxDelay '+str(tx_delay_ms))
        return 'setTxDelay', response
    @driverCall
    def setChannel(self, value:int)->str:
        response = self._command('setChannel '+str(value))
        return 'setChannel', response