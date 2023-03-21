import time
import serial
import numpy as np
#from ctune_w_siggen import ctune
from ctune_w_sa import ctune

board_name = 'BRD4264B'

freq = 915e6        # operating CW frequency
ctune_init = 120    # initial crystal CTUNE value
pwr_raw = 200       # raw power value where the crystal tuning is performed at
SA_span = 200e3     # SA span setting
SA_rbw = 10e3       # SA RBW setting

xo_ctuned, actual_cw_freq = ctune(freq, ctune_init, pwr_raw, SA_span, SA_rbw)
print('Programmed CW Frequency: ' + str(freq))
print('Crystal tuned CTUNE: ' + str(xo_ctuned) + '\nActual CW Frequency: ' + str(actual_cw_freq))
freq_error = actual_cw_freq - freq
print('Frequency error: ' + str(freq_error) + ' Hz')