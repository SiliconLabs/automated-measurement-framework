
"""
Automated Measurement Framework - PSU driver example

This example demonstrates the use of the pyPSU driver, including selecting and toggling outputs, setting voltages and measuring current. 

Tested with:
    - Keysight E3646A

"""

#################################################################################################################################################

# This is needed for the current folder structure of the examples. Scripts placed in the main folder won't need this.
try:
    from pypsu import pyPSU
except ModuleNotFoundError:
    # This assumes that the script is 2 folders deep compared to the main folder. 
    import sys
    sys.path.append('../../')

#################################################################################################################################################

from pypsu import pyPSU
from time import sleep

psu = pyPSU.PSU("ASRL8::INSTR")

psu.selectOutput(1)
psu.toggleOutput(True)

psu.setVoltage(2.0)
sleep(0.5)
psu.setVoltage(3.0)

print("Voltage: ", psu.getVoltage())
print("Measured current: ", psu.measCurrent())

print(psu.settings)

psu.toggleOutput(False)