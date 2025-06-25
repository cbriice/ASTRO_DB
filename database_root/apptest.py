import dash
from dash import html
import dash_bootstrap_components as dbc
import backend_top as dbf
from callbacks_main import register_main_callbacks
from utils.constants import MAIN_MENU_OPS
from callbacks_graphs import register_graph_callbacks
from callbacks_uploaddata import register_upload_callbacks
from callbacks_search import register_search_callbacks
from callbacks_atts import register_att_callbacks

MASTER_FILE = 'master2.h5'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions = True)
app.title = 'ASTRO Database Interface'

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
        ),
        html.Div(id='main-content')     
])
#------------------------------------------------------------------------------------------
register_main_callbacks(app)
register_upload_callbacks(app)
register_graph_callbacks(app)
register_search_callbacks(app)
register_att_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)

