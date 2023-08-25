from dataclasses import dataclass, fields
from pyparsing import nestedExpr
from .pywstk_driver import WSTK_RAILTest_Driver, RAILError
from multiprocessing import Queue
import time
from common import Logger, Level



@dataclass
class RAILTest_status:
    UserTxCount:int=0
    AckTxCount:int=0
    UserTxAborted:int=0
    AckTxAborted:int=0
    UserTxBlocked:int=0
    AckTxBlocked:int=0
    UserTxUnderflow:int=0
    AckTxUnderflow:int=0
    RxCount:int=0
    RxCrcErrDrop:int=0
    SyncDetect:int=0
    NoRxBuffer:int=0
    TxRemainErrs:int=0
    RfSensed:int=0
    ackTimeout:int=0
    ackTxFpSet:int=0
    ackTxFpFail:int=0
    ackTxFpAddrFail:int=0
    RfState:str=''
    RAIL_state_active:int=0
    RAIL_state_rx:int=0
    RAIL_state_tx:int=0
    Channel:int=0
    AppMode:str=''
    TimingLost:int=0
    TimingDetect:int=0
    FrameErrors:int=0
    RxFifoFull:int=0
    RxOverflow:int=0
    AddrFilt:int=0
    Aborted:int=0
    RxBeams:int=0
    DataRequests:int=0
    Calibrations:int=0
    TxChannelBusy:int=0
    TxClear:int=0
    TxCca:int=0
    TxRetry:int=0
    UserTxStarted:int=0
    PaProtect:int=0
    SubPhy0:int=0
    SubPhy1:int=0
    SubPhy2:int=0
    SubPhy3:int=0
    rxRawSourceBytes:str=''
    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, field.type):
                setattr(self, field.name, field.type(value))


@dataclass
class RAILTest_info:
    radio={}
    system={}
    pti={}
    reset={}
    def __init__(self, info_message):
        responses = WSTK_RAILTest_Driver.parseResponse(info_message)
        for r in responses:
            if r.response_type=='(radio)':
                self.radio['XTAL'] = float(r.response_content['FreqHz'])
                self.radio['ModuleInfo'] = str(r.response_content['ModuleInfo'])
                self.radio['ModuleName'] = str(r.response_content['ModuleName'])
            elif r.response_type=='(system)':
                self.system['Family'] = str(r.response_content['Family'])
                self.system['Fam#'] = int(r.response_content['Fam#'])
                self.system['ChipRev'] = str(r.response_content['ChipRev'])
                self.system['sdid'] = int(r.response_content['sdid'])
                self.system['Part'] = str(r.response_content['Part'])
            elif r.response_type=='(pti)':
                self.pti['mode'] = str(r.response_content['mode'])
                self.pti['baud'] = int(r.response_content['baud'])
                self.pti['protocol'] = int(r.response_content['protocol'])
                self.pti['radioConfig'] = str(r.response_content['radioConfig'])
            elif r.response_type=='(reset)':
                self.reset['App'] = str(r.response_content['App'])
                self.reset['Built'] = str(r.response_content['Built'])
            else:
                raise RAILError('parseResponse: unknown response type',r.response_type)

@dataclass
class PA_Config:
    paMode:str|int  # As per STUDIO_SDK_LOC\platform\radio\rail_lib\chip\efr32\efr32xg2x\rail_chip_specific.h
    milliVolts:int
    rampTime_us:int


