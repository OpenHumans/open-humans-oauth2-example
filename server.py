#!/usr/bin/env python

import logging
import os

logging.basicConfig(level=logging.DEBUG)

from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth

OPEN_HUMANS_KEY = os.getenv('OPEN_HUMANS_KEY')
OPEN_HUMANS_SECRET = os.getenv('OPEN_HUMANS_SECRET')

OPEN_HUMANS_BASE_URL = os.getenv('OPEN_HUMANS_BASE_URL',
                                 'https://openhumans.org')

PORT = int(os.getenv('PORT', 8000))

app = Flask(__name__)

app.debug = True
app.secret_key = 'development'

oauth = OAuth(app)

open_humans = oauth.remote_app(
    'open-humans',
    consumer_key=OPEN_HUMANS_KEY,
    consumer_secret=OPEN_HUMANS_SECRET,
    request_token_params={'scope': 'read+write'},
    base_url=OPEN_HUMANS_BASE_URL + '/api/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url=OPEN_HUMANS_BASE_URL + '/oauth2/access_token',
    authorize_url=OPEN_HUMANS_BASE_URL + '/oauth2/authorize'
)


@app.route('/')
def index():
    if 'open_humans_token' in session:
        # Once you have the token you can GET and POST to the API
        profile = open_humans.get('profile/current/')

        return jsonify(profile.data)

    return redirect(url_for('login'))


@app.route('/auth/open-humans')
def login():
    return open_humans.authorize(callback=url_for('callback',
                                                  _external=True))


@app.route('/logout')
def logout():
    session.pop('open_humans_token', None)

    return redirect(url_for('index'))


@app.route('/auth/open-humans/callback')
def callback():
    response = open_humans.authorized_response()

    if response is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description'])

    if 'access_token' not in response:
        return 'No access_token present'

    session['open_humans_token'] = (response['access_token'], '')

    return redirect(url_for('index'))


@open_humans.tokengetter
def get_open_humans_oauth_token():
    return session.get('open_humans_token')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
