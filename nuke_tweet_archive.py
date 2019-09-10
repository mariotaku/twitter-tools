#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
from json import JSONDecodeError
from time import sleep

from twitter import TwitterError

import common
from common import confirm, to_datetime

parser = argparse.ArgumentParser(description='Delete all tweets')
parser.add_argument('tweets', metavar='tweet.js', help='Tweets data from your twitter archive')
parser.add_argument('--since', dest='since', type=common.argparse_date, help='Delete all tweets since date (UTC)',
                    required=False)
parser.add_argument('--until', dest='until', type=common.argparse_date, help='Delete all tweets until date (UTC)',
                    required=False)

args = parser.parse_args()

filter_since = args.since
filter_until = args.until

print(filter_since)

api = common.api()

tweets = []


def filter_by_args(tweet):
    created_at = to_datetime(tweet['created_at'])
    if filter_since is not None and created_at < filter_since:
        return False
    if filter_until is not None and created_at > filter_until:
        return False
    return True


try:
    with open(args.tweets, encoding='utf-8') as f:
        js = f.read()
        idx = js.index('= [') + 2
        tweets = list(filter(filter_by_args, json.loads(js[idx:])))
except IOError or JSONDecodeError:
    print('Usage: nuke_tweet_archive.py tweet.js')
    exit(0)

confirmed = confirm('There are %d tweets. Are you sure to delete all tweets in this archive?' % len(tweets),
                    default=False)

if not confirmed:
    exit(0)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=80)

cancelled = False

delete_failed_ids = []


def delete_tweet(tid):
    if cancelled:
        return
    try:
        print('deleting %s' % tid)
        api.DestroyStatus(tid)
    except TwitterError as te:
        err_body = te.message[0]
        err_code = err_body['code']
        if err_code != 144:
            print('deleting %s failed: %s' % (tid, err_body))
            delete_failed_ids.append(tid)


try:
    for tweet in tweets:
        executor.submit(delete_tweet, tweet['id'])
    executor.shutdown(wait=True)
except (KeyboardInterrupt, SystemExit):
    cancelled = True
    print('Interrupted, exiting...')

with open('delete_failed_tweet_ids.list', 'w') as f:
    for tid in delete_failed_ids:
        f.write('%s\n' % tid)
