from dash import dcc, html, Input, Output, State, ctx, MATCH
from utils.data_compiler import compile_atts, compile_plot, reconstruct_df, export_csv
from layouts_search import manual_search, search_all, search_autos, result_search, search_exsitu, search_insitu
import h5rdmtoolbox as h5tbx
from utils.search_tools import search_for_att, show_datasets
from utils.helpers import ntng
from utils.tools import process_data_for_preview
from layouts import display_data_info
from utils.constants import MASTER_FILE
import h5py
from cleaners.merged_df import merge_isd_mcd_md_df

def get_graph(dataset_name):    #little graph util function only for use in these callbacks
    graph = compile_plot(
        path = dataset_name,
        master_file = MASTER_FILE,
        dim = 2,
        target = dataset_name,
        metric = False,
        plot_all_from_df = False
    )
    graph.update_layout(width = 1000, height = 600)
    return dcc.Graph(figure = graph)

def try_process(path, master_file):
    try:
        stored_data, plottable = process_data_for_preview(path, master_file)
        return stored_data, plottable
    except TypeError:
        return '', False
    
#------------------------------ first section - browse database ------------------------------
def register_search_callbacks(app):
    #show details from browse database section
    @app.callback(
        [Output('details-bd', 'children'),
         Output('csv-download-link', 'children')],
        [Input('show-atts-bd', 'n_clicks'),
         Input('export-ds-csv', 'n_clicks'),
         Input('combine-and-export', 'n_clicks')],
        State('selected-path-store', 'data')
    )
    def iamsotired(n1, n2, n3, path):
        trigg = ctx.triggered_id
        if trigg is None:
            return '', ''
        
        if trigg == 'show-atts-bd':
            formatted_atts = compile_atts(path)
            stored_data, plottable = try_process(path, MASTER_FILE)
            if plottable:
                graph = get_graph(path)
            else:
                graph = ''
            
            return display_data_info(formatted_atts, stored_data, graph), ''
        
        #let user export data as csv
        elif trigg == 'export-ds-csv':
            if path is None:
                return html.Span("Don't do that"), ''
            
            with h5tbx.File(MASTER_FILE, 'r') as master:
                node = master[path]
                if isinstance(node, h5py.Dataset):
                    return '', html.Span("Can't export single dataset to a csv. Go back one layer and select the parent group of the dataset")
                if not any(isinstance(d, h5py.Dataset) for _, d in node.items()):
                    return '', html.Span(f"Can't export data at {path} to a csv, no datasets present", style = {'color': 'red'})
                
            df = reconstruct_df(path)
            split = path.split('/')
            filename = f'{split[-2]}-{split[-1]}.csv'
            redirect = export_csv(df, filename)
            link = html.A('Click to download CSV', href = redirect, target = '_blank')

            return html.Span(f'Data at {path} exported to {filename}', style = {'color': 'green'}), link
        
        #logic to combine files associated with a build and export them as a combined .csv for user to download
        elif trigg == 'combine-and-export':
            if path is None:
                return html.Span("Don't do that"), ''
            
            to_combine = []
            good = False
            try:
                with h5tbx.File(MASTER_FILE, 'r') as master:
                    node = master[path]
                    if not isinstance(node, h5py.Group):
                        return html.Span('Can only combine and export data from a build file.'), ''
                    if 'machine_data' not in node.keys():
                            return html.Span('Can only combine and export data from a build file.'), ''
                    
                    for name in node.keys():
                        #get things at node. decide if they are build files to be recombined
                        candidate_address = f'{path}/{name}'
                        candidate = master[candidate_address]   
                        print(f'Attempting to reconstruct data at {candidate_address}')

                        if isinstance(candidate, h5py.Group):
                            if 'build_id' in candidate.attrs:   #then we good
                                good = True
                                reconstructed = reconstruct_df(candidate_address)
                                if reconstructed is not None:
                                    print(f'Reconstructed data at {candidate_address}')
                                    to_combine.append(reconstructed)
                                else:
                                    print(f'Failed to reconstruct data at {candidate_address} . Skipping')

                if good:
                    print(f'Attempting to generate combined dataframe from data at {path} ...')
                    machine_df = None
                    isd_df = None
                    mcd_df = None
                    for df in to_combine:
                        if 'SpinVel' in df.columns:
                            if machine_df is None:
                                print(f'Machine file assigned')
                                machine_df = df
                        elif 'Force_1_Force' in df.columns:
                            if isd_df is None:
                                print(f'ISD file assigned')
                                isd_df = df
                            else:
                                print(f'Duplicate IN-SITU data file found at {path}. Using first one found')
                        else:
                            if mcd_df is None:
                                print(f'MCD file assigned')
                                mcd_df = df
                            else:
                                print(f'Duplicate MCD file found at {path}. Using first one found')

                    if machine_df is not None and isd_df is not None and mcd_df is not None:
                        try:
                            merged_df = merge_isd_mcd_md_df(isd_df, mcd_df, machine_df)
                            merged_filename = f"{path.split('/')[-1]}-merged.csv"
                            print(f'Successfully generated {merged_filename}')
                            redirect = export_csv(merged_df, merged_filename)
                        except Exception as e:
                            return html.Span(f'Error merging dataframes: {e}', style = {'color': 'red'}), ''
                        
                        link = html.A('Click to download merged CSV', href = redirect, target = '_blank')
                        return html.Span(f'Build files at {path} merged and exported to {merged_filename}', style = {'color': 'green'}), link

                    else:
                        missing = []
                        if mcd_df is None: missing.append('mcd')
                        if isd_df is None: missing.append('isd')
                        if machine_df is None: missing.append('machine')
                        return html.Span(f'Not enough valid files found at {path} to construct combined csv. Missing: {missing}', style = {'color': 'red'}), ''
                
                else:
                    return html.Span(f'Unable to process request: Files under this group are likely missing "build_id" attribute. Add this under "Add attributes"'), ''
                    
            except Exception as e:
                print(f'Failed to combine data: {e}')
                return html.Span(f'Failed to compile data from build at {path}. Check console', style = {'color': 'red'}), ''

        
    #------------------------------------------ search page section ------------------------
    @app.callback(
        Output('search-page-2', 'children'),
        Input('att-filt-input', 'value')
    )
    def searchpage2(choice):
        if choice == 'aa-machine':
            return search_autos()
        elif choice == 'manual-search': 
            return manual_search()
        elif choice == 'view-all-atts':
            return search_all()
        elif choice == 'exsitu-search':
            return search_exsitu()
        elif choice == 'insitu-search':
            return search_insitu()
        
    @app.callback(
        [Output('search-page-manual', 'children'),
         Output('results-manual', 'data')],
        Input('submit-manual-search', 'n_clicks'),
        State('att-search-input', 'value'),
        State('all-or-not-manual', 'value'),
        State('lower-bound-manual', 'value'),
        State('upper-bound-manual', 'value'),
        State('exact-value-manual', 'value'),
        State('non-numeric-manual', 'value')
    )
    def manual_search_callback(n, att, filter, lowerbound, upperbound, exactvalue, nonnumeric):
        if n == 0:
            return '', ntng()
        else:
            groupsonly = True if filter == 'show-all-manual' else False
            if nonnumeric is None:
                result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound, upperbound, exactvalue)
                stored = [(res.name, res.attrs) for res in result]
            else:
                result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound = None, upperbound = None, exactvalue = nonnumeric)
                stored = [(res.name, res.attrs) for res in result]

            if result:
                return result_search(result, att), stored
            else:
                return html.Div([
                html.Span('No results found. Try adjusting bounds?'), 
                html.Br(), 
                html.Span('Note: there\'s a bug here that idk how to fix - try choosing "Only show groups" even if you know your result will be a dataset.')]), ntng()
            
    @app.callback(
        [Output({'type': 'search-output', 'category': MATCH}, 'children'),
         Output({'type': 'search-results', 'category': MATCH}, 'data')],
        Input({'type': 'submit-search', 'category': MATCH}, 'n_clicks'),
        State({'type': 'dropdown-att', 'category': MATCH}, 'value'),
        State({'type': 'radio-group-filter', 'category': MATCH}, 'value'),
        State({'type': 'bound-lower', 'category': MATCH}, 'value'),
        State({'type': 'bound-upper', 'category': MATCH}, 'value'),
        State({'type': 'bound-exact', 'category': MATCH}, 'value'),
        State({'type': 'non-numeric', 'category': MATCH}, 'value'),
        prevent_initial_call=True
    )
    def search_callback(n, att, filter_mode, lowerbound, upperbound, exactvalue, nonnumeric):
        if n == 0 or att is None:
            return '', ntng()
        #if user puts shit in nonnumeric box, takes priority over everything else arbitrarily to avoid collisions between numeric/nonnumeric function
        if nonnumeric is None:
            groupsonly = 'builds' in filter_mode if filter_mode else False
            result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound, upperbound, exactvalue)
            stored = [(res.name, res.attrs) for res in result]
        else:
            groupsonly = 'builds' in filter_mode if filter_mode else False
            result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound = None, upperbound = None, exactvalue = nonnumeric)
            stored = [(res.name, res.attrs) for res in result]

        if result:
            return result_search(result, att), stored
        else:
            return html.Div([
                html.Span('No results found. Try adjusting bounds?'), 
                html.Br(), 
                html.Span('Note: there\'s a bug here that idk how to fix - try choosing "Only show groups" even if you know your result will be a dataset.')]), ntng()
            
    @app.callback(
        Output('expanded-results', 'children'),
        Input('show-details-ssa', 'n_clicks'),
        State('att-result-checklist' , 'value')
    )
    def show_details_manual(n, selected):
        if n == 0:
            return ''
        else:
            expanded = []
            for path in selected:
                expanded.append(compile_atts(path))
                expanded.append(show_datasets(path, MASTER_FILE))
            
            return expanded
        
    @app.callback(
        Output({'type': 'dataset-preview', 'group': MATCH}, 'children'),
        Input({'type': 'dataset-dropdown', 'group': MATCH}, 'value')
    )
    def load_preview(dataset_name):
        if not dataset_name:
            return ''
        atts = compile_atts(dataset_name)
        data, plottable = try_process(dataset_name, MASTER_FILE)
        if plottable:
            graph = get_graph(dataset_name)
        else:
            graph = ''
        return display_data_info(atts, data, graph)
    
    #logic to save shit for analysis tab
    @app.callback(
        [Output('analysis-save-status', 'children'),
         Output('global-storage-1', 'data', allow_duplicate= True),
         Output('global-storage-2', 'data', allow_duplicate= True)],
        [Input('save-for-analysis', 'n_clicks'),
         Input('set-as-bm', 'n_clicks')],
        State('att-result-checklist', 'value'),
        prevent_initial_call = True
    )
    def save_for_a(n1, n2, selected):
        trigg = ctx.triggered_id
        if n1 == n2 == 0:
            return ntng(), ntng(), ntng()
        
        if trigg == 'save-for-analysis':
            return html.Span('Selected data saved to global storage. Load in "Analyze data" tab.', style = {'color': 'green'}), ntng(), selected
        elif trigg == 'set-as-bm':
            if len(selected) > 1:
                return html.Span('Cannot set >1 item as benchmark for comparison. Try "Save all for analysis" or select a single item', style = {'color': 'red'}), ntng(), ntng()
            else:
                return html.Span('Selected data set as benchmark for comparison. Load in "Analyze data" tab.', style = {'color': 'green'}), selected, ntng()