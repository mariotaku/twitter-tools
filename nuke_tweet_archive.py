#!/usr/bin/env python3
import concurrent.futures
import json

from twitter import TwitterError

from common import confirm, api
import sys

tweets = []

with open(sys.argv[-1], encoding='utf-8') as f:
    js = f.read()
    idx = js.index('= [') + 2
    tweets = json.loads(js[idx:])

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
    except TwitterError:
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
