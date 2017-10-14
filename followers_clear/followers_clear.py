#!/usr/bin/env python3
import concurrent.futures

from twitter import TwitterError
import twitter
from requests_oauthlib import OAuth1Session
import webbrowser
import yaml

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
            return c['consumer_key'], c['consumer_secret'], c['access_token'], \
                   c['access_token_secret']
    except IOError:
        return None


def get_credentials():
    ck = input('Input consumer key: ')
    cs = input('Input consumer secret: ')

    if confirm('Do you have access token and secret already?', default=False):
        at = input('Input access token: ')
        ats = input('Input access token secret: ')
    else:
        at, ats = get_access_token(ck, cs)
    return ck, cs, at, ats


credentials = load_credentials()

if not credentials or confirm('Do you want to switch to a new user?', default=False):
    credentials = get_credentials()
    with open('.twitter_credentials.yml', 'w') as f:
        yaml.dump({
            'consumer_key': credentials[0],
            'consumer_secret': credentials[1],
            'access_token': credentials[2],
            'access_token_secret': credentials[3],
        }, f, default_flow_style=False)

consumer_key, consumer_secret, access_token, access_token_secret = credentials

api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_token,
                  access_token_secret=access_token_secret)

friend_ids_cursor = -1
friend_ids = []

print('Getting following list...')
while friend_ids_cursor != 0:
    friend_ids_cursor, _, ids = api.GetFriendIDsPaged(cursor=friend_ids_cursor)
    friend_ids += ids
print('You have %d followings' % len(friend_ids))

follower_ids_cursor = -1
follower_ids = []

print('Getting followers list')
while follower_ids_cursor != 0:
    follower_ids_cursor, _, ids = api.GetFollowerIDsPaged(cursor=follower_ids_cursor)
    follower_ids += ids
print('You have %d followers' % len(follower_ids))

no_mutual_followers = set(follower_ids) - set(friend_ids)

print('You have %d followers you haven\'t followed.' % len(no_mutual_followers))

unblock = confirm('Unblock those users after removed from followers list?', default=True)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

cancelled = False

block_failed_ids = []
unblock_failed_ids = []


def remove_follower(uid):
    if cancelled:
        return
    try:
        print('blocking %d' % uid)
        api.CreateBlock(uid)
    except TwitterError:
        block_failed_ids.append(uid)
    if unblock:
        try:
            print('unblocking %d' % uid)
            api.DestroyBlock(uid)
        except TwitterError:
            unblock_failed_ids.append(uid)


try:
    for user_id in no_mutual_followers:
        executor.submit(remove_follower, user_id)
    executor.shutdown(wait=True)
except (KeyboardInterrupt, SystemExit):
    cancelled = True
    print('Interrupted, exiting...')

with open('block_failed_ids.list', 'w') as f:
    for user_id in block_failed_ids:
        f.write('%d\n' % user_id)

with open('unblock_failed_ids.list', 'w') as f:
    for user_id in unblock_failed_ids:
        f.write('%d\n' % user_id)
