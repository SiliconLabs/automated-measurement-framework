# pyPSU

pyPSU is a Python library for controlling various types of Puwer Supplies via the SCPI protocol. The library is built on top of the PyVISA package, which allows communication with instruments over a variety of interfaces including GPIB, USB, and Ethernet.

This library is meant to be used inside the Automated Measurement Framework(AMF).

More detailed documentation and examples can de found there.

## Usage

The PSU class is a factory class that returns the appropriate subclass based on the *IDN? query response of the instrument. If the instrument cannot be identified, the GenericPSU class is used as a fallback, which has all the basic functions of a power supply implemented.

Currently, the only implemented one is the GenericPSU class, tested on Agilent E3646A.

The classes take the `Logger.Settings` class from the `common` module of AMF, to set up the internal logging. The default `DEBUG` logging level prints all the SCPI command to console.

```
from pyPSU import PSU, PSUSettings
from common import Logger, Level

psu = PSU(ASLR8::INSTR", auto_detect=True,logger_settings=Logger.Settings(logging_level=Level.INFO))


```
Once the instance is ready, all the functions can be called, check the examples for more info. 
```
psu.geterror()


psu.selectOutput(1)
psu.toggleOutput(True)

psu.setVoltage(2.0)

```

Check the example for more.
## Common errors

Check the AMF main documentation for common errors on SCPI and VISA.

