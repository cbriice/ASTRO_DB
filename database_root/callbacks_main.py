import dash, requests, h5py
from dash import dcc, html, Input, Output, State, ctx, ALL
from layouts import creategroup_layout, browsedb_layout, uploadmachine_layout, admin_layout, edit_db_layout, del_or_move
from backend_deep import add_data, add_group
from utils.constants import MAIN_MENU_OPS
from utils.helpers import ntng, get_keys
from layouts_graphinterface import graphmain_layout
from layouts_uploaddata import uploaddata_layout
from layouts_search import search_atts
from layouts_atts import att_main
from utils.constants import MASTER_FILE
from layouts_analysis import analysis_main
from flask import session, request
from utils.lock import master_lock
import h5rdmtoolbox as h5tbx

def register_main_callbacks(app):
    @app.callback(
    Output('main-content', 'children'),
    Input({'type': 'program-option', 'index': dash.ALL}, 'n_clicks')
    )
    def display_main_page(button_choice):                 
        trigg = ctx.triggered_id
        if not trigg:
            return html.H6("Click a button to start.", style = {'text-align': 'center'})
        
        choice = MAIN_MENU_OPS[int(trigg['index'])]
        #print(choice)
        if choice == MAIN_MENU_OPS[0]: return browsedb_layout()

        elif choice == MAIN_MENU_OPS[1]: return uploadmachine_layout()

        elif choice == MAIN_MENU_OPS[2]: return uploaddata_layout()

        elif choice == MAIN_MENU_OPS[3]: return att_main()

        elif choice == MAIN_MENU_OPS[4]: return edit_db_layout()

        elif choice == MAIN_MENU_OPS[5]: return search_atts()

        elif choice == MAIN_MENU_OPS[6]: return graphmain_layout()

        elif choice == MAIN_MENU_OPS[7]: return analysis_main()

        elif choice == MAIN_MENU_OPS[8]: return admin_layout()
        
        else:
            return "Idk what happened but we got here somehow"
    
