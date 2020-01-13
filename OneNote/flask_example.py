"""Flask-OAuthlib sample for Microsoft Graph"""
# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license.
# See LICENSE in the project root for license information.
import uuid
import json
import flask
from flask_oauthlib.client import OAuth
from tqdm import tqdm
import config

APP = flask.Flask(__name__, template_folder='static/templates')
APP.debug = True
APP.secret_key = 'development'
OAUTH = OAuth(APP)
MSGRAPH = OAUTH.remote_app(
    'microsoft', consumer_key=config.CLIENT_ID, consumer_secret=config.CLIENT_SECRET,
    request_token_params={'scope': config.SCOPES},
    base_url=config.RESOURCE + config.API_VERSION + '/',
    request_token_url=None, access_token_method='POST',
    access_token_url=config.AUTHORITY_URL + config.TOKEN_ENDPOINT,
    authorize_url=config.AUTHORITY_URL + config.AUTH_ENDPOINT)

@APP.route('/')
def homepage():
    """Render the home page."""
    return flask.render_template('homepage.html', sample='Flask-OAuthlib')

@APP.route('/login')
def login():
    """Prompt user to authenticate."""
    flask.session['state'] = str(uuid.uuid4())
    return MSGRAPH.authorize(callback=config.REDIRECT_URI, state=flask.session['state'])

@APP.route('/login/authorized')
def authorized():
    """Handler for the application's Redirect Uri."""
    if str(flask.session['state']) != str(flask.request.args['state']):
        raise Exception('state returned to redirect URL does not match!')
    response = MSGRAPH.authorized_response()
    flask.session['access_token'] = response['access_token']
    return flask.redirect('/graphcall')

@APP.route('/graphcall')
def graphcall():
    """Confirm user authentication by calling Graph and displaying some data."""

    # grab list of notebooks and for each build hierarchy of associated sections, pages, and content
    notebooks = MSGRAPH.get('me/onenote/notebooks').data['value']
    for i, notebook in enumerate(tqdm(notebooks, desc='notebooks')):
        notebooks[i]['sections'] = MSGRAPH.get('me/onenote/notebooks/{}/sections'.format(notebook['id'])).data['value']
        
        for j, section in enumerate(tqdm(notebooks[i]['sections'], desc='sections of notebook {}'.format(notebooks[i]['displayName']))):
            notebooks[i]['sections'][j]['pages'] = MSGRAPH.get('me/onenote/sections/{}/pages'.format(notebooks[i]['sections'][j]['id'])).data['value']
            
            for k, page in enumerate(tqdm(notebooks[i]['sections'][j]['pages'], desc='pages of section {} of notebook {}'.format(
                notebooks[i]['displayName'], notebooks[i]['sections'][j]['displayName']))):
                
                notebooks[i]['sections'][j]['pages'][k]['content'] = MSGRAPH.get('me/onenote/pages/{}/content?includeinkML=true'.format(
                    notebooks[i]['sections'][j]['pages'][k]['id'])).data
                with open('testing.html', 'wb') as f:
                    f.write(notebooks[i]['sections'][j]['pages'][k]['content'])
                
                assert False
    
    # return website shit
    return flask.render_template('graphcall.html',
                                 graphdata=notebooks[0],
                                 endpoint=config.RESOURCE + config.API_VERSION + '/',
                                 sample='Flask-OAuthlib')

@MSGRAPH.tokengetter
def get_token():
    """Called by flask_oauthlib.client to retrieve current access token."""
    return (flask.session.get('access_token'), '')

if __name__ == '__main__':
    APP.run()