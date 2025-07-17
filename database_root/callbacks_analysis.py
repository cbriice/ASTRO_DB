from utils.constants import MASTER_FILE, FORCE_METS, TC_METS, HTHFS_METS, LTHFS_METS
from dash import dcc, html, Input, Output, State, ctx, ALL
from utils.helpers import ntng, analysis_table
import layouts_analysis as la
from utils.search_tools import conformance_comp
import plotly.graph_objects as go
import h5rdmtoolbox as h5tbx

def register_analysis_callbacks(app):
    @app.callback(
        [Output('analysis-2', 'children'),
         Output('global-storage-1', 'data'),
         Output('global-storage-2', 'data'),
         Output('global-graph-storage', 'data', allow_duplicate= True)],
        [Input('load-storage', 'n_clicks'),
         Input('clear-storage', 'n_clicks'),
         Input('custom-benchmark', 'n_clicks')],
        State('global-storage-1', 'data'),
        State('global-storage-2', 'data'),
        State('global-graph-storage', 'data'),
        prevent_initial_call = True
    )
    def analysis_1(n1, n2, n3, store1, store2, stored_plots):             #store1 is one path, store2 is a list of paths
        trigg = ctx.triggered_id
        if trigg is None or (n1 == 0 and n2 == 0 and n3 == 0):
            return '', ntng(), ntng(), ntng()
        
        if trigg == 'clear-storage':
            return html.Span('Storage cleared. Load data to analyze from search tab.'), None, [], []
        
        elif trigg == 'load-storage':
            if store1 or store2 or stored_plots:
                return la.load_storage(store1, store2, stored_plots), ntng(), ntng(), ntng()
            else:
                return html.Span(f'Error: not enough data to load. 1: {store1} | 2: {store2} | 3: {stored_plots}'), ntng(), ntng(), ntng()
        
        elif trigg == 'custom-benchmark':
            return la.custom_benchmark1(), ntng(), ntng(), ntng()

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

            if isinstance(stored1, list):
                store1 = stored1[0]
                name_1 = store1.split('/')[-1]
            else:
                store1 = stored1
                name_1 = 'Custom benchmark'

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
            if all(trace.type == 'scatter' and trace.mode == 'lines' for trace in fig.data) and len(fig.data) > 1:  #then its a stacked plot, needs custom width
                fig.update_layout({'width': 1000, 'height': 500})
            else:
                fig.update_layout({'width': 700, 'height': 500})
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
    
    #-------------custom benchmark creator callbacks--------------
    @app.callback(
        Output('custom-bench-1', 'children'),
        Input('choose-met-bench', 'value')
    )
    def bench1(dd):
        if dd is None:
            return ''
        if dd == 'mach-mets':
            return la.choose_machmets()
        elif dd == 'sens-mets':
            return la.choose_sensorcat()
        elif dd == 'other-mets':
            return la.choose_othermets()
    
    @app.callback(
        Output('sensor-checklist', 'children'),
        Input('choose-sensor-cat', 'value')
    )
    def sencheck(cat):
        if cat is None:
            return ''
        if cat == 'force': return la.choose_sensormets(FORCE_METS)
        elif cat == 'hthfs': return la.choose_sensormets(HTHFS_METS)
        elif cat == 'lthfs': return la.choose_sensormets(LTHFS_METS)
        elif cat == 'therms': return la.choose_sensormets(TC_METS)
        
    #manually entered
    @app.callback(
        [Output('other-mets-store', 'data', allow_duplicate=True),
         Output('custom-bench-2', 'children', allow_duplicate=True)],
        Input('add-other-mets', 'n_clicks'),
        State('other-mets-met', 'value'),
        prevent_initial_call=True
    )
    def store_other(n, val):
        if n == 0:
            return ntng(), ''
        return ([val] if val else []), f'Stored: {val}'
    
    #machine ops
    @app.callback(
        [Output('machine-mets-store', 'data', allow_duplicate=True),
         Output('custom-bench-2', 'children', allow_duplicate=True)],
        Input('add-mach-mets', 'n_clicks'),
        State('machinefile-mets-select', 'value'),
        prevent_initial_call=True
    )
    def store_machine(n, selected):
        if n == 0: 
            return ntng(), ''
        return (selected or []), f'Stored: {selected}'
    
    #sensor
    @app.callback(
        [Output('sensor-mets-store', 'data', allow_duplicate=True),
         Output('custom-bench-2', 'children', allow_duplicate=True)],
        Input('add-sens-mets', 'n_clicks'),
        State('sensorfile-mets-select', 'value'),
        prevent_initial_call=True
    )
    def store_sensor(n, selected):
        if n == 0:
            return ntng(), ''
        return (selected or []), f'Stored: {selected}'
    
    #combine
    @app.callback(
        Output('benchmark-mets', 'data'),
        Input('machine-mets-store', 'data'),
        Input('sensor-mets-store', 'data'),
        Input('other-mets-store', 'data')
    )
    def combine_mets(machine, sensor, other):
        combined = (machine or []) + (sensor or []) + (other or [])
        return list(dict.fromkeys(combined))
    
    #clear selection 
    @app.callback(
        [Output('benchmark-mets', 'data', allow_duplicate=True),
         Output('machine-mets-store', 'data', allow_duplicate=True),
         Output('sensor-mets-store', 'data', allow_duplicate=True),
         Output('other-mets-store', 'data', allow_duplicate=True),
         Output('custom-bench-2', 'children', allow_duplicate=True),
         Output('custom-bench-3', 'children', allow_duplicate=True)],
        Input('clear-custom-bench', 'n_clicks'),
        prevent_initial_call=True
    )
    def clear_metrics(n):
        if n == 0:
            return ntng(), ntng(), ntng(), ntng(), '', ''
        else:
            return [], [], [], [], html.Span('Cleared stored metrics.'), ''
    
    #---now get values for metrics stored---
    @app.callback(
        Output('custom-bench-3', 'children'),
        Input('submit-custom-metrics', 'n_clicks'),
        State('benchmark-mets', 'data'),
        prevent_initial_call=True
    )
    def show_input_fields(n, metrics):
        if not metrics:
            return html.Span("No metrics selected.")
        
        metrics = sorted(metrics)
        inputs = [
            html.Div([
                html.Label(f"{m}: "),
                html.Div(dcc.Input(id={'type': 'custom-bench-input', 'index': m}, type='text', placeholder='value'), style = {'marginLeft': '20px'})
            ], style={'marginBottom': '10px'})
            for m in metrics
        ]
        inputs.append(html.Button('Submit benchmark values', id='submit-custom-values', n_clicks=0, style = {'backgroundColor': "#acf879"}))
        return inputs
    
    @app.callback(
        [Output('custom-benchmark-container', 'data'),
         Output('global-storage-1', 'data', allow_duplicate = True),
         Output('custom-bench-4', 'children')],
        Input('submit-custom-values', 'n_clicks'),
        State('benchmark-mets', 'data'),
        State({'type': 'custom-bench-input', 'index': ALL}, 'value'),
        prevent_initial_call=True
    )
    def store_final_benchmark(n, metrics, values):
        if not metrics or not values:
            return {}, ntng(), ''
        if n == 0:
            return {}, ntng(), ''
        
        met_dict = {m: float(v) for m, v in zip(metrics, values)}
        return met_dict, met_dict, html.Span(f'Stored {met_dict} to global benchmark storage for comparison. Ready for loading')
    
    #----------searching within analysis tab------------
    from utils.search_tools import search_for_att
    
    @app.callback(
        Output('benchmark-search-results', 'children'),
        Input('search-custom-benchmark', 'n_clicks'),
        State('custom-benchmark-container', 'data'),
        State('norm-threshold', 'value'),            #add layout - button, input for threshold of normalized
        prevent_initial_call=True
    )
    def search_db_with_benchmark(n, custom_bench, tolerance):
        if n == 0:
            return ''
        
        if not custom_bench:
            return html.Span('No custom benchmark provided.', style={'color': 'red'})
        
        tolerance = tolerance or 10     #default tolerance of 10%

        #assign tolerance values
        upper_dict = {}
        lower_dict = {}
        key_list = []
        for key, val in custom_bench.items():
            lower_dict[key] = val - val * (tolerance / 100)
            upper_dict[key] = val + val * (tolerance / 100)
            key_list.append(key)
        
        #get a list of result lists, where each result list corresponds to builds which have the att key within the given range
        results = []
        for key in key_list:
            results.append(search_for_att(MASTER_FILE, key, False, lower_dict[key], upper_dict[key], None))
        
        if not results: return html.Span('No results found', style = {'textAlign': 'center'})
        
        #need to find results which are present in every list
        results_names = [set(res.name for res in result_list) for result_list in results]
        common_names = set.intersection(*results_names)
        all_results_flat = {res.name: res for sublist in results for res in sublist}
        results_cleaned = [all_results_flat[name] for name in common_names]

        if not results_cleaned: return html.Span('No results found', style = {'textAlign': 'center'})

        #generate and format tables
        rendered = []
        name_1 = 'Custom benchmark'
        for res in results_cleaned:
            diffs, norm = conformance_comp(custom_bench, res.name, MASTER_FILE)
            table = analysis_table(diffs, norm)
            name_2 = res.name.split('/')[-1]
            rendered.append(html.Div([
                html.Label(f'[{name_1}] vs [{name_2}]'),
                table
            ]))

        return html.Div([
            html.Span(f'Found {len(results_cleaned)} result(s) with metrics within {tolerance}% of the custom benchmark'), html.Br(),
            html.Hr(),
            html.Div(rendered, style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'gap': '50px',
                'justifyContent': 'center'
            }),
            html.Br()
        ])