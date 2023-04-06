import numpy as np
import pandas as pd
import xlsxwriter
import os

def Py_to_Excel_plotter(source_xlsx_file:str):
    # Import raw vs power data from existing xlsx
    raw_data = pd.read_excel(source_xlsx_file, sheet_name="RawData")
    # Create new xlsx with the imported data + the plots of it. Therefore, the code creates a new xlsx instead of writing into the imported xlsx.
    output_workbook_name = "Plot" + source_xlsx_file
    workbook = xlsxwriter.Workbook(output_workbook_name)
    Raw_Sheet = workbook.add_worksheet(name= 'RawData')
    Chart_Sheet = workbook.add_worksheet(name= 'Charts')
    # Copy imported data to this new xlsx
    col_name: str
    for i, col_name in enumerate(raw_data.columns):
        Raw_Sheet.write(0, i, col_name)
        Raw_Sheet.write_column(1, i, raw_data[col_name])
  
    # Create empty plot
    plot = workbook.add_chart({"type" : "scatter"})
    # Plotting
    plot.add_series({"categories" : "=RawData!$B$2:$B$10000",
                  "values" : "=RawData!$C$2:$C$10000",
                 "name" : "CTUNE vs FreqError"})
    plot.set_x_axis({"name" : "CTUNE [decimal]"})
    plot.set_y_axis(({"name" : "Frequency Error [kHz]"}))
    plot.set_title({'name': 'CTUNE vs FreqError', 'name_font':{'name':'Calibri(Body)','size':12}})
    Chart_Sheet.insert_chart("A" + "1", plot, {'x_scale': 1.2, 'y_scale': 1.4})
    
    # shaping and filtering
    Raw_Sheet.set_column(0, 13, 20)
    #Raw_Sheet.autofilter(0, 2, 10000, 0)

    workbook.close()

    #replace original xlsx file with new xlsx file containing the plots
    os.remove(source_xlsx_file)
    os.rename(output_workbook_name, source_xlsx_file)