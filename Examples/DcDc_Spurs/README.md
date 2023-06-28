# DC-DC Spur measurement example

This example measures DC-DC spur levels on an EFR device that is transmitting a CW wave. It is not recommended for first time users of the framework, they should instead start with trying out a simple TX power sweep using the *TX CW Sweep* example.

The parameters that need to be set before running this script can be found at the end of the file, after `if __name__ == '__main__':`.

The output of this example currently consists of screenshots, that the spectrum analyzer (developed and tested with Anritsu MS2692A) saves to a USB drive plugged into it. It also saves the final results into an Excel file.