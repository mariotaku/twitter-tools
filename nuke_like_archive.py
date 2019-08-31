#!/usr/bin/env python3
import concurrent.futures
import json
import sys

from twitter import TwitterError

import common
from common import confirm

api = common.api()
likes = []

with open(sys.argv[-1], encoding='utf-8') as f:
    js = f.read()
    idx = js.index('= [') + 2
    likes = json.loads(js[idx:])

confirmed = confirm('There are %d likes. Are you sure to delete all likes in this archive?' % len(likes),
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
        api.DestroyFavorite(status_id=tid)
    except TwitterError as e:
        if e.message[0]['code'] == 144:
            return
        print(e)
        delete_failed_ids.append(tid)


try:
    for like in likes:
        executor.submit(delete_tweet, like['like']['tweetId'])
    executor.shutdown(wait=True)
except (KeyboardInterrupt, SystemExit):
    cancelled = True
    print('Interrupted, exiting...')

with open('delete_failed_like_ids.list', 'w') as f:
    for tid in delete_failed_ids:
        f.write('%s\n' % tid)
