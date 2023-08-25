# PyWSTK

PyWSTK is a module for controlling Silicon Labs EFR32 based designs through serial communication (using the RAILTest application). It consists of two separate modules: pyRAIL and pywstk_driver. The pywstk_driver contains the WSTK_RAILTest_Driver class, giving access to basic driver-level commands (setting up and managing serial communication with the device, issuing single RAILTest commands etc.), while the pyRAIL module implements higher level functions that build on top of the driver (such as transmitting data, receiving and counting packets, measuring BER etc.).

This library is meant to be used inside the Automated Measurement Framework(AMF).
More detailed documentation and examples can de found there.

## Usage

It is recommended to use the WSTK_RAILTest class found in the pyRAIL module. This can be created by giving it the COM port of the device as a parameter:

```
from pyRAIL import WSTK_RAILTest

wstk = WSTK_RAILTest("COM8")
```

After this is ready, the supported functions can be called:

```
wstk.resetDevice()

data_to_tx_16 = bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
wstk.transmitData(data=data_to_tx_16, frequency_Hz=2450e6, power_dBm=0, timeout_ms=2000, echo=True)
```

For examples on how to use the modules in actual measurements, please see the examples provided in the Automated Measurement Framework.