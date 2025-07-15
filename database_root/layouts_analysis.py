from dash import dcc, html
from utils.constants import METRICS_MACHINEFILE

def analysis_main():
    return html.Div([
        html.H4('Comparison/analysis page', style = {'text-align': 'center'}), html.Br(),
        html.Div([
            html.Div([
                html.Button('Load storage', id = 'load-storage', n_clicks = 0, style = {'backgroundColor': "#40b8fd"}),
                html.Button('Clear storage', id = 'clear-storage', n_clicks = 0), 
                html.Button('Create custom benchmark', id = 'custom-benchmark', n_clicks = 0), html.Br(), html.Br()
            ], style = {'padding-left': '700px'}),
            html.Div(id = 'analysis-2')
        ], style = {'padding-left': '50px', 'padding-right': '50px', 'padding-bottom': '50px'}),
        dcc.Store(id = 'benchmark-mets', storage_type = 'session', data = []),
        dcc.Store(id = 'custom-benchmark-container', storage_type = 'session')
    ])

def load_storage(path1, paths2, plot_data):
    paths2_list = []
    if paths2:
        for item in paths2:
            paths2_list.append(html.Li(item))
    else:
        paths2_list.append('No data')
    
    stored_sources = []
    if plot_data:
        for item in plot_data:
            stored_sources.append(html.Li(item.get('source')))
    else:
        stored_sources.append('No data')

    return html.Div([
        html.H6('Benchmark data:'), 
        html.Ul(['Custom benchmark' if isinstance(path1, dict) else (path1 or 'No data')]),
        html.H6('Comparison data:'),
        html.Ul(paths2_list), 
        html.H6('Stored plots:'),
        html.Ul(stored_sources), html.Br(),

        html.Button('Generate comparison summary', id = 'gen-comp-summary', n_clicks = 0), 
        html.Button('Load graphs', id = 'load-plots', n_clicks = 0),
        html.Br(), html.Br(),

        html.Label('To search for similar builds to benchmark, enter desired normalized difference threshold (in percentage):'),
        dcc.Input(id = 'norm-threshold', type = 'number', size = '30'),
        html.Button('Search', id = 'search-custom-benchmark', n_clicks = 0), html.Br(), html.Br(),

        html.Div(id = 'analysis-3'),
        html.Div(id = 'analysis-3-2')
    ])

def custom_benchmark1():
    return html.Div([
        html.H6('Choose metrics to add to custom benchmark:'), html.Br(),
        dcc.Dropdown(
            id = 'choose-met-bench', 
            options = [{'label': 'Machine file metrics', 'value': 'mach-mets'},
                       {'label': 'Sensor file metrics', 'value': 'sens-mets'},
                       {'label': 'Other metrics', 'value': 'other-mets'}],
            placeholder = 'Select',
            style = {'maxWidth': '200px'} 
        ), html.Br(),
        html.Button('Clear metrics', id = 'clear-custom-bench', n_clicks = 0), html.Br(), html.Br(),
        html.Div(id = 'custom-bench-1'), html.Br(),
        html.Div(id = 'custom-bench-2'), html.Br(),
        html.Div(id = 'custom-bench-3'), html.Br(), 
        html.Button('Submit and enter values', id = 'submit-custom-metrics', n_clicks = 0, style = {'backgroundColor': "#dcfac8"}), html.Br(),
        html.Div(id = 'custom-bench-4')
    ])

def choose_machmets():
    return html.Div([
        html.H6('Machine file metrics'), html.Br(),
        dcc.Checklist(
            id = 'machinefile-mets-select', 
            options = [{'label': m, 'value': m} for m in METRICS_MACHINEFILE],
            labelStyle = {'width': '10%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '1px'}
        ), html.Br(),
        html.Button('Add metrics', id = 'add-mach-mets', n_clicks = 0)
    ])

def choose_sensorcat():
    return html.Div([
        dcc.Dropdown(
            id = 'choose-sensor-cat', 
            options = [{'label': 'Force sensors', 'value': 'force'},
                       {'label': 'HT heat flux sensors', 'value': 'hthfs'},
                       {'label': 'LT heat flux sensors', 'value': 'lthfs'},
                       {'label': 'Thermocouples', 'value': 'therms'}],
            placeholder = 'Select',
            style = {'maxWidth': '200px'}
        ), html.Br(),
        html.Div(id = 'sensor-checklist')
    ])

def choose_sensormets(ops):
    return html.Div([
        html.H6('Sensor file metrics'), html.Br(),
        dcc.Checklist(
            id = f'sensorfile-mets-select', 
            options = [{'label': m, 'value': m} for m in ops],
            labelStyle = {'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginBottom': '6px', 'whiteSpace': 'normal'}
        ), html.Br(),
        html.Button('Add metrics', id = 'add-sens-mets', n_clicks = 0)
    ])

def choose_othermets():
    return html.Div([
        dcc.Input(id = 'other-mets-met', type = 'text', placeholder = 'Metric', size = '35'),
        html.Button('Add metric', id = 'add-other-mets', n_clicks = 0)
    ])