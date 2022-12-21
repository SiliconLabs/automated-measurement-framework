from pydoc import visiblename
from tkinter import N
from pywstk.pywstk_driver import WSTK_RAILTest_Driver
from pyspecan.pySpecAn import SpecAn
import numpy as np
from pypsu import pyPSU
from matplotlib import pyplot as plt
import xlsxwriter
from time import sleep
from datetime import datetime as dt
from excel_plotter.Py_to_Excel_plotter import Py_to_Excel_plotter

# Tested chip and board names 
chip_name = 'EFR32FG28'
board_name = 'BRD4401A'

# number of frequency sweep points or discrete frequencies can be added below in "frequencies" list
freq_start = 868e6
freq_stop = 928e6
freq_number_steps = 2
#frequencies = np.linspace(freq_start, freq_stop, freq_number_steps, dtype=float)
frequencies = [868e6,920e6]

# number of PAVDD measurement sweep points or discrete PA supply voltage levels can be added below in "pavdd_levels" list
psu_present = False
PAVDD_min = 2.0
PAVDD_max = 3.6
PAVDD_number_steps = 2
#pavdd_levels = np.linspace(PAVDD_min, PAVDD_max, PAVDD_number_steps, dtype=float)
pavdd_levels = [3.3,3.6]
PAVDD_max = max(pavdd_levels)

if not  psu_present:
    pavdd_levels = [3.3]
    PAVDD_max = max(pavdd_levels)

# number of raw power sweep measurement points or discrete raw power values can be added below in "power_levels" list
min_pwr_state = 0
max_pwr_state = 240
pwr_number_steps = 25
power_levels = np.linspace(min_pwr_state, max_pwr_state, pwr_number_steps, dtype=int)
#power_levels = [10, 100, 240]

# highest harmonic order to measure
harm_order_up_to = 10

# SA settings
specan_address = 'TCPIP::169.254.250.234::INSTR'
span = 10e6
RBW = 1e6
ref_level = 10


if psu_present:
    psu = pyPSU.PSU("ASRL8::INSTR")
    psu.selectOutput(1)
    psu.toggleOutput(True)
    psu.setVoltage(PAVDD_max)
    sleep(0.1)

wstk = WSTK_RAILTest_Driver('COM10')
wstk_echo = False
wstk.reset()
wstk.rx(on_off=False, echo=wstk_echo)
wstk.setTxTone(on_off=True, mode="CW", echo=wstk_echo)

timestamp = dt.now().timestamp()
workbook_name = board_name + '_Raw_PAVDD_Freq_vs_Power-Harmonic-Current_results_'+str(int(timestamp))+'.xlsx'
workbook = xlsxwriter.Workbook(workbook_name)
sheet_sum = workbook.add_worksheet('Summary')
sheet_sum.write(0, 0, 'Chip name: ' + chip_name)
sheet_sum.write(1, 0, 'Board name: ' + board_name)

harmonics = []
for i in range(1, harm_order_up_to + 1):
    harmonics.append(i)
sheet_sum.write(2, 0, 'Harmonic orders measured: ' + str(harmonics))
sheet_sum.write(3, 0, 'Raw power levels swept: ' + str(power_levels))
sheet_sum.write(5, 0, 'Test frequencies [MHz]:')
for i, f in enumerate(frequencies):
    sheet_sum.write(6+i, 0, str(f/1e6))
sheet_sum.write(5, 3, 'Test supply voltages [V]:')
for j, V in enumerate(pavdd_levels):
    sheet_sum.write(6+j, 3, str(V))

worksheet = workbook.add_worksheet('RawData')
worksheet.write(0, 0, 'Frequency [MHz]')
worksheet.write(0, 1, 'PA raw values')
worksheet.write(0, 2, 'PAVDD [V]')
worksheet.write(0, 3, 'TX current [mA]')
worksheet.write(0, 4, 'Fundamental [dBm]')
for r in range(5, harm_order_up_to+4):
    w = r - 3 
    worksheet.write(0, r, 'Harmonic #%d [dBm]' % w)
row = 1

for freq in frequencies:

    wstk.setTxTone(on_off=False, mode="CW", echo=wstk_echo)
    wstk.setDebugMode(on_off=True, echo=wstk_echo)
    wstk.freqOverride(freq, echo=wstk_echo)
    wstk.setTxTone(on_off=True, mode="CW", echo=wstk_echo)

    for pavdd in pavdd_levels:
        if psu_present:
            psu.setVoltage(pavdd)
            sleep(0.1)
        # measured power levels at fundamental and harmonics
        meas_sum2D = np.empty((len(power_levels), harm_order_up_to))
        # for harmonic iterations
        n = 1

        while n <= harm_order_up_to:

            if __name__ == "__main__":
                wstk_echo = False
                specan = SpecAn(resource=specan_address)
                specan.command("SYST:DISP:UPD ON")
                specan.setMode('single')
                specan.setFrequency(n * freq)
                specan.setSpan(span)
                specan.setRBW(RBW)
                specan.setRefLevel(ref_level)
            
                measured_power = np.empty(len(power_levels))
                measured_power_curr = np.empty(len(power_levels))
                
                for k,pl in enumerate(power_levels):
                    wstk.setTxTone(on_off=False, mode="CW", echo=wstk_echo)
                    wstk.setPower(value=pl, format='raw', echo=wstk_echo)
                    wstk.setTxTone(on_off=True, mode="CW", echo=wstk_echo)
                    specan.initiate()
                    marker = specan.getMaxMarker()
                    print(pl, marker)
                    measured_power[k] = marker.value
                    meas_sum2D[k,n-1] = marker.value
                    if psu_present:
                        if n == 1:
                            i = psu.measCurrent() * 1000
                            print(pl, i)
                            measured_power_curr[k] = i
                    else:
                         measured_power_curr[k] = 0
            if n == 1:
                current  = measured_power_curr
        
            n += 1 

        voltage = np.empty(len(power_levels))
        freqs_sheet = np.empty(len(power_levels))
        for i in range(len(power_levels)):
            voltage[i] = pavdd
            freqs_sheet[i] = freq/1e6
        if type(power_levels) == list:
            results = np.c_[(freqs_sheet.T, power_levels, voltage.T, current.T, meas_sum2D)]
        else:
            results = np.c_[(freqs_sheet.T, power_levels.T, voltage.T, current.T, meas_sum2D)]
        column = 0
        for col, data in enumerate(results.T):
            worksheet.write_column(row, col, data)  
        row = row + len(power_levels) 

workbook.close()

wstk.setTxTone(on_off=False, mode="CW", echo=wstk_echo)
#wstk.reset()
sleep(0.1)
if psu_present:
    psu.toggleOutput(False)

# use pandas data frame instead??
Py_to_Excel_plotter(workbook_name, harm_order_up_to)

print("\nDone with measurements")