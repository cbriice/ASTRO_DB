#apptest.py - my locally ran database for testing db specific functionality. no server logic or anything

import dash, os
from dash import html, dcc
import dash_bootstrap_components as dbc
import backend_top as dbf
from callbacks_main import register_main_callbacks
from utils.constants import MAIN_MENU_OPS, MASTER_FILE
from callbacks_graphs import register_graph_callbacks
from callbacks_uploaddata import register_upload_callbacks
from callbacks_search import register_search_callbacks
from callbacks_atts import register_att_callbacks
from callbacks_analysis import register_analysis_callbacks

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions = True)
app.title = '[DEV] ASTRO Database Interface'

server = app.server

#master file should be in the app working directory on the server. if this changes, update logic to have absolute filepath attached to master2.h5
dbf.create_master_file(MASTER_FILE, {'machine': 'meld piece of shit'})
#-----------------------------------------------------------------------------------------

app.layout = html.Div([
    html.H2("best database of all time", style = {'text-align': 'center'}),

    html.Div(
        dbc.ButtonGroup([
            dbc.Button(opt, id={'type': 'program-option', 'index': i}, n_clicks=0)
            for i, opt in enumerate(MAIN_MENU_OPS)], 
            className='mb-3'), 
            className = 'd-flex justify-content-center'
        ), html.Hr(),
        html.Div(id='main-content'),
        
        #global dcc.Store objects for saving/loading shit for comparison
        dcc.Store(id = 'global-storage-1', data = [], storage_type = 'memory'),
        dcc.Store(id = 'global-storage-2', data = [], storage_type = 'memory'),
        dcc.Store(id = 'global-graph-storage', data = [], storage_type= 'memory')     
])
#------------------------------------------------------------------------------------------
register_main_callbacks(app)
register_upload_callbacks(app)
register_graph_callbacks(app)
register_search_callbacks(app)
register_att_callbacks(app)
register_analysis_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)

