#!/usr/bin/env python3
import json
from builtins import set, open

from twitter import Status

import common

api = common.api()

max_id = None
statuses = set()

print('Getting following list...')
while True:
    page = api.GetUserTimeline(screen_name='sunshengzi', include_rts=False, count=200, max_id=max_id)  # type: [Status]
    if len(page) == 1 and page[0].id == max_id:
        break
    statuses.update(page)
    max_id = page[-1].id

with open('user_timeline.json', 'w') as f:
    json.dump(list(map(lambda x: x.AsDict(), sorted(statuses, key=lambda x: x.created_at_in_seconds, reverse=True))), f,
              indent=2)
