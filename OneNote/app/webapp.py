# dependencies
import uuid
import config
import flask
from flask_oauthlib.client import OAuth
from threading import Thread

# setup the app
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

# msgraph token getter
@MSGRAPH.tokengetter
def get_token():
    """Called by flask_oauthlib.client to retrieve current access token."""
    return (flask.session.get('access_token'), '')

# app functions
@APP.route('/')
def homepage():
    """Render the homepage."""
    content = '''
        <p>To begin using the add-on, first authenticate for Microsoft Graph by clicking Connect.</p>
        <p><button type="button" class="btn btn-success btn-md" onclick="window.location.href='/login'">Connect</button></p>
        <img src="/static/images/microsoft_graph.png" alt="Microsoft Graph" width=400 height=195/>
        '''
    return flask.render_template('homepage.html', content=content)

@APP.route('/login')
def login():
    """Prompt user to authenticate"""
    flask.session['state'] = str(uuid.uuid4())
    return MSGRAPH.authorize(callback=config.REDIRECT_URI,
        state=flask.session['state'])

@APP.route('/login/authorized')
def authorized():
    """Handler for the application's Redirect Uri."""
    if str(flask.session['state']) != str(flask.request.args['state']):
        raise Exception('state returned to redirect URL does not match!')
    response = MSGRAPH.authorized_response()
    flask.session['access_token'] = response['access_token']
    return flask.redirect('/start_task')

@APP.route('/start_task')
def start_task():
    def do_work():
        # do something that takes a long time
        import time
        for i in range(10):
            time.sleep(10)
            print(testvar)

    thread = Thread(target=do_work)
    thread.start()

    # update the user
    content = '''
        <p>You are authenticated and the app is live. Feel free to close this window.</p>
        <img src="/static/images/microsoft_graph.png" alt="Microsoft Graph" width=400 height=195/>
        '''
    return flask.render_template('homepage.html', content=content)

"""
From here, I think I'll pursue a UI that creates kernel settings and enables stuff like resets, restarts, interruptions, etc.
"""
#@APP.route('/graphcall')
#def graphcall():
    # return website shit
#    return flask.render_template('homepage.html')

if __name__ == '__main__':
    APP.run()