from utils.constants import MASTER_FILE, COLUMN_MAP_STANDARD
from dash import dcc, html, Input, Output, State, ctx
from utils.helpers import ntng, analysis_table
from layouts_analysis import load_storage
from utils.search_tools import conformance_comp
import plotly.graph_objects as go

'''
this how im tryna lay shit out:
when page pops up, option to load or clear storage. 2 options for storage to load - load first storage which would be the "model" build, and then
second storage would have the shit thats being compared to the model. idea is to make it easy to look at conformance

i think the stores will probably just have build addresses so then i can just load a preview of that build as i do in other tabs and give the user
the option to expand and look at specific things if they want. initially ill show list of stored builds once i load and then give checklist where the
user can choose how much information they want to see. 
    first level: conformance comparisons, attribute summaries, "compare datasets" option
    second level: show list of shared datasets organized by subgroup which user can choose to analyze further. 
'''

def register_analysis_callbacks(app):
    @app.callback(
        [Output('analysis-2', 'children'),
         Output('global-storage-1', 'data'),
         Output('global-storage-2', 'data'),
         Output('global-graph-storage', 'data', allow_duplicate= True)],
        [Input('load-storage', 'n_clicks'),
         Input('clear-storage', 'n_clicks')],
        State('global-storage-1', 'data'),
        State('global-storage-2', 'data'),
        State('global-graph-storage', 'data'),
        prevent_initial_call = True
    )
    def analysis_1(n1, n2, store1, store2, stored_plots):             #store1 is one path, store2 is a list of paths
        trigg = ctx.triggered_id
        if trigg is None or (n1 == 0 and n2 == 0):
            return '', ntng(), ntng(), ntng()
        
        if trigg == 'clear-storage':
            return html.Span('Storage cleared. Load data to analyze from search tab.'), None, [], []
        
        elif trigg == 'load-storage':
            if (store1 and store2) or stored_plots:
                return load_storage(store1, store2, stored_plots), ntng(), ntng(), ntng()
            else:
                return html.Span(f'Error: not enough data to load. 1: {store1} | 2: {store2} | 3: {stored_plots}'), ntng(), ntng(), ntng()

    @app.callback(
        Output('analysis-3', 'children'),
        Input('gen-comp-summary', 'n_clicks'),
        State('global-storage-1', 'data'),
        State('global-storage-2', 'data')
    )
    def analysis_2(n, stored1, store2):  #goes through list of items in store2 and compares attributes of each to item in store1. store1/2 are paths
        if n == 0:
            return ''
        
        if stored1 and store2:
            key_diffs = []
            normalized_diffs = []
            name_list = []
            store1 = stored1[0]
            name_1 = store1.split('/')[-1]

            for item in store2:
                complist, normalized = conformance_comp(store1, item, MASTER_FILE)    #complist is list of (key, %diff) from comparison target (store1)
                key_diffs.append(complist)
                normalized_diffs.append(normalized)
                name_list.append(item.split('/')[-1])

            tables = [analysis_table(comp, normalized_diffs[i]) for i, comp in enumerate(key_diffs)]
            formatted_tables = [
                html.Div([
                    html.Div([
                        html.Label(f'[{name_1}] vs [{name_list[i]}]'), html.Br(),
                        tables[i]
                    ]) for i in range(len(tables))  
                ], style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'gap': '50px',
                    'justifyContent': 'center'
                })
            ]

            return html.Div([
                html.Hr(),
                *formatted_tables, html.Br(),
                html.Button("Analyze datasets", id = 'analyze-datasets-button', n_clicks = 0), html.Br(),
                html.Div(id = 'analyze-datasets')
            ])
        else:
            return html.Span('Not enough data provided for comparison summary.', style = {'color': 'red'})
    #analysis - when user opens dataset up and explores items have program get min, max, avg values for specific data within dataset and display
    #that for all datasets user analyzing. or something idk

    @app.callback(
        Output('analysis-3-2', 'children'),
        Input('load-plots', 'n_clicks'),
        State('global-graph-storage', 'data')
    )
    def load_plots(n, global_plot_data):
        if n == 0:
            return ''
        
        if not global_plot_data:
            return html.Span('No plots stored.')
        
        plot_list = [item.get('figure') for item in global_plot_data]
        resized = []
        for fig in plot_list:
            fig = go.Figure(fig)
            fig.update_layout({
                'width': 700,
                'height': 500
            })
            resized.append(fig)
        source_list = [item.get('source') for item in global_plot_data]

        plots = [
            html.Div([
                html.H6(source_list[i]),
                dcc.Graph(id = f'stored-plot-{i}', figure = resized[i])
            ]) 
            for i in range(len(resized))
        ]

        return html.Div([
            html.Hr(), html.Br(),
            *plots 
        ], style = {
                'display': 'grid', 
                'gridTemplateColumns': '1fr 1fr',
                #'gap': '50px',
                'justifyContent': 'center'
            }
        )