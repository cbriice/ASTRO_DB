from dash import dcc, html
from utils.constants import METRICS_MACHINEFILE, FORCE_METS, LTHFS_METS, HTHFS_METS, TC_METS

def analysis_main():
    return html.Div([
        html.H4('Comparison/analysis page', style = {'text-align': 'center'}), html.Br(),
        html.Div([
            html.Div([
                html.Button('Load storage', id = 'load-storage', n_clicks = 0, style = {'backgroundColor': "#40b8fd"}),
                html.Button('Clear storage', id = 'clear-storage', n_clicks = 0), 
                html.Button('Create custom benchmark', id = 'custom-benchmark', n_clicks = 0), html.Br(), html.Br()
            ], style = {'padding-left': '750px'}),
            html.Div(id = 'analysis-2')
        ], style = {'padding-left': '50px', 'padding-right': '50px', 'padding-bottom': '50px'})
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
        html.Ul([path1 if path1 else 'No data']),
        html.H6('Comparison data:'),
        html.Ul(paths2_list), 
        html.H6('Stored plots:'),
        html.Ul(stored_sources), html.Br(),
        html.Button('Generate comparison summary', id = 'gen-comp-summary', n_clicks = 0), 
        html.Button('Load graphs', id = 'load-plots', n_clicks = 0),
        html.Br(),
        html.Div(id = 'analysis-3'),
        html.Div(id = 'analysis-3-2')
    ])

def custom_benchmark1():
    return html.Div([
        html.H6('Choose metrics to add to custom benchmark:'), html.Br(),
        dcc.Dropdown(
            id = 'choose-met-bench', 
            options = [{'label': 'Machine file metrics', 'value': 'mach-mets'},
                       {'label': ''}] 
        )
    ])

def custom_benchmark2():
    return html.Div([
        html.Label('Machine file metrics'), html.Br(),
        dcc.Checklist(
            id = 'machinefile-mets-select', 
            options = [{'label': m, 'value': m} for m in METRICS_MACHINEFILE],
            labelStyle = {'width': '10%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '1px'}
        ), html.Br()
    ])

def custom_benchmark_sensorops(i, ops):
    return html.Div([
        html.Label('Sensor file metrics'), html.Br(),
        dcc.Checklist(
            id = f'sensorfile-mets-select-{i}', 
            options = [{'label': m, 'value': m} for m in ops],
            labelStyle = {'width': '10%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '1px'}
        )
    ])