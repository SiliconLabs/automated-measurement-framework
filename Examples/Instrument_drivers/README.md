## Instrument driver examples

This folder contains examples for the provided instrument drivers. These are a great starting point for anyone interested in using the Automated Measurement Framework, as they can be used to test whether the Framework can control the instruments owned by the user.

The following examples can be found in this folder:
- `psu_example.py`: Demonstrates basic functions with a programmable PSU (setting voltage, toggling outputs, measuring current etc.)
- `pySpecan_example.py`: Creates a basic measurement using a spectrum analyzer
- `pySpecan_example_siggen.py`: Demonstrates signal generator functionality using a compatible spectrum analyzer
- `siggen_packets_example.py`: Sends pre-defined packets using a signal generator with a set modulation
- `siggen_stream_example.py`: Sends a stream of bits using a signal generator with a set modulation
- `RAILtest_TX_example.py`: Sends a packet every second using a connected WSTK and radio board
- `RAILtest_RX_example.py`: Listens for and receives data using a connected WSTK and radio board
- `RAILtest_BERRX_example.py`: Creates a basic BER measurement between two WSTKs and radio boards