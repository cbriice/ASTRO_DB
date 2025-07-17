from dash import dcc, html, Input, Output, State, ctx, ALL
import layouts_graphinterface as lgi
from utils.helpers import ntng, get_keys, verify_existence, verify_stack, display_stack, generate_dset_list
from utils.data_compiler import compile_plot, compile_stacked_plots
from utils.tools import decode_color_att
import plotly.graph_objects as go
import utils.plot_tools as pt
from utils.constants import MASTER_FILE

#----- global plot cache to make plot all case logic more efficient -----
import uuid, time
from threading import Lock

plot_cache = {}
cache_lock = Lock()
CACHE_TL = 60 * 5

def set_plot_cache(data):
    key = str(uuid.uuid4())
    with cache_lock:
        plot_cache[key] = (time.time(), data)
    return key

def get_plot_cache(key):
    with cache_lock:
        val = plot_cache.get(key)
        if val:
            t, data = val
            if time.time() - t < CACHE_TL:
                return data
            else:
                del plot_cache[key]
        return None

#----------------- callback logic -----------------------
def update_global(global_storage, stored_plots):
    if not stored_plots:
        return global_storage or []

    global_copy = global_storage.copy() if global_storage else []

    sources_existing = {item.get('source') for item in global_copy}

    for item in stored_plots:
        source = item.get('source')
        if source and source not in sources_existing:
            global_copy.append(item)
            sources_existing.add(source)  #track as you go

    return global_copy

