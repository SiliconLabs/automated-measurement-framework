## Examples

This folder contains examples for the Automated Measurement Framework. 

### Recommended starting points:
These are examples that have good documentation and "Getting started" guides.
- **RX:** Can be used to measure BER and PER sensitivity, waterfall diagrams, RSSI sweeps and blocking. Includes a "Getting started" list
- **TX_CW:** Can be used to measure TX CW power (on the fundamental as well as harmonic frequencies). Includes a "Getting started" list
- **Instrument drivers:** Can be used to test the basic functionality of the drivers included in the Framework.

### Other examples:
These are more specific examples that have less documentation and thus are not that suitable for new users. However, they are great for demonstrating how parts of the framework could be used to develop your own applications.
- **Telec245:** Implements a whole T254 certification for the EFR32FG25. Also demonstrates higher level measurements (OBW for example) on an Anritsu spectrum analyzer.
- **DcDc_Spurs:** Measures DC-DC spur levels in TX CW mode