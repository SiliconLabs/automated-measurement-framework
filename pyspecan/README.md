# PySpecAn

PySpecAn is a Python library for controlling various types of spectrum analyzers via the SCPI protocol. The library is built on top of the PyVISA package, which allows communication with instruments over a variety of interfaces including GPIB, USB, and Ethernet.

This library is meant to be used inside the Automated Measurement Framework(AMF).
More detailed documentation and examples can de found there.

## Usage

 The SpecAn class is a factory class that returns the appropriate subclass based on the *IDN? query response of the instrument. If the instrument cannot be identified, the GenericSpecAn class is used as a fallback, which has all the basic functions of a spectrum analyzer implemented.

Currently, there are 2 subclasses implemented for various brands of instruments:
- `Anritsu_SignalAnalyzer` ( tested on MS2692A), contains the instrument's built-in Signal Generator functions( see pySpecan_example_siggen.py), and various high level measurements like ACP and OBW etc. in the measurements folder. On how to utilize them, please refer to `telec_t245_measurements.py', which implements all the measurements for a whole T254 certification 
- `RS_SpectrumAnalyzer` (tested on FSV and FPL1007)

The classes take the `Logger.Settings` class from the `common` module of AMF, to set up the internal logging. The default `DEBUG` logging level prints all the SCPI command to console.

```
from pySpecAn import SpecAn
from common import Logger, Level

specan = SpecAn("TCPIP::169.254.88.77::INSTR", auto_detect=True,logger_settings=Logger.Settings(logging_level=Level.INFO))

```
Once the instance is ready, all the functions can be called, check the examples for more info. 
```
specan.setFrequency(433.965e6)
specan.setSpan(50e3)
specan.setRBW(10000.0)
specan.setRefLevel(-60.0)
specan.initiate()
marker = specan.getMaxMarker()

print(marker)
```
## Common errors

Check the AMF main documentation for common errors on SCPI and VISA.