class WSTK_RAILTest:
    def __init__(self, COMport:str, reset:bool=False,logger_settings:Logger.Settings = Logger.Settings()):
        self._driver = None  # initialize _driver attribute so if something goes wrong later, it still extists
        self._driver = WSTK_RAILTest_Driver(COMport=COMport,logger_settings = logger_settings.copy())  # initialize driver
        if reset:
            self._driver.reset()
        self._driver.rx(on_off=False)  # turn RX off, just in case. won't mess up anything even it is already off
        self._driver.flushIO()  # clear buffers. some remaining content can cause trouble later
        self._status = self.getStatus()
        self.PACKETLENGHT_NBYTES:int = 16
        self.txbuffer_npackets:int = 0
        self.receiveQ:Queue = None

        if logger_settings.module_name is None:
            logger_settings.module_name = __name__

        self.logger = Logger(logger_settings)
    def close(self):
        if self._driver!=None:
            self.stop()
            self._driver.close()
    # **************************************************************************************************
    # Higher level methods, wrapping/using multiple driver calls ***************************************
    def resetDevice(self)->RAILTest_info:
        response = self._driver.reset()
        #return RAILTest_info(info_message=response)
    def getStatus(self)->RAILTest_status:
        response = self._driver.status()
        return RAILTest_status(**response[0].response_content)
    def setTransmitData(self, data:bytes):
        nbytes = len(data)  # length of input data
        if nbytes%self.PACKETLENGHT_NBYTES:
            roundup_nbytes = (nbytes//self.PACKETLENGHT_NBYTES+1)*16  # data can only be set in 16-byte chunks
        else:
            roundup_nbytes = nbytes
        padding = roundup_nbytes - nbytes  # this many padding will be needed
        data_to_send = data + bytes([0 for _ in range(0, padding)] ) # padding with 0's
        self._driver.setTxLength(length=len(data_to_send))
        self.txbuffer_npackets = len(data_to_send)//self.PACKETLENGHT_NBYTES
        for k in range(0, len(data_to_send)//self.PACKETLENGHT_NBYTES):  # download data to unit in 16-byte chunks
            self._driver.setTxPayload(data=data_to_send[k*self.PACKETLENGHT_NBYTES:(k+1)*self.PACKETLENGHT_NBYTES], offset=k*self.PACKETLENGHT_NBYTES)

    def transmit(self, mode:str, frequency_Hz:float, power_dBm:float, power_format:str = "DBM", pa_config:PA_Config=None, tx_delay_ms:int=None):
        self.stop()
        self._driver.setDebugMode(on_off=True)
        self._driver.freqOverride(frequency_Hz=frequency_Hz)
        if pa_config is not None:
            self._driver.setPowerConfig(**pa_config.__dict__)
        self._driver.setPower(power_dBm, format=power_format)
        self.logger.info("Starting TX " + mode + " at "+str(frequency_Hz/1e6)+" MHz " + str(power_dBm)+ power_format+"\n")

        if mode.upper() == 'CW':
            self._driver.setTxTone(on_off=True, mode='cw')
        elif mode.upper() == 'PN9':
            if self.is_using_ofdm_pa() and len(self.getTxPacket()) != 4:
                raise RuntimeError("If OFDM is used, packet length must be 4 (and the PHR should be also updated)!")
            self._driver.setTxStream(on_off=True, mode='PN9', antenna=0)
        elif mode.upper() == 'CONTINUOUSTX':
            if tx_delay_ms is not None:
                self._driver.setTxDelay(tx_delay_ms)
            self._driver.tx(0)
        else:
            raise ValueError('unknown TX mode: ', mode)
    def sendPacketInBuffer(self, timeout_ms:int=2000):
        self._driver.tx(npackets=self.txbuffer_npackets)  # start transmitting
        start = time.time_ns()
        timeout = False
        keep_reading = True
        txEnd_ok = False
        read_buffer = ''
        while keep_reading:
            r = self._driver._read(termination_char=None, timeout_ms=100).replace('>', '')  # remove '>' chars
            read_buffer += r
            responses = WSTK_RAILTest_Driver.parseResponse(read_buffer)   # check if read_buffer has the right content with 'txEnd'
            for r in responses:
                if r.response_type.upper()=="(TXEND)" and r.response_content['txStatus']=='Complete':
                    txEnd_ok = True  # TX was successfull
            timeout = (time.time_ns()-start)/1e6 > timeout_ms
            keep_reading = not (timeout or txEnd_ok) 
        if timeout:
            raise TimeoutError("pyRAIL.transmitData Timeout")
        return
    def transmitData(self, data:bytes, frequency_Hz:float, power_dBm:float, timeout_ms:int=2000):
        self.setTransmitData(data=data)  # load data
        self.stop()
        self._driver.setPower(value=power_dBm, format='dBm' ,)
        self._driver.setDebugMode(on_off=True)
        self._driver.freqOverride(frequency_Hz=frequency_Hz)
        self.sendPacketInBuffer(timeout_ms=timeout_ms)

    def startReceive(self,on_off:bool,frequency_Hz:int = 2450e6,timeout_ms:int = 1000):
        if on_off: # if receive mode is not initialized
            self.stop()
            self._driver.setDebugMode(on_off=True)
            self._driver.freqOverride(frequency_Hz=frequency_Hz)
            self._driver.rx(on_off=True)
            self.receiveQ = Queue()
        else:
            self.receiveQ = None
            self._driver.rx(on_off=False)
    def receive(self,on_off:bool,frequency_Hz:int = 2450e6,timeout_ms:int = 1000):
        self.startReceive(on_off=on_off, frequency_Hz=frequency_Hz,)
        if not on_off:
            return
        keep_reading = True
        start = time.time_ns()
        timeout = False
        packet_counter = 0


        while keep_reading:
            try:
                responses_str = self._driver._read(termination_char='\r\n',)
                responses = WSTK_RAILTest_Driver.parseResponse(responses_str) # TODO: parsing response here, should be moved to lower level

                for r in responses:
                    if r.response_type=='(rxPacket)':
                        payload_str = str(r.response_content['payload'])
                        self.receiveQ.put(payload_str)
                        packet_counter = packet_counter + 1
                    else:
                        raise RAILError('Read type is not an rxPacket:',r.response_type)


            except TimeoutError:
                self.logger.warning("Reading timeout at RX")
            timeout = (time.time_ns()-start)/1e6 > timeout_ms
            keep_reading = not(timeout)
        self.stop()
        return self.receiveQ

    def readRSSI(self)->float:
        response = self._driver.getRssi()
        temp = float(response[0].response_content['rssi']) #quick and dirty parsing of RSSI value from the response string
        return temp
    def measureBer(self,nbytes:int=100000,timeout_ms:int=1000,frequency_Hz:int=0)->float:
        """
        Measuring BER on a PN9 stream, can only be used with BER configured RAILtest

        :param int nbytes: number of bytes to perform the measurement on
        :param int timeout_ms: maximum time the measurement can run, in miliseconds
        :param int frequency_Hz: frequency of the recieved  PN9 stream, in Hz

        :return: the BER value in percentage, the percentage of completion
        :rtype: float tuple
        """
        self.stop() # stopping current process just in case
        if frequency_Hz: # if not default frequency is used
            self._driver.setDebugMode(on_off=True)
            self._driver.freqOverride(frequency_Hz=frequency_Hz)

        self._driver.setBerConfig(nbytes) # how many bytes are used for the BER calculation
        self._driver.berRx(on_off=True) # start receiving bytes

        done_percent = 0.0
        ber_percent = 0.0
        rssi_current = 0.0
        start = time.time_ns()
        timeout = False

        while not (timeout or done_percent==100.0):#
            time.sleep(0.1) # 100 miliseconds of delay to stop continuous polling
            responses = self._driver.berStatus() # polling BER status
            timeout = (time.time_ns()-start)/1e6 > timeout_ms

            if timeout:
                self.logger.warn("Timeout during BER measurement!")

            for r in responses:
                if r.response_type=='(berStatus)':
                    ber_percent = float(r.response_content['PercentBitError'])
                    done_percent = float(r.response_content['PercentDone'])
                    rssi_current = float(r.response_content['RSSI'])

                    self.logger.debug("BER: " + str(ber_percent) + "%, Done percent: "+ str(done_percent)+  "% RSSI:  "+ str(rssi_current))
                else:
                    raise RAILError('BER status unkown type:',r.response_type)
        return ber_percent, done_percent,rssi_current

    def measurePer(self,npackets:int=1000,interpacket_delay_s:float=0.0001,frequency_Hz:int=0,tx_start_function=None,timeout_ms = 500)->float:
        """
        Measuring PER

        :param int npackets: number of packets to perform the measurement on
        :param int timeout_ms: maximum time the measurement can run, in miliseconds
        :param int frequency_Hz: frequency in Hz

        :return: the PER value in percentage, the percentage of completion,and the last packets rssi
        :rtype: float tuple
        """
        self.stop() # stopping current process just in case
        if frequency_Hz: # if not default frequency is used
            self._driver.setDebugMode(on_off=True)
            self._driver.freqOverride(frequency_Hz=frequency_Hz)

        #self._driver.setBerConfig(nbytes) # how many bytes are used for the BER calculation
        #self._driver.berRx(on_off=True) # start receiving bytes
        self._driver.rx(on_off=True)

        done_percent = 0.0
        per_percent = 0.0
        rssi_current = 0.0
        start = time.time_ns()
        timeout = False
        self._driver.resetCounters()
        tx_start_function(npackets,interpacket_delay_s)

        try:
            self._driver._write('')
            expected_packets = self._driver._read()
            self.logger.debug("PACKETS:" + expected_packets)
            first_rssi_index = expected_packets.find('rssi')
            if first_rssi_index>0:
                after_rssi_index = expected_packets.find('}', first_rssi_index)
                rssi_current = expected_packets[first_rssi_index+5:after_rssi_index]
                done_percent = 100
            else:
                self.logger.error("No packets on serial!")
        except TimeoutError:
            self.logger.error("No packets on serial!")
            pass

        received_packets = 0

        while not (timeout or npackets==received_packets):#

            self._driver.flushIO()
            self._driver.flushIO()
            try:
                responses = self._driver.status()
            except IndexError:
                self.logger.warn("Index error occured in PER test, that I cannot figure out, skipping to next loop")
                responses = []
            runtime_ms = (time.time_ns()-start)/1e6
            timeout = runtime_ms > timeout_ms

            for r in responses:
                if r.response_type=='(status)':
                    received_packets = float(r.response_content['RxCount'])
                    per_percent = 100 -received_packets /npackets*100
                    self.logger.debug("PER: " + str(per_percent) + "%, Done percent: "+ str(done_percent)+  "% RSSI:  "+ str(rssi_current))
                elif r.response_type == '(rxPacket)':
                    rssi_current =  float(r.response_content['rssi'])
                else:
                    #raise RAILError('BER status unkown type:',r.response_type)
                    self.logger.warn('different response: '+ r.response_type)

        self._driver.resetCounters()
        return per_percent, done_percent,rssi_current
    def stop(self):
        self.logger.info("Stop called\n")
        try:
            _status = self.getStatus() # if this hits in the middle of a command a ValueError will be thrown
        except ValueError: # but we dont care
            _status = self.getStatus()

        if _status.AppMode.upper() in ("CONTINUOUSTX"):
            self._driver.tx(npackets=0)
            self._driver._read(termination_char=None, timeout_ms=200)  # Catch status message of last packet (finished after "tx 0")
        elif _status.AppMode.upper() in ("STREAM"):
            self._driver.setTxStream(on_off=False, mode='cw', antenna=0)
        elif _status.AppMode.upper() in ("BER"):
            self._driver.berRx(on_off=False,)
        elif _status.AppMode.upper() in ("PACKETTX"):
            try:
                self._driver.tx(npackets=0,)#if packet tx is done during this commands execution the device will be set to continouos mode by accident
            except ValueError:
                self.logger.debug(" Value error caught at stopping packet TX")
                self._driver.flushIO()
                _status = self.getStatus()
                if _status.AppMode.upper() in ("CONTINUOUSTX"):
                    self._driver.tx(npackets=0)
        elif _status.AppMode.upper() in ("NONE"):
            pass
        else:
            raise RAILError('unknown RAILTest mode: ',_status.AppMode)
        _status= self.getStatus()
        if _status.RAIL_state_rx:
            self._driver.rx(on_off=False)
        if _status.RAIL_state_tx:
            self._driver.tx(npackets=0)


    def set_wisun_fsk_config(self, radio_config_id:int, profile:str="FAN", whitening:bool=True):
        """
        Configures the radio in Wi-SUN FSK mode. The specific PHY operating mode (e.g. 2b) is set by the radio config used
        TX length definition must always precede calling this
        :param radio_config_id: As per Simplicity Studio project
        :param profile: either 'FAN' or 'ECHONET_HAN'
        :param whitening:
        :return:
        """
        self._driver.setconfigindex(radio_config_id)

        if profile.upper() == "FAN":
            fcs_type = 0
        elif profile.upper() == "ECHONET_HAN":
            fcs_type = 1
        else:
            raise ValueError('Invalid profile: ', profile)
        self._driver.set802154phr(phr_format=1, opt1=fcs_type, opt2=(1 if whitening else 0))

    def set_wisun_ofdm_config(self, radio_config_id:int, mcs:int , scrambler:int=0):
        """
        Configures the radio in Wi-SUN OFDM mode. Option (1-4) is set by the radio config used
        :param radio_config_id: As per Simplicity Studio project
        :param mcs: MCS index (0-6)
        :param scrambler: 0 for '000010111', 1 for '101111100'
        :return:
        """
        self._driver.setconfigindex(radio_config_id)
        self._driver.set802154phr(phr_format=2, opt1=mcs, opt2=scrambler)

    def setSingleTransmitData(self, data:bytes, packet_length_override:int|None=None):
        """
        Sets the TX payload and packet length for single packet
        :param data:
        :param packet_length:
        :return:
        """
        packet_length = packet_length_override if packet_length_override is not None else len(data)
        padding_len = packet_length - len(data)  # this many padding will be needed
        data_to_send = data + bytes([0 for _ in range(0, padding_len)] ) # padding with 0's
        self._driver.setTxLength(length=packet_length)
        chunk_len = 18  # download data to unit in 18-byte chunks
        for k in range(0, len(data_to_send)//chunk_len):
            self._driver.setTxPayload(data=data_to_send[k*chunk_len:(k+1)*chunk_len], offset=k*chunk_len)

    def getTxPacket(self):
        response = self._driver.printTxPacket()[0]
        if response.response_type == '(printTxPacket)':
            return bytes([int(s, 16) for s in (response.response_content["payload"]).split()])
        else:
            raise RAILError('Read type is not a printTxPacket:', response.response_type)

    def is_using_ofdm_pa(self)->bool:
        response = self._driver.getPowerConfig()[0]
        if response.response_type == '(getPowerConfig)':
            mode_str = response.response_content['mode']
            return mode_str.startswith("RAIL_TX_POWER_MODE_OFDM_PA")
        else:
            raise RAILError('Read type is not a getPowerConfig:', response.response_type)
