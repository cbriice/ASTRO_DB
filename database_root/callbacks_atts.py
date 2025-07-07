from dash import Input, Output, State, html, dcc, ctx, MATCH, ALL
from utils.constants import MASTER_FILE, ATT_CATEGORIES_HIGHEST, ALL_ATT_SUBCATEGORIES, EXSITU_KEYS, ATT_SUB_EXSITU, ATT_SUB_BUILD, BUILD_KEYS
import h5rdmtoolbox as h5tbx
from utils.helpers import ntng
from layouts_atts import att_second, show_curr_atts, add_att, att_dropdown, type_of_att, enter_att1, enter_att2, enter_any
from utils.search_tools import add_attribute

def register_att_callbacks(app):
    @app.callback(
        [Output('att-page-2', 'children'),
         Output('user-address', 'data')],
        Input('pull-address-att', 'n_clicks'),
        State('att-address', 'value')
    )
    def att_first(n, address):
        if n == 0: 
            return '', ntng()
        else:
            with h5tbx.File(MASTER_FILE, 'r') as master:
                if address not in master:
                    return html.Span(f'{address} not found in {MASTER_FILE}', style = {'color': 'red'}), ntng()
                
            return att_second(), address
        
    @app.callback(
        [Output('curr-atts-page', 'children'),
         Output('att-page-3', 'children')],
        [Input('show-curr-atts', 'n_clicks'),
         Input('hide-curr-atts', 'n_clicks')],
        State('user-address', 'data')
    )
    def att_2(n1, n2, path):
        trigg = ctx.triggered_id
        if n1 == 0 and n2 == 0:
            return '', add_att()
        
        if trigg == 'show-curr-atts':
            return show_curr_atts(path), ntng()
        elif trigg == 'hide-curr-atts':
            return '', ntng()
        
    @app.callback(
        Output('next-att-dropdown', 'children'),
        Input({'type': 'dropdown', 'stage': 'category'}, 'value'),
        prevent_initial_call = True
    )
    def att_3(category):
        if category == 'Other':
            return enter_any()
        for i in range(len(ATT_CATEGORIES_HIGHEST)):
            if category == ATT_CATEGORIES_HIGHEST[i]:
                if category != 'Manually add':
                    return att_dropdown(ALL_ATT_SUBCATEGORIES[i], 'subcategory')
                else:
                    return enter_any()
            
    @app.callback(
        Output('next-next-att-dropdown', 'children'),
        Input({'type': 'dropdown', 'stage': 'subcategory'}, 'value')
    )
    def att_4(subcat):
        if subcat in ATT_SUB_EXSITU:
            i = ATT_SUB_EXSITU.index(subcat)
            return att_dropdown(EXSITU_KEYS[i], 'final')
        elif subcat in ATT_SUB_BUILD:
            i = ATT_SUB_BUILD.index(subcat)
            return att_dropdown(BUILD_KEYS[i], 'final')
        else:
            return ntng()
        
    @app.callback(
        [Output('num-or-text-container', 'children'),
         Output('att-key', 'data', allow_duplicate = True)],
        Input({'type': 'dropdown', 'stage': 'final'}, 'value'),
        prevent_initial_call = True        
    )
    def cooked_asf(key):
        if key is None:
            return ntng(), ntng()
        return type_of_att(), key
    
    @app.callback(
        Output('enter-att', 'children'),
        Input('num-or-text-atts', 'value')
    )
    def att_5(choice):
        if choice is None:
            return ntng()
        elif choice == 'num':
            return enter_att2()
        else:
            return enter_att1()
        
    @app.callback(
        Output({'type': 'att-status', 'method': MATCH}, 'children'),
        Input({'type': 'submit-att', 'method': MATCH}, 'n_clicks'),
        State('user-address', 'data'),
        State({'type': 'att-input', 'method': MATCH}, 'value'),
        State('att-key', 'data'),
        prevent_initial_call = True
    )
    def att_6(n, path, value, key):
        if n == 0:
            return ntng()
        if value is None:
            return html.Span('How tf u get through all those dropdowns and not even put anything in the input box?', style = {'color': 'red'})
        success = add_attribute(path, key, value, MASTER_FILE)
        if success:
            return html.Span(f'Tagged {path} with "{key}: {value}"', style = {'color': 'green'})
        else:
            return html.Span(f'Failed to tag {path} with "{key}: {value}"', style = {'color': 'red'})
        
    @app.callback(
        [Output('att-other-continuation', 'children'),
         Output('att-key', 'data', allow_duplicate = True)],
        Input('confirm-name-other', 'n_clicks'),
        State('att-name-other', 'value'),
        prevent_initial_call = True
    )
    def att_7(n, key):
        if n == 0:
            return ntng(), ntng()
        else:
            if key:
                return type_of_att(), key
            else:
                return html.Span('need input bro', style = {'color': 'red'}), ntng()