def register_graph_callbacks(app):
    #graphmain_layout
    @app.callback(
        Output('graph-page-2', 'children'),
        Input('confirm-stacked', 'n_clicks'),
        State('stacked-or-not', 'value')
    )
    def graph_page1(n, stacked):
        if n == 0:
            return ""
        else:
            if stacked == 'stacked':
                return lgi.graphmain_stacked()
            else:
                return lgi.graphmain_individual()
   
   #---------------------------------------------------------------- not stacked case
   #graphmain_individual submit path here
    @app.callback(
        [Output('graph-target-ops', 'data'),
         Output('graph-path-confirm', 'children'),
         Output('graph-path', 'data'),
         Output('graph-page-3', 'children')],
        Input('submit-ind-graph-path', 'n_clicks'),
        State('data-path', 'value')
    )
    def take_path(n_clicks, path):
        if n_clicks == 0:
            return "", "", "", ""
        else:
            verification, yes = verify_existence(path)
            if yes:
                ops = get_keys(path, MASTER_FILE)
                if not ops:
                    n = path.split('/')[-1]
                    ops = {n: n}
                    return ops, verification, path, lgi.dummy_decide_plotall()
                return ops, verification, path, lgi.decide_plotall()
            else:
                return "", verification, "", ""
    
    #decide_plotall decide if plotting all valid or just targets
    @app.callback(
        Output('graph-page-4', 'children'),
        Input('submit-plot-all', 'n_clicks'),
        State('plot-all-from-df', 'value'),
        State('graph-target-ops', 'data')
    )
    def smh(n, to_plot, target_ops):
        if n == 0:
            return ntng()
        else:
            if to_plot == 'plot-single':
                return lgi.info_not_plotall(target_ops)
            else:
                return lgi.info_plotall()
    
    #dummy options to make thing idiot proof
    @app.callback(
        Output('dummy-graph-page-4', 'children'),
        Input('dummy-submit-plot-all', 'n_clicks'),
        State('graph-target-ops', 'data')
    )
    def dummy(n, target_ops):
        if n == 0:
            return ""
        else:
            return lgi.info_not_plotall(target_ops)
    
    #------------------------------------ "plot all from dataset" case
    #info_plotall
    @app.callback(
        [Output('graph-page-5', 'children'),
         Output('pa-plot-list', 'data')],
        Input('submit-all-graph-data', 'n_clicks'),
        State('graph-dim-pa', 'value'),
        State('metric-pa', 'value'),
        State('graph-path', 'data'),
        prevent_initial_call = True
    )
    def handle_plotall(n, dim, metric, path):
        #print(path)
        if n == 0:
            return "", ntng()
        else:
            metric_b = True if metric == 'metric-true' else False
        #because of previous ui selections, this is guaranteed to return a list of either 2d or 3d plots of all plottable data from one dataframe. -> no target arg
            plots = compile_plot(           
                path = path, 
                master_file = MASTER_FILE, 
                dim = int(dim), 
                target = None,
                metric = metric_b, 
                plot_all_from_df = True
            )
            plot_dict = {}
            dict_to_store = {}
            for i, (name, plot) in enumerate(plots):
                if plot is None or not hasattr(plot, 'to_dict'):
                    print(f'Skipping invalid plot for {name}: {type(plot)}')
                    continue
                plot_dict[name] = dcc.Graph(id = f'plot{i}', figure = plot)
                dict_to_store[name] = {
                    'figure': plot.to_dict(),
                    'source': f'{name}'
                }
            
            if not plots or not isinstance(plots, list):
                print(f'No valid plots in {plots}')
                return "", {}
            
            session_key = set_plot_cache(dict_to_store)
            return lgi.show_plotall(plot_dict), {'session_id': session_key}

    #show_plotall triggered by submit button, shows graphs from checklist --------------------------------
    @app.callback(
        [Output('pa-plot-output', 'children'),
         Output('generated-plots', 'data', allow_duplicate= True)],
        Input('submit-pa-graph-choices', 'n_clicks'),
        State('pa-plot-list', 'data'),
        State('pa-plot-selector', 'value'),
        State('generated-plots', 'data'),
        prevent_initial_call = True
    )
    def show_pa_plots(n, plot_dict, selected_plots, stored_plots):
        if not plot_dict or not selected_plots:
            return html.Span('No selection was made, nothing to display', style = {'color': 'gray'}), ntng()
        
        graphs = []
        active_plots = []
        for i, plt in enumerate(selected_plots):
            session_id = plot_dict.get('session_id')
            plot_data_dict = get_plot_cache(session_id)
            if not plot_data_dict:
                return html.Span('Session expired or invalid'), ntng()
            
            if plt in plot_data_dict:
                fig_data = plot_data_dict[plt]
                if isinstance(fig_data, dict) and 'figure' in fig_data:
                    fig = go.Figure(fig_data['figure']) if isinstance(fig_data['figure'], dict) else fig_data['figure']
                    source = fig_data.get('source', 'Unknown')
                else:
                    fig = go.Figure(fig_data)
                    source = 'Unknown'
                graphs.append(
                    html.Div([
                        dcc.Graph(
                            id = f'plot-{i}', 
                            figure = fig,
                            style = {'width': '100%', 'maxWidth': 'none'}
                        )]
                    ))
                #update generated-graphs with all plots user has generated. new ones every time user generates from checklist
                active_plots.append({
                    'figure': fig.to_dict(),
                    'source': source
                })
                print(f'Processed plot for {source} (pa)')
                plots_toupdate = update_global(stored_plots, active_plots) #confusing function name but its the same general logic so reused it

        plot_div = html.Div(graphs, style = {'display': 'grid', 'gridTemplateColumns': '1fr 1fr'})
        return lgi.display_plots(plot_div), plots_toupdate

    #---------------------------------- "plot single dataset" case
    #info_not_plotall
    @app.callback(
        [Output('npa-graph-output', 'children'),
         Output('color-axis-shit', 'children'),
         Output('npa-stored-plots', 'data'),
         Output('generated-plots', 'data', allow_duplicate= True)],
        Input('submit-ind-graph-data', 'n_clicks'),
        State('target-ind-npa', 'value'),
        State('graph-dim-npa', 'value'),
        State('metric-npa', 'value'),
        State('graph-path', 'data'),
        State('generated-plots', 'data'),
        prevent_initial_call = True
    )
    def these_names_dont_matter(n, target, dim, metric, path, stored_plots):
        if n == 0:
            return html.Div(), html.Div(), None, ntng()
        else:
            metric_b = True if metric == 'metric-true' else False
            plot = compile_plot(
                path = path,
                master_file = MASTER_FILE,
                dim = int(dim),
                target = target,
                metric = metric_b,
                plot_all_from_df = False
            )
            if isinstance(plot, list):
                if len(plot) == 1:
                    plot = plot[0][1]
                else:
                    print(f'[ERROR] Got multiple plots in single-plot path. {plot}')
                    return html.Div("Invalid result: expected one plot", style = {'color': 'red'}), html.Div(), None, ntng()
                
            plot.update_layout(autosize = False, width = 1500, height = 800)
            graph = html.Div([dcc.Graph(id = f'plot-0', figure = plot)])

            stored_copy = stored_plots.copy() if stored_plots else []
            stored_copy.append({
                'figure': plot.to_dict(),
                'source': f'{target} ({dim}D)'
            })
            print(f'Processed {dim}D plot for {target} (npa)')

            if int(dim) == 2:
                plot_div = html.Div(graph, style = {'display': 'grid', 'gridTemplateColumns': '1fr 1fr'})
                return lgi.display_plots(plot_div), html.Div(), None, stored_copy
            
            else:
                plot_div = html.Div(graph, style = {'display': 'grid', 'gridTemplateColumns': '1fr 1fr'})
                return lgi.display_plots(plot_div), lgi.color_adjust(), plot, stored_copy

    #color scale adjustment callback
    @app.callback(
        [Output('new-scale-3d-plot', 'children'),
         Output('generated-plots', 'data', allow_duplicate= True)],
        Input('submit-color-scale', 'n_clicks'),
        State('color-min', 'value'),
        State('color-max', 'value'),
        State('npa-stored-plots', 'data'),
        State('generated-plots', 'data'),
        State('graph-path', 'data'),
        prevent_initial_call = True
    )
    def dddd(n, cmin, cmax, plot, stored_plots, path):
        if n == 0:
            return "", ntng()
        else:
            fig = decode_color_att(plot)
            for trace in fig.data:
                if hasattr(trace, 'marker') and hasattr(trace.marker, 'color'):
                    trace.marker.cmin = cmin
                    trace.marker.cmax = cmax
            fig.update_layout(coloraxis = dict(cmin = cmin, cmax = cmax))

            plot_div = html.Div([
                html.Br(),
                html.H5('Adjusted graph'),
                dcc.Graph(id = f'plot-1', figure = fig)
            ])

            stored_copy = stored_plots.copy() if stored_plots else []
            stored_copy = [item for item in stored_copy if path not in item.get('source', '')]

            stored_copy.append({
                'figure': fig.to_dict(),
                'source': path
            })

            return lgi.display_plots(plot_div), stored_copy

    #------------------------------------------------------------------------------------------------------ stacked case
    #initial stacker page
    @app.callback(
        [Output('stackers', 'data'),
         Output('status-stackers', 'children'),
         Output('stacker-current-list', 'children')],
        [Input('save-stacker', 'n_clicks'),
         Input('clear-stackers', 'n_clicks')],
        State('stackers', 'data'),
        State('stack-addy-input', 'value'),
        prevent_initial_call = True
    )
    def stacker1(n1, n2, stackerlist, stack_addy):
        trigg = ctx.triggered_id

        if trigg == 'save-stacker':
            validation, check = verify_stack(stack_addy, stackerlist)
            update = stackerlist.copy()

            if check:
                update.append(stack_addy)
                return update, validation, display_stack(update)
            else:
                return ntng(), validation, display_stack(update)
        
        elif trigg == 'clear-stackers':
            return [], 'List of plots to stack cleared.', ''
        
        else:
            return ntng(), ntng(), ntng()
    

    @app.callback(
        [Output('stacked-plot', 'children'),
         Output('generated-plots', 'data', allow_duplicate= True)],
        Input('submit-stackers', 'n_clicks'),
        State('stackers', 'data'),
        State('generated-plots', 'data'),
        prevent_initial_call = True
    )
    def show_stack(n, stack, stored_plots):
        if n == 0:
            return "", ntng()
        else:
            normalized_times = pt.normalize_times(stack)
            plots, fig = compile_stacked_plots(stack, normalized_times)
            stored_copy = stored_plots.copy() if stored_plots else []
            stack_string = f''
            for s in stack:
                stack_string = stack_string + f'{s} || '

            stored_copy.append({
                'figure': fig.to_dict(),
                'source': stack_string
            })
            print(f'Processed stacked plot for {stack_string}')

            return lgi.display_plots(plots), stored_copy
        
    #--------- send to storage
    @app.callback(
        [Output('global-graph-storage', 'data'),
         Output('store-plot-status', 'children'),
         Output('generated-plots', 'data', allow_duplicate= True)],
        Input('store-plot', 'n_clicks'),
        State('generated-plots', 'data'),
        State('global-graph-storage', 'data'),
        prevent_initial_call = True
    )
    def store_callback(n, stored_plots, global_storage):
        if n == 0:
            return ntng(), ntng(), ntng()
        
        global_copy = update_global(global_storage, stored_plots)
            
        return global_copy, html.Span('Plot stored globally. Load in "Analyze data" tab', style = {'color': 'green'}), []