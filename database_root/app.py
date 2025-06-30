import dash, os
from dash import html, dcc
import dash_bootstrap_components as dbc
import backend_top as dbf
from callbacks_main import register_main_callbacks
from utils.constants import MAIN_MENU_OPS, MASTER_FILE
from callbacks_graphs import register_graph_callbacks
from callbacks_uploaddata import register_upload_callbacks
from callbacks_search import register_search_callbacks
from callbacks_atts import register_att_callbacks
from callbacks_analysis import register_analysis_callbacks
from flask import Flask, session, redirect, url_for, request
# type: ignore[import]
from authlib.integrations.flask_client import OAuth # type: ignore
from werkzeug.middleware.proxy_fix import ProxyFix

#-------------------------- Authentication system setup --------------------------------

server = Flask(__name__)
server.wsgi_app = ProxyFix(server.wsgi_app, x_proto = 1, x_host = 1)
server.secret_key = os.getenv("FLASK_SECRET_KEY")

oauth = OAuth(server)
azure = oauth.register(
    name = 'azure',
    client_id = os.getenv('AZURE_CLIENT_ID'), 
    client_secret = os.getenv('AZURE_CLIENT_SECRET'),  
    access_token_url = f'https://login.microsoftonline.us/fd4ef3c7-ccdb-4a12-99ce-3f4e52c50d67/oauth2/v2.0/token', 
    authorize_url = f'https://login.microsoftonline.us/fd4ef3c7-ccdb-4a12-99ce-3f4e52c50d67/oauth2/v2.0/authorize',
    api_base_url = 'https://graph.microsoft.us/v1.0/',
    userinfo_endpoint = 'https://graph.microsoft.us/oidc/userinfo',
    jwks_uri = 'https://login.microsoftonline.us/fd4ef3c7-ccdb-4a12-99ce-3f4e52c50d67/discovery/v2.0/keys',
    client_kwargs = {'scope': 'openid email profile'}
)

@server.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external = True)
    return azure.authorize_redirect(redirect_uri)

@server.route('/login/callback')
def auth_callback():
    if not request.args.get('code'):
        return "Invalid or unsolicited callback - no code provided.", 400

    if request.args.get('error'):
        return f'Oauth Error: {request.args.get("error_description", "Unknown error")}', 400
    
    try:
        token = azure.authorize_access_token()
        if not token:
            return "No token received", 400

        user = azure.get('me').json()
        email = user.get('mail') or user.get('userPrincipalName')
        if not email:
            return "No email in token", 400
        if email:
            if not email.endswith('@astroa.org'):
                return "Access denied", 403
            session['user'] = email
            return redirect('/')
        
    except Exception as e:
        print(f'OAuth error: {e}')
        return f'OAuth Exception: {e}', 500

@server.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@server.before_request
def restrict_access():
    if request.path.startswith('/_dash') or request.path.startswith('/login') or request.path.startswith('/static'):
        return  #allow internal Dash requests and static assets
    if 'user' not in session:
        return redirect('/login')

#----------------------------- Dash App Setup ------------------------------------------

app = dash.Dash(
    __name__, 
    server = server,
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    suppress_callback_exceptions = True
)
app.title = 'ASTRO Database Interface'

#master file should be in the app working directory on the server. if this changes, update logic to have absolute filepath attached to master2.h5
dbf.create_master_file(MASTER_FILE, {'machine': 'meld piece of shit'})

app.layout = html.Div([
    html.H2("best database of all time", style = {'text-align': 'center'}),

    html.Div(
        dbc.ButtonGroup([
            dbc.Button(opt, id={'type': 'program-option', 'index': i}, n_clicks=0)
            for i, opt in enumerate(MAIN_MENU_OPS)], 
            className='mb-3'), 
            className = 'd-flex justify-content-center'
        ), html.Hr(),
        html.Div(id='main-content'),
        
        #global dcc.Store objects for saving/loading shit for comparison
        dcc.Store(id = 'global-storage-1', data = [], storage_type = 'memory'),
        dcc.Store(id = 'global-storage-2', data = [], storage_type = 'memory')     
])

register_main_callbacks(app)
register_upload_callbacks(app)
register_graph_callbacks(app)
register_search_callbacks(app)
register_att_callbacks(app)
register_analysis_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)