from dash import dcc, html
import dash_bootstrap_components as dbc
from utils.helpers import get_all_att_keys
from utils.constants import METRICS_MACHINEFILE, EXSITU_KEYS

def dropdown_search_layouts(category, ops = None):
    if category == 'all' or category == 'autos' or category == 'exsitu': #dropdown layouts
        return html.Div([
        html.H6('Choose an attribute to search for:'), 
        dcc.Dropdown(
            id = {'type': 'dropdown-att', 'category': category},
            options = [{'label': key, 'value': key} for key in ops],
            placeholder = 'Select'
        ), html.Br(),

        dcc.RadioItems(
            id = {'type': 'radio-group-filter', 'category': category},
            options = [
                {'label': 'Show all results', 'value': f'show-all-{category}'},
                {'label': 'Only show groups', 'value': f'show-builds-{category}'}
            ]
        ), html.Br(),

        html.Label('Lower bound?'), html.Br(), 
        dcc.Input(
            id = {'type': 'bound-lower', 'category': category},
            type = 'number',
            placeholder = '0.00'
        ), html.Br(),
        html.Label('Upper bound?'), html.Br(), 
        dcc.Input(
            id = {'type': 'bound-upper', 'category': category},
            type = 'number',
            placeholder = '0.00'
        ), html.Br(),
        html.Label('Exact value?'), html.Br(), 
        dcc.Input(
            id = {'type': 'bound-exact', 'category': category},
            type = 'number',
            placeholder = '0.00'
        ), html.Br(), html.Br(),
        html.Label('Non-numeric attribute value?'), html.Br(),
        dcc.Input(
            id = {'type': 'non-numeric', 'category': category},
            type = 'text', 
            placeholder = 'att'
        ), html.Br(), html.Br(),

        html.Button(
            'Search',
            id = {'type': 'submit-search', 'category': category},
            n_clicks = 0,
            style = {'backgroundColor': '#8af15a'}
        ), html.Br(),

        dcc.Store(id = {'type': 'search-results', 'category': category}, storage_type = 'memory'),

        html.Div(id = {'type': 'search-output', 'category': category})
    ])
    
    else:   #takes typed input
        return html.Div([
        html.H6('Input attribute (warning - case sensitive!)'),
        dcc.Input(
            id = 'att-search-input',
            type = 'text',
            placeholder = 'i.e. SpinTrq_min, _max, _avg',
            size = '50'
        ), html.Br(),

        dcc.RadioItems(
            id = 'all-or-not-manual',
            options = [{'label': 'Show all results', 'value': 'show-all-manual'},
                       {'label': 'Only show groups', 'value': 'show-builds-manual'}]
        ), html.Br(),

        html.Label('Lower bound?'), html.Br(), 
        dcc.Input(
            id = 'lower-bound-manual', 
            type = 'number', 
            placeholder = '0.00'
        ), html.Br(),
        html.Label('Upper bound?'), html.Br(), 
        dcc.Input(
            id = 'upper-bound-manual', 
            type = 'number', 
            placeholder = '0.00'
        ), html.Br(),
        html.Label('Exact value?'), html.Br(), 
        dcc.Input(
            id = 'exact-value-manual', 
            type = 'number', 
            placeholder = '0.00'
        ), html.Br(), html.Br(),
        html.Label('Non-numeric attribute value?'), html.Br(),
        dcc.Input(
            id = 'non-numeric-manual',
            type = 'text',
            placeholder = 'att'
        ), html.Br(), html.Br(),

        html.Button('Search', id = 'submit-manual-search', n_clicks = 0, style = {'backgroundColor': "#8af15a"}), html.Br(),
        dcc.Store(id = 'results-manual', storage_type = 'memory'),
        html.Div(id = 'search-page-manual')
    ])

def search_atts():
    return html.Div([
        html.H4('Search for items with specific attribute values', style = {'text-align': 'center'}),
        html.H6('Choose attribute category:'),
        dcc.RadioItems(
            id = 'att-filt-input',
            options = [{'label': 'Auto-assigned (machine)', 'value': 'aa-machine'},
                       {'label': 'Exsitu attributes', 'value': 'exsitu-search'},
                       {'label': 'Other attribute', 'value': 'manual-search'},
                       {'label': 'View all attributes', 'value': 'view-all-atts'}]
        ), html.Br(),
        html.Div(id = 'search-page-2')
    ], style = {'padding-left': '300px', 'padding-right': '300px'}
    )

def manual_search():
    return dropdown_search_layouts('manual')

def search_all():
    return dropdown_search_layouts('all', get_all_att_keys())

def search_autos():
    return dropdown_search_layouts('autos', sorted(METRICS_MACHINEFILE))

def search_exsitu():
    raw_exsitu_keys = []
    for sublist in EXSITU_KEYS:
        raw_exsitu_keys.extend(sublist)

    return dropdown_search_layouts('exsitu', sorted(raw_exsitu_keys))

def result_search(result, att):
    return html.Div([
        html.Br(),
        html.H6(f'Found {len(result)} results for {att} with the given filter conditions:'),
        html.Ul([html.Li([
            html.Div([
                html.Span(f'Path: {res.name} | # attributes: {len(res.attrs)}'),
            ])
        ])
        for res in sorted(result)]), html.Br(),

        html.H6('Select results to show expanded details for:'),
        dcc.Checklist(
            id = 'att-result-checklist',
            options=[{'label': res.name, 'value': res.name} for res in sorted(result)],
            value=[]
        ), html.Br(),
        html.Button('Show details', id = 'show-details-ssa', n_clicks = 0), html.Br(),
        html.Div(id = 'expanded-results')
    ], style = {'padding-bottom': '50px'})