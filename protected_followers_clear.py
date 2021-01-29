#!/usr/bin/env python3
import concurrent.futures

from twitter import TwitterError

import common
from common import confirm

api, me = common.api2()
friend_ids_cursor = -1
friend_ids = []

print('Getting following list...')
while friend_ids_cursor != 0:
    friend_ids_cursor, _, ids = api.GetFriendIDsPaged(cursor=friend_ids_cursor)
    friend_ids += ids
print('You have %d followings' % len(friend_ids))

follower_ids_cursor = -1
protected_follower_ids = []

print('Getting followers list (%d total)' % me.followers_count)
fetched = 0
while follower_ids_cursor != 0:
    follower_ids_cursor, _, followers = api.GetFollowersPaged(cursor=follower_ids_cursor)
    fetched += len(followers)
    protected_batch = list(map(lambda x: x.id, filter(lambda x: x.protected, followers)))
    print('Fetched %d/%d (%d protected in this batch)', fetched, me.followers_count, len(protected_batch))
    protected_follower_ids += protected_batch
print('You have %d protected followers' % len(protected_follower_ids))

no_mutual_followers = set(protected_follower_ids) - set(friend_ids)

print('You have %d protected followers you haven\'t followed.' % len(no_mutual_followers))

unblock = confirm('Unblock those users after removed from followers list?', default=True)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=80)

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
