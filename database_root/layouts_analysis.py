from dash import dcc, html
from utils.constants import MASTER_FILE

def analysis_main():
    return html.Div([
        html.H4('Comparison/analysis page', style = {'text-align': 'center'}), html.Br(),
        html.Div([
            html.Div([
                html.Button('Load storage', id = 'load-storage', n_clicks = 0, style = {'backgroundColor': "#40b8fd"}),
                html.Button('Clear storage', id = 'clear-storage', n_clicks = 0), html.Br(), html.Br()
            ], style = {'padding-left': '800px'}),
            html.Div(id = 'analysis-2')
        ], style = {'padding-left': '50px', 'padding-right': '50px'})
    ])

def load_storage(path1, paths2):
    return html.Div([
        html.H6('Benchmark data:'), 
        html.Ul([path1]), html.Br(),
        html.H6('Comparison data:'),
        html.Ul([html.Li(item) for item in paths2]), html.Br(),
        html.Button('Generate comparison summary', id = 'gen-comp-summary', n_clicks = 0), html.Br(),
        html.Div(id = 'analysis-3')
    ])

