#!/usr/bin/env python3
import concurrent.futures

from twitter import TwitterError

from common import confirm, api

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
