#!/usr/bin/env python3
import concurrent.futures
from twitter import TwitterError

import common
from common import confirm

api = common.api()
with open("blocked.list") as f:
    blocked_ids = list(filter(lambda l: len(l) > 0, map(lambda l: l.rstrip('\n'), f.readlines())))

executor = concurrent.futures.ThreadPoolExecutor(max_workers=80)

cancelled = False

unblock_failed_ids = []

def do_unblock(uid):
    if cancelled:
        return
    try:
        print('unblocking %d' % uid)
        api.DestroyBlock(uid)
    except TwitterError as e:
        unblock_failed_ids.append(uid)

try:
    for user_id in blocked_ids:
        executor.submit(do_unblock, int(user_id))
    executor.shutdown(wait=True)
except (KeyboardInterrupt, SystemExit):
    cancelled = True
    print('Interrupted, exiting...')