#---------------------------------------------------edit database callbacks ---------------------------------
    @app.callback(
        Output('edit-db-container', 'children'),
        [Input('create-folder', 'n_clicks'),
         Input('del-or-move', 'n_clicks')]
    )
    def edit_db_landing(n1, n2):
        trigg = ctx.triggered_id
        if trigg is None:
            return ''
        
        if trigg == 'create-folder':
            return creategroup_layout()
        elif trigg == 'del-or-move':
            return del_or_move()

    @app.callback(
        Output('group-creation-output', 'children'),
        Input('submit-group-creation', 'n_clicks'),
        State('created-path', 'value'),
        State('created-name', 'value')
    )
    def handle_group_creation(n_clicks, path, name):
        if n_clicks == 0:
            return ""
        if not path or not name:
            return html.Span("WARNING: Location and name are required for group creation.", style = {'color': 'red'})
        
        try:
            created_file_address = add_group(MASTER_FILE, path, name)
            return html.Span(f'Group initialized at {created_file_address}.', style = {'color': 'green'})
        except Exception as e:
            return html.Span(f'Error initializing group: {e}', style = {'color': 'red'})
        
    #usually id make separate layout functions for the outputs of this callback but i dont want to rn so im not going to
    @app.callback(
        Output('edit-page-2', 'children'),
        [Input('move-sm', 'n_clicks'),
         Input('delete-sm', 'n_clicks')],
        State('address-to-edit', 'value')
    )
    def edit2(n1, n2, path):
        trigg = ctx.triggered_id
        if trigg is None:
            return ''
        
        if trigg == 'move-sm':
            with h5tbx.File(MASTER_FILE, 'r') as master:
                if path in master:
                    return html.Div([ html.Br(),
                        html.H6('Warning: you can mess things up very fast with "move data" if you\'re not careful with your addresses. Double check your typing!'),
                        html.Label('Enter address to move data to:'), html.Br(),
                        dcc.Input(id = 'new-location', type = 'text', placeholder = '/', size = '50'), html.Br(),
                        html.Button('Move', id = 'confirm-move', n_clicks= 0),
                        html.Div(id = 'move-confirmation')
                    ])
                else:
                    return html.Span(f'{path} not found in master file', style = {'color': 'red'})

        elif trigg == 'delete-sm':
            with h5tbx.File(MASTER_FILE, 'r') as master:
                if path in master:
                    return html.Div([ html.Br(),
                        html.Label(f'You are deleting {path}. This action cannot be undone. Are you sure?'), html.Br(),
                        html.Button('Delete', id = 'confirm-delete', n_clicks = 0, style = {'backgroundColor': "#e65757"}),
                        html.Button('Cancel', id = 'cancel-delete', n_clicks = 0), html.Br(),
                        html.Div(id = 'delete-confirmation')
                    ])
                else:
                    return html.Span(f'{path} not found in master file', style = {'color': 'red'})
        
    @app.callback(
        Output('delete-confirmation', 'children'),
        [Input('confirm-delete', 'n_clicks'),
         Input('cancel-delete', 'n_clicks')],
        State('address-to-edit', 'value')
    )
    def edit3(n1, n2, path):
        trigg = ctx.triggered_id
        if trigg is None:
            return ''
        
        if trigg == 'confirm-delete':
            with master_lock:
                with h5tbx.File(MASTER_FILE, 'a') as master:
                    del master[path]
            return html.Span(f'{path} permanently deleted from {MASTER_FILE}.')
        
        elif trigg == 'cancel-delete':
            return html.Span(f'Delete canceled. {path} lives to see another day')
        
    @app.callback(
        Output('move-confirmation', 'children'),
        Input('confirm-move', 'n_clicks'),
        State('new-location', 'value'),
        State('address-to-edit', 'value')
    )
    def edit4(n, new_path, old_path):
        if n == 0:
            return ''
        
        with master_lock:
            with h5tbx.File(MASTER_FILE, 'a') as master:
                if new_path in master:
                    try:
                        if isinstance(master[new_path], h5py.Dataset):
                            return html.Span(f'Move canceled. {new_path} is not a group')
                    except KeyError:
                        pass

                name = old_path.split('/')[-1]
                master.copy(source = master[old_path], dest = f'{new_path}/{name}')
                del master[old_path]

                if new_path in master:
                    return html.Span(f'Data at {old_path} successfully transferred to {new_path}', style = {'color': 'green'})
                else:
                    return html.Span(f'Data at {old_path} was unable to be copied to {new_path}', style = {'color': 'red'})

#-------------------------------------------------------------------------
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
#under "admin" tab, allow admin user to generate a bypass link. block if guest user
    @app.callback(
        Output('bypass-link-output', 'children'),
        Input('bypass-gen', 'n_clicks'),
        prevent_initial_call = True
    )
    def bypass_call(n):
        if session.get('user') == 'guest':
            return html.Span('This function is disabled for guest users', style = {'color': 'red'})
        
        if n == 0:
            return ''

        try:
            session_cookie = request.cookies.get('session')
            cookies = {'session': session_cookie} if session_cookie else {}
            response = requests.get('https://astrodatabase.online/generate-bypass', cookies = cookies, timeout = 5)
            resp_json = response.json()

            if 'bypass_url' in resp_json:
                url = resp_json.get('bypass_url')
                return html.Div([
                    html.Span('Bypass link (valid for 1 hour):'), html.Br(),
                    html.A(url, href = url, target = '_blank', id = 'bypass-link-anchor'), html.Br(),
                    dcc.Clipboard(
                        target_id = 'bypass-link-anchor', 
                        title = 'Copy',
                        style = {
                            'cursor': 'pointer',
                            'display': 'inline-block',
                            'marginTop': '5px',
                            'padding': '4px 8px',
                            'border': '1px solid #ccc',
                            'borderRadius': '5px',
                            'backgroundColor': "#d9ff96",
                            'color': '#333'
                        }
                    ),
                    html.Span('Click clipboard to copy.')
                ])
            
            elif 'error' in resp_json:
                return html.Span('Authentication error. Try re-logging in.', style={'color': 'red'})
            else:
                return html.Span(f'Failed to generate bypass: {response.text}', style = {'color': 'red'})
        except Exception as e:
            return html.Span(f'Request error: {e}', style = {'color': 'red'})