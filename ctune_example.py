import time
import serial
import numpy as np
from ctune_w_siggen import ctune_sg
from ctune_w_sa import ctune

board_name = 'BRD4264B'

SA_or_SG_sel = "SG" # CTUNE performed by "SA" or "SG"?

if SA_or_SG_sel == "SA":    # Spectrum Analyzer

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

elif SA_or_SG_sel == "SG":  # Signal Generator

    freq = 915e6        # operating CW frequency
    ctune_init = 120    # initial crystal CTUNE value
    ctune_min = 50      # CTNUE min during the sweep
    ctune_max = 150     # CTUNE max during the sweep
    # narrowband PHY is needed for proper CTUNE tuning
    data_rate = 2400    # FSK2 data rate
    deviation = 1200    # FSK2 frequency deviation

    xo_ctuned, rssi_max = ctune_sg(freq, ctune_init, ctune_min, ctune_max, data_rate, deviation)
    print('\nProgrammed CW Frequency: ' + str(freq))
    print('Crystal tuned CTUNE: ' + str(xo_ctuned) + '\nActual max RSSI: ' + str(rssi_max))

else:
    print("Select between SA or SG!")