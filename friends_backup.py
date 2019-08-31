#!/usr/bin/env python3

from openpyxl import Workbook

import common

api = common.api()

friends_cursor = -1
friends = []

print('Getting following list...')
while friends_cursor != 0:
    friends_cursor, _, ids = api.GetFriendsPaged(cursor=friends_cursor)
    friends += ids
print('You have %d followings' % len(friends))

wb = Workbook()
ws = wb.active

for user in friends:
    ws.append([user.id, '@%s' % user.screen_name, user.name, 'https://twitter.com/%s' % user.screen_name])

wb.save('friends.xlsx')
