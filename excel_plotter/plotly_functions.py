import plotly.graph_objects as go
import pandas as pd


def plot_bathtub(dataset_filename_csv:str,output_filename_html:str):
    data = pd.read_csv(dataset_filename_csv,index_col=[0,1,2])

    z_label = data.columns[0]
    print(z_label)
    data = data.drop(columns=['RSSI'])
    data = data.droplevel('Frequency [MHz]')

    try:
        data_2d = data['PER [%]'].unstack()
    except:
        raise ValueError("Cannot find PER values, maybe BER is set")
    
    x_values = data_2d.columns
    y_values = data_2d.index

    fig = go.Figure(data=[go.Surface(z=data_2d.values,x=x_values,y=y_values)])

    fig.update_layout(title='Frequency Offset Tolerance',scene = dict(
                        xaxis_title=x_values.name,
                        yaxis_title=y_values.name,
                        zaxis_title=z_label), autosize=True)

    fig.show()
    fig.write_html("frequency_offset_3d.html")