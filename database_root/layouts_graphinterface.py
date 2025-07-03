from dash import dcc, html
import dash_bootstrap_components as dbc
from utils.helpers import generate_plot_list

def graphmain_layout():
    return html.Div([
        html.H4("All-powerful graphing interface", style = {'text-align': 'center'}),
        html.H6("Do you want stacked or individual graphs?"),
        dcc.RadioItems(
            id = 'stacked-or-not',
            options = [{'label': 'Stacked', 'value': 'stacked'},
                       {'label': 'Individual', 'value': 'indiv'}],
            value = 'indiv'
        ),
        html.Button('Confirm', 'confirm-stacked', n_clicks = 0),
        html.Div(id = 'graph-page-2'),
        dcc.Store(id = 'generated-plots', data = [], storage_type = 'memory')
    ],
        style = {'padding-left': '35px'}
    )
        
#prompt 2
def graphmain_individual():
    return html.Div([
        html.Br(),
        html.H6("Input path to plottable data:"),
        dcc.Input(
            id = 'data-path',
            type = 'text',
            placeholder = '/path/to/data',
            value = "",
            size = '50'
        ), 
        html.Div(id = 'graph-path-confirm'),
        dcc.Store(id = 'graph-path', storage_type = 'memory'),

        html.Button('Submit', id = 'submit-ind-graph-path', n_clicks = 0),
        dcc.Store('graph-target-ops', storage_type = 'memory'),
        html.Div(id = 'graph-page-3')
    ])

#prompt 3
def decide_plotall():
    return html.Div([
        html.Br(),
        html.H6("Plot all valid columns from the file at this address?"),
        dcc.RadioItems(
            id = 'plot-all-from-df', 
            options = [{'label': 'Plot all', 'value': 'plot-all'},
                       {'label': 'Plot single dataset', 'value': 'plot-single'}],
            value = 'plot-single'
        ),
        html.Button('Confirm', id = 'submit-plot-all', n_clicks = 0),
        html.Div(id = 'graph-page-4')
    ])

def dummy_decide_plotall():
    return html.Div([
        html.Br(),
        html.H6("Plot all valid columns from the file at this address?"),
        dcc.RadioItems(
            id = 'dummy-plot-all-from-df', 
            options = [{'label': 'Plot single dataset', 'value': 'plot-single'}],
            value = 'plot-single'
        ),
        html.Button('Confirm', id = 'dummy-submit-plot-all', n_clicks = 0),
        html.Div(id = 'dummy-graph-page-4')
    ])

def info_not_plotall(target_list):
    return html.Div([
        html.Br(),
        html.H6("Choose data to plot"),
        html.Div(id = 'npa-dd-container', children = [ 
            dcc.Dropdown(
                id = 'target-ind-npa', 
                options = target_list
                ),
        ], style = {'padding-right': '1500px'}
        ), html.Br(),

        html.H6("Dimension of graph?"), 
        dcc.RadioItems(
            id = 'graph-dim-npa',
            options = [{'label': '2D', 'value': '2'},
                       {'label': '3D', 'value': '3'}],
            value = '2'
        ), html.Br(),

        html.H6("Metric?"), 
        dcc.RadioItems(
            id = 'metric-npa',
            options = [{'label': 'Metric', 'value': 'metric-true'},
                       {'label': 'Customary', 'value': 'customary-true'}],
            value = 'customary-true'
        ),

        dcc.Store(id = 'npa-stored-plots', storage_type = 'memory'),
        html.Button('Submit', id = 'submit-ind-graph-data', n_clicks = 0),
        html.Div(id = 'npa-graph-output'),
        html.Div(id = 'color-axis-shit')
    ])

def color_adjust():
    return html.Div([
        html.H6('Adjust color axis definitions?'),
        html.Label('Color scale min:'),
        dcc.Input(
            id = 'color-min',
            type = 'number',
            placeholder = 'Min', 
            step = 0.1,
            debounce = True
        ), html.Br(),
        html.Label('Color scale max:'),
        dcc.Input(
            id = 'color-max',
            type = 'number',
            placeholder = 'Max', 
            step = 0.1,
            debounce = True
        ), html.Br(),
        html.Button('Confirm', id = 'submit-color-scale', n_clicks = 0),
        html.Div(id = 'new-scale-3d-plot')
    ], style = {'padding-bottom': '30px'}
    )

#---- plot all from dataset ones
def info_plotall():
    return html.Div([
        html.Br(),
        html.H6("Dimension of graph?"), 
        dcc.RadioItems(
            id = 'graph-dim-pa',
            options = [{'label': '2D', 'value': '2'},
                       {'label': '3D', 'value': '3'}],
            value = '2'
        ), html.Br(),

        html.H6("Metric?"), 
        dcc.RadioItems(
            id = 'metric-pa',
            options = [{'label': 'Metric', 'value': 'metric-true'},
                       {'label': 'Customary', 'value': 'customary-true'}],
            value = 'customary-true'
        ),

        dcc.Store(id = 'pa-plot-list', storage_type = 'memory'),
        html.Button('Confirm', id = 'submit-all-graph-data', n_clicks = 0),
        html.Div(id = 'graph-page-5')
    ])

def show_plotall(plots):
    return html.Div([
        html.Br(),
        html.H6("Select graphs to view:"),
        dcc.Checklist(
            id = 'pa-plot-selector',
            options = generate_plot_list(plots),
            labelStyle = {'width': '10%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '1px'}
        ),
        html.Button('Show graphs', id = 'submit-pa-graph-choices', n_clicks = 0, 
                    style = {'padding-left': '100px', 'padding-right': '100px', 'backgroundColor': '#c8e9b8'}), html.Br(),
        html.Div(id = 'pa-plot-output')
    ])

#------------------------------ stacked plots layouts
def graphmain_stacked():
    return html.Div([
        html.Br(),
        html.H5('Stacked graph generator'), html.Br(),
        html.H6("Addresses?"),
        dcc.Input(id = 'stack-addy-input', type = 'text', placeholder = '/some/address', size = '50'), html.Br(),
        html.Button('Confirm', id = 'save-stacker', n_clicks = 0),
        html.Button('Clear selections', id = 'clear-stackers', n_clicks = 0), html.Br(),

        html.Div(id = 'status-stackers'), html.Br(),
        html.H6('Stored addresses:'),
        html.Div(id = 'stacker-current-list'), html.Br(),
        
        dcc.Store(id = 'stackers', data = [], storage_type = 'memory'),
        html.Button('Show graph', id = 'submit-stackers', n_clicks = 0),
        html.Div(id = 'stacked-plot')
    ])

def display_plots(plot_div):
    return html.Div([
        plot_div, html.Br(),
        html.Button('Store for analysis', id = 'store-plot', n_clicks = 0), html.Br(), 
        html.Div(id = 'store-plot-status'), html.Br()
    ])
