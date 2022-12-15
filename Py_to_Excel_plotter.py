import numpy as np
import pandas as pd
import xlsxwriter
import os

def Py_to_Excel_plotter(source_xlsx_file:str,input_harm_order_up_to:int):
    # Import raw vs power data from existing xlsx
    raw_vs_output_power = pd.read_excel(source_xlsx_file, sheet_name="RawData")
    #raw_vs_output_power_sum = pd.read_excel(source_xlsx_file, sheet_name="Summary")
    
    # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
    output_workbook_name = "Plot" + source_xlsx_file
    workbook = xlsxwriter.Workbook(output_workbook_name)
    #Sum_Sheet = workbook.add_worksheet(name= 'Summary')
    Fund_Sheet = workbook.add_worksheet(name= 'RawData')
    Chart_Sheet = workbook.add_worksheet(name= 'Charts')
    # Copy imported data to this new xlsx
    col_name: str
    for i, col_name in enumerate(raw_vs_output_power.columns):
        Fund_Sheet.write(0, i, col_name)
        Fund_Sheet.write_column(1, i, raw_vs_output_power[col_name])
    #col_name: str
    #for i, col_name in enumerate(raw_vs_output_power_sum):
        #Sum_Sheet.write(0, i, col_name)
        #Sum_Sheet.write_row(0, i, raw_vs_output_power_sum)

    # Create empty plot for power vs raw
    plot = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the Fundamental power vs raw
    plot.add_series({"categories" : "=RawData!$B$2:$B$10000",
                  "values" : "=RawData!$E$2:$E$10000",
                 "name" : "Fundamental"})
    plot.set_x_axis({"name" : "Raw power value"})
    plot.set_y_axis(({"name" : "Amplitude [dBm]"}))
    plot.set_title({'name': 'TX Power', 'name_font':{'name':'Calibri(Body)','size':12}})
    # Plot the harmonic power levels vs raw
    array_harm_letters = ["F", "G", "H", "I", "J", "K", "L", "M", "N"]
    array_harm_indices = ["2","3","4","5","6","7","8","9","10"]
    for i in range (0, input_harm_order_up_to-1):
        current_harm_letter = array_harm_letters[i]
        current_harm_index = array_harm_indices[i]
        current_harm_name = "Harmonic #" + current_harm_index
        current_harm_excel_var = "=RawData!$" + current_harm_letter + "$2" + ":$" + current_harm_letter + "$10000"
        #print(current_harm_name)
        #print(current_harm_excel_var)
        plot.add_series({"categories": "=RawData!$B$2:$B$10000",
                         "values": "=RawData!$" + current_harm_letter + "$2" + ":$" + current_harm_letter + "$10000",
                         "name": current_harm_name})
        plot.set_x_axis({"name": "Raw power value"})
        plot.set_y_axis(({"name": "Amplitude [dBm]"}))
    #print(i)
    #plot_cell = array_harm_letters[i+2]
    Chart_Sheet.insert_chart("A" + "1", plot, {'x_scale': 1.2, 'y_scale': 1.4})

    # Create empty power vs PAVDD plot
    plot_pavdd = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the Fundamental power vs PAVDD
    plot_pavdd.add_series({"categories" : "=RawData!$C$2:$C$10000",
                  "values" : "=RawData!$E$2:$E$10000",
                 "name" : "Fundamental"})
    plot_pavdd.set_x_axis({"name" : "PAVDD [V]"})
    plot_pavdd.set_y_axis(({"name" : "Amplitude [dBm]"}))
    plot_pavdd.set_title({'name': 'TX Power', 'name_font':{'name':'Calibri(Body)','size':12}})
    # Plot the harmonic power levels vs PAVDD
    array_harm_letters = ["F", "G", "H", "I", "J", "K", "L", "M", "N"]
    array_harm_indices = ["2","3","4","5","6","7","8","9","10"]
    for i in range (0, input_harm_order_up_to-1):
        current_harm_letter = array_harm_letters[i]
        current_harm_index = array_harm_indices[i]
        current_harm_name = "Harmonic #" + current_harm_index
        current_harm_excel_var = "=RawData!$" + current_harm_letter + "$2" + ":$" + current_harm_letter + "$10000"
        #print(current_harm_name)
        #print(current_harm_excel_var)
        plot_pavdd.add_series({"categories": "=RawData!$C$2:$C$10000",
                         "values": "=RawData!$" + current_harm_letter + "$2" + ":$" + current_harm_letter + "$10000",
                         "name": current_harm_name})
        plot_pavdd.set_x_axis({"name": "PAVDD [V]"})
        plot_pavdd.set_y_axis(({"name": "Amplitude [dBm]"}))
    #plot_cell_pavdd = array_harm_letters[i+2]
    Chart_Sheet.insert_chart("J" + "1", plot_pavdd, {'x_scale': 1.2, 'y_scale': 1.4})

    # Create empty power vs freq plot
    plot_freq = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the Fundamental power vs freq
    plot_freq.add_series({"categories" : "=RawData!$A$2:$A$10000",
                  "values" : "=RawData!$E$2:$E$10000",
                 "name" : "Fundamental"})
    plot_freq.set_x_axis({"name" : "Frequency [MHz]"})
    plot_freq.set_y_axis(({"name" : "Amplitude [dBm]"}))
    plot_freq.set_title({'name': 'TX Power', 'name_font':{'name':'Calibri(Body)','size':12}})
    # Plot the harmonic power levels vs freq
    array_harm_letters = ["F", "G", "H", "I", "J", "K", "L", "M", "N"]
    array_harm_indices = ["2","3","4","5","6","7","8","9","10"]
    for i in range (0, input_harm_order_up_to-1):
        current_harm_letter = array_harm_letters[i]
        current_harm_index = array_harm_indices[i]
        current_harm_name = "Harmonic #" + current_harm_index
        current_harm_excel_var = "=RawData!$" + current_harm_letter + "$2" + ":$" + current_harm_letter + "$10000"
        #print(current_harm_name)
        #print(current_harm_excel_var)
        plot_freq.add_series({"categories": "=RawData!$A$2:$A$10000",
                         "values": "=RawData!$" + current_harm_letter + "$2" + ":$" + current_harm_letter + "$10000",
                         "name": current_harm_name})
        plot_freq.set_x_axis({"name": "Frequency [MHz]"})
        plot_freq.set_y_axis(({"name": "Amplitude [dBm]"}))
    #plot_cell_freq = array_harm_letters[i+2]
    Chart_Sheet.insert_chart("S" + "1", plot_freq, {'x_scale': 1.2, 'y_scale': 1.4})

    # Create empty current vs raw plot
    plot_current_raw = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the current vs raw power
    plot_current_raw.add_series({"categories" : "=RawData!$B$2:$B$10000",
                  "values" : "=RawData!$D$2:$D$10000",
                 "name" : "TX current"})
    plot_current_raw.set_x_axis({"name" : "Raw power value"})
    plot_current_raw.set_y_axis(({"name" : "TX current [mA]"}))
    plot_current_raw.set_title({'name': 'TX current', 'name_font':{'name':'Calibri(Body)','size':12}})
    #plot_cell_current_raw = array_harm_letters[i+2]
    Chart_Sheet.insert_chart("A" + "22", plot_current_raw, {'x_scale': 1.2, 'y_scale': 1.4})

    # Create empty current vs pavdd plot
    plot_current_pavdd = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the current vs raw power
    plot_current_pavdd.add_series({"categories" : "=RawData!$C$2:$C$10000",
                  "values" : "=RawData!$D$2:$D$10000",
                 "name" : "TX current"})
    plot_current_pavdd.set_x_axis({"name" : "PAVDD [V]"})
    plot_current_pavdd.set_y_axis(({"name" : "TX current [mA]"}))
    plot_current_pavdd.set_title({'name': 'TX current', 'name_font':{'name':'Calibri(Body)','size':12}})
    #plot_cell_current_pavdd = array_harm_letters[i+2]
    Chart_Sheet.insert_chart("J" + "22", plot_current_pavdd, {'x_scale': 1.2, 'y_scale': 1.4})

    # Create empty current vs freq plot
    plot_current_freq = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the current vs freq power
    plot_current_freq.add_series({"categories" : "=RawData!$A$2:$A$10000",
                  "values" : "=RawData!$D$2:$D$10000",
                 "name" : "TX current"})
    plot_current_freq.set_x_axis({"name" : "Frequency [MHz]"})
    plot_current_freq.set_y_axis(({"name" : "TX current [mA]"}))
    plot_current_freq.set_title({'name': 'TX current', 'name_font':{'name':'Calibri(Body)','size':12}})
    #plot_cell_current_freq = array_harm_letters[i+2]
    Chart_Sheet.insert_chart("S" + "22", plot_current_freq, {'x_scale': 1.2, 'y_scale': 1.4})
    
    # shaping and filtering
    Fund_Sheet.set_column(0, 13, 16)
    Fund_Sheet.autofilter(0, 0, 10000, 2)

    workbook.close()

    #replace original xlsx file with new xlsx file containing the plots
    os.remove(source_xlsx_file)
    os.rename(output_workbook_name, source_xlsx_file)
