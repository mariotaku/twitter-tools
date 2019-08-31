#!/usr/bin/env python3
import argparse
import datetime
import webbrowser
from datetime import datetime, timedelta
from email.utils import parsedate_tz

import twitter
import yaml
from requests_oauthlib import OAuth1Session
from twitter import TwitterError

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'


def confirm(message, default=None):
    if default is None:
        t = input(message)
    else:
        if default:
            default_input = 'y'
        else:
            default_input = 'n'
        t = input('%s [%s]' % (message, default_input))
    if t == '' or t is None and default is not None:
        return default
    while t != 'y' and t != 'n':
        t = input('Type y or n: ')
    if t == 'y':
        return True
    else:
        return False


def get_access_token(ck, cs):
    oauth_client = OAuth1Session(client_key=ck, client_secret=cs, callback_uri='oob')

    print('\nRequesting temp token from Twitter...\n')

    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError as e:
        raise 'Invalid response from Twitter requesting temp token: {0}'.format(e)

    url = oauth_client.authorization_url(AUTHORIZATION_URL)

    print('I will try to start a browser to visit the following Twitter page '
          'if a browser will not start, copy the URL to your browser '
          'and retrieve the pincode to be used '
          'in the next step to obtaining an Authentication Token: \n'
          '\n\t{0}'.format(url))

    webbrowser.open(url)
    pincode = input('\nEnter your pincode? ')

    print('\nGenerating and signing request for an access token...\n')

    oauth_client = OAuth1Session(client_key=ck, client_secret=cs,
                                 resource_owner_key=resp.get('oauth_token'),
                                 resource_owner_secret=resp.get('oauth_token_secret'),
                                 verifier=pincode)
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError as e:
        raise 'Invalid response from Twitter requesting temp token: {0}'.format(e)

    return resp.get('oauth_token'), resp.get('oauth_token_secret')


def load_credentials():
    try:
        with open('.twitter_credentials.yml') as f:
            c = yaml.load(f)
            return {'ck': c['consumer_key'],
                    'cs': c['consumer_secret'],
                    'at': c['access_token'],
                    'ats': c['access_token_secret']}
    except IOError:
        return None


def get_credentials(crds):
    ck = None
    cs = None
    if crds and crds['ck'] and crds['cs']:
        if not confirm('Do you need to use new consumer key/secret?', default=False):
            ck = crds['ck']
            cs = crds['cs']
    if ck is None or cs is None:
        ck = input('Input consumer key: ')
        cs = input('Input consumer secret: ')

    if confirm('Do you have access token and secret already?', default=False):
        at = input('Input access token: ')
        ats = input('Input access token secret: ')
    else:
        at, ats = get_access_token(ck, cs)
    return {'ck': ck, 'cs': cs, 'at': at, 'ats': ats}


def api():
    credentials = load_credentials()

    if not credentials or confirm('Do you want to switch to a new user?', default=False):
        credentials = get_credentials(credentials)
        with open('.twitter_credentials.yml', 'w') as f:
            yaml.dump({
                'consumer_key': credentials['ck'],
                'consumer_secret': credentials['cs'],
                'access_token': credentials['at'],
                'access_token_secret': credentials['ats'],
            }, f, default_flow_style=False)

    a = twitter.Api(consumer_key=credentials['ck'], consumer_secret=credentials['cs'],
                    access_token_key=credentials['at'],
                    access_token_secret=credentials['ats'])

    try:
        a.VerifyCredentials()
    except TwitterError:
        print('User logged out')
        exit(0)

    return a


def argparse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f'Unrecognized date {date_str}')

def to_datetime(datestring):
    time_tuple = parsedate_tz(datestring.strip())
    dt = datetime(*time_tuple[:6])
    return dt - timedelta(seconds=time_tuple[-1])
