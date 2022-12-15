import numpy as np
import pandas as pd
import xlsxwriter
import os

def Py_to_Excel_plotter(source_xlsx_file:str):
    # Import raw vs power data from existing xlsx
    parameters = pd.read_excel(source_xlsx_file, sheet_name="Parameters")
    raw_data = pd.read_excel(source_xlsx_file, sheet_name="RawData")
    sens_data = pd.read_excel(source_xlsx_file, sheet_name="SensData")
    
    # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
    output_workbook_name = "Plot" + source_xlsx_file
    workbook = xlsxwriter.Workbook(output_workbook_name)
    Parameters_Sheet = workbook.add_worksheet(name= 'Parameters')
    Raw_Sheet = workbook.add_worksheet(name= 'RawData')
    Sens_Sheet = workbook.add_worksheet(name= 'SensData')
    Chart_Sheet = workbook.add_worksheet(name= 'Charts')
    # Copy imported data to this new xlsx
    col_name: str
    for i, col_name in enumerate(raw_data.columns):
        Raw_Sheet.write(0, i, col_name)
        Raw_Sheet.write_column(1, i, raw_data[col_name])
    col_name: str
    for i, col_name in enumerate(sens_data.columns):
        Sens_Sheet.write(0, i, col_name)
        Sens_Sheet.write_column(1, i, sens_data[col_name])
    col_name: str
    for i, col_name in enumerate(parameters.columns):
        Parameters_Sheet.write(0, i, col_name)
        Parameters_Sheet.write_column(1, i, parameters[col_name])
  
    # Create empty plot for input power vs BER
    plot = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the Fundamental input power vs BER
    plot.add_series({"categories" : "=RawData!$B$2:$B$10000",
                  "values" : "=RawData!$C$2:$C$10000",
                 "name" : "BER"})
    plot.set_x_axis({"name" : "Input Power [dBm]"})
    plot.set_y_axis(({"name" : "BER [%]"}))
    plot.set_title({'name': 'Waterfall', 'name_font':{'name':'Calibri(Body)','size':12}})
    Chart_Sheet.insert_chart("A" + "1", plot, {'x_scale': 1.2, 'y_scale': 1.4})

    # Create empty plot for frequency vs Sensitivity
    plot_sens = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"})
    # Plot the Fundamental frequency vs Sensitivity
    plot_sens.add_series({"categories" : "=SensData!$A$2:$A$10000",
                  "values" : "=SensData!$B$2:$B$10000",
                 "name" : "Sens."})
    plot_sens.set_x_axis({"name" : "Frequency [MHz]"})
    plot_sens.set_y_axis(({"name" : "Sensitivity [dBm]"}))
    plot_sens.set_title({'name': 'Sensitivity vs Frequency', 'name_font':{'name':'Calibri(Body)','size':12}})
    Chart_Sheet.insert_chart("A" + "22", plot_sens, {'x_scale': 1.2, 'y_scale': 1.4})
    
    # shaping and filtering
    Parameters_Sheet.set_column(0, 13, 16)
    Raw_Sheet.set_column(0, 13, 16)
    Raw_Sheet.autofilter(0, 0, 10000, 0)
    Sens_Sheet.set_column(0, 13, 16)

    workbook.close()

    #replace original xlsx file with new xlsx file containing the plots
    os.remove(source_xlsx_file)
    os.rename(output_workbook_name, source_xlsx_file)
