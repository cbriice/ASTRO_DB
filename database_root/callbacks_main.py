import dash, base64, io
from dash import dcc, html, Input, Output, State, ctx, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from layouts import creategroup_layout, browsedb_layout, uploadmachine_layout
from backend_deep import add_data, add_group
from utils.constants import MAIN_MENU_OPS
from utils.helpers import ntng, get_keys, process_upload
from layouts_graphinterface import graphmain_layout
from layouts_uploaddata import uploaddata_layout
from layouts_search import search_atts
from layouts_atts import att_main
from utils.constants import MASTER_FILE
from layouts_analysis import analysis_main

def register_main_callbacks(app):
    @app.callback(
    Output('main-content', 'children'),
    Input({'type': 'program-option', 'index': dash.ALL}, 'n_clicks')
    )
    def display_main_page(button_choice):                 #return of this function maps to outputs. callback inputs map to function argument in order
        trigg = ctx.triggered_id
        if not trigg:
            return "Click a button to start."
        
        choice = MAIN_MENU_OPS[int(trigg['index'])]
        #print(choice)
        if choice == MAIN_MENU_OPS[0]:                  #browse dir
            return browsedb_layout()
        
        elif choice == MAIN_MENU_OPS[1]:                #graph interface
            return graphmain_layout()
        
        elif choice == MAIN_MENU_OPS[2]:                #filter by att
            return att_main()
        
        elif choice == MAIN_MENU_OPS[3]:                #search spec att
            return search_atts()
        
        elif choice == MAIN_MENU_OPS[4]:                #upload data
            return uploaddata_layout()
        
        elif choice == MAIN_MENU_OPS[5]:                #create group
            return creategroup_layout()
        
        elif choice == MAIN_MENU_OPS[6]:                #upload machine data
            return uploadmachine_layout()
        
        elif choice == MAIN_MENU_OPS[7]:
            return analysis_main()
        
        else:
            return "Idk what happened but we got here somehow"
    
#--------------------------------------------------------------------------

    @app.callback(
        Output('group-creation-output', 'children'),
        Input('submit-group-creation', 'n_clicks'),
        State('created-path', 'value'),
        State('created-name', 'value')
    )
    def handle_group_creation(n_clicks, path, name):
        if n_clicks == 0:
            return "Click submit once you've finished typing shit in."
        if not path or not name:
            return html.Span("WARNING: File location and filename are required for group creation.", style = {'color': 'red'})
        
        try:
            created_file_address = add_group(MASTER_FILE, path, name)
            return html.Span(f'Group initialized at {created_file_address}.', style = {'color': 'green'})
        except Exception as e:
            return html.Span(f'Error initializing group: {e}', style = {'color': 'red'})
#--------------------------------------------------------------------------
#callbacks for dynamic dropdowns
#   first - add new dropdown when user selects from previous
    @app.callback(
        Output('dropdown-container', 'children'),
        Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
        State('dropdown-container', 'children')
    )
    def new_dropdown(selected_values, existing_dropdowns):
        trigg = ctx.triggered_id
        if trigg is None:
            return existing_dropdowns
        
        trigg_idx = trigg['index']
        trimmed_dropdowns = existing_dropdowns[:trigg_idx + 1]
        curr_path = selected_values[trigg_idx]

        sub_keys = get_keys(curr_path, MASTER_FILE)
        if not sub_keys:
            return trimmed_dropdowns
        
        new_dropdown = dcc.Dropdown(
            id = {'type': 'dynamic-dropdown', 'index': trigg_idx + 1},
            options = sub_keys,
            placeholder = f'Select from {curr_path}'
        )
        return trimmed_dropdowns + [new_dropdown]
        
#   next - update selected path
    @app.callback(
        [Output('end-of-chain', 'children'),
         Output('selected-path', 'children'),
         Output('selected-path-store', 'data')],
        Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value')
    )
    def update_selected(selected_values):
        selected_values = [val for val in selected_values if val is not None]

        if not selected_values:
            return '', '', ntng()
        
        full_path = selected_values[-1]
        return '', full_path, full_path
#--------------------------------------------------------------------------

    
#--------------------------------------------------------------------------