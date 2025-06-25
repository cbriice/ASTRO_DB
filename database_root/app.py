import dash, io, base64
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import h5rdmtoolbox as h5tbx
import backend_top as dbf
import numpy as np

#ignore everything here it hasn't been updated. working on apptest.py

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'HDF5 Dash Interface'

MASTER_FILE = 'master2.h5'
dbf.create_master_file(MASTER_FILE, {'machine': 'meld piece of shit'})

# === Layout ===
app.layout = html.Div([
    html.H2("Database options"),
    dbc.ButtonGroup([
        dbc.Button(opt, id={'type': 'program-option', 'index': i}, n_clicks=0)
        for i, opt in enumerate([
            'Browse directories', 'Find build', 'Filter by attribute',
            'Search specific attributes', 'Upload .csv file',
            'Show data structure', 'Edit build data'])
    ], 
        className='mb-3'
    ),
    html.Div(id='main-content'),
    dcc.Store(id='selected-build'),
    dcc.Store(id='file-upload-data')
])

# === Callbacks ===

@app.callback(
    Output('main-content', 'children'),
    Input({'type': 'program-option', 'index': dash.ALL}, 'n_clicks')
)
def handle_main_buttons(n_clicks_list):
    triggered = ctx.triggered_id
    if not triggered:
        return "Click a button to start."

    label = ['Browse directories', 'Find build', 'Filter by attribute',
             'Search specific attributes', 'Upload .csv file',
             'Show data structure', 'Edit build data'][int(triggered['index'])]

    if label == 'Browse directories':
        with h5tbx.File(MASTER_FILE, 'r') as master:
            return html.Div([
                html.H4("Select Directory:"),
                dcc.Dropdown(list(master.keys()), id='dir-choice-1')
            ])
        
    elif label == 'Find build':
        return html.Div([
            dcc.Input(id='build-id-input', type='text', placeholder='Enter build ID'),
            html.Button('Submit', id='submit-build-id', n_clicks=0),
            html.Div(id='build-result')
        ])
    
    elif label == 'Upload .csv file':
        return html.Div([
            dcc.Upload(
                id='csv-upload',
                children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center'
                },
                multiple=False
            ),
            html.Div(id='upload-output')
        ])
    
    else:
        return html.Div(f"Feature '{label}' not yet implemented.")

# === CSV Upload Handler ===
@app.callback(
    Output('upload-output', 'children'),
    Input('csv-upload', 'contents'),
    State('csv-upload', 'filename')
)
def handle_upload(contents, filename):
    if contents is None:
        return dash.no_update

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        csv_io = io.StringIO(decoded.decode('utf-8', errors='replace'))
        header_row = dbf.find_header_line(csv_io)
        csv_io.seek(0)
        userfile = pd.read_csv(csv_io, skiprows=header_row)
        return html.Div([
            html.H5(f"Uploaded file: {filename}"),
            html.Pre(userfile.head().to_string(index=False))
        ])
    except Exception as e:
        return html.Div([f"Error parsing file: {e}"])




if __name__ == '__main__':
    app.run(debug=True, port=8080)