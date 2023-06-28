# Telec-245 example

This example goes through and measures every parameter needed for a full T254 certification (belonging to the ARIB T-108 standard). It is not recommended for first time users of the framework, they should instead start with trying out a simple TX power sweep using the *TX CW Sweep* example. That script has a detailed README that explains how to get started with the framework.

This example is configured to work with the EFR32FG25. The DUT has to be configured with a RAILTest application that already has all the needed PHYs in its radio configurator. The .sls project file and the .s37 binary file for this can be found in the *DUT_program* folder. The project was created using GSDK 4.2.0.

The output of this example currently consists of screenshots, that the spectrum analyzer (developed and tested with Anritsu MS2692A) saves to a USB drive plugged into it.
Of course, it could be rewritten to provide other file output as well.