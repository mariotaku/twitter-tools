#!/usr/bin/env python3
import html
import json
import sys
from datetime import datetime
from pathlib import Path

tweets = {}

data_dir = Path(sys.argv[1])
for entry in data_dir.iterdir():
    if entry.name == 'tweets.js' or entry.name.startswith('tweets-part'):
        with entry.open(encoding='utf-8') as f:
            js = f.read()
            idx = js.index('= [') + 2
            for tweet in json.loads(js[idx:]):
                if 'tweet' in tweet:
                    tweet = tweet['tweet']
                tweets[tweet['id']] = tweet

for tweet in tweets.values():
    if 'in_reply_to_status_id' in tweet:
        in_reply_to_status_id = tweet['in_reply_to_status_id']
        if in_reply_to_status_id in tweets:
            in_reply_to_tweet = tweets[in_reply_to_status_id]
            tweet['in_reply_to_tweet'] = in_reply_to_tweet
            if 'thread_replies' not in in_reply_to_tweet:
                in_reply_to_tweet['thread_replies'] = []
            in_reply_to_tweet['thread_replies'].append(tweet)


def tweet_created_at(t):
    return datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S %z %Y')


def is_thread_head(t):
    return 'thread_replies' in t and 'in_reply_to_status_id' not in t


threads = sorted(filter(is_thread_head, tweets.values()), key=tweet_created_at)

with Path(data_dir.parent, 'Your threads.html').open(mode='w', encoding='utf-8') as f:
    print('<html>', file=f)
    print("""
    <head>
      <title>Your threads</title>
      <style>
      body {
        font-family: "Times New Roman", "YuMincho", "Hiragino Mincho ProN", "Yu Mincho", "MS PMincho", serif;
        width: 800px;
        margin-left: auto;
        margin-right: auto;
      }
      
      article {
      }
      
      article img,video {
        margin-top: 5px;
        width: 100%;
      }
      
      hr {
      }
      </style>
    </head>
    """, file=f)
    print('<body>', file=f)
    for thread in threads:
        print('<article>', file=f)
        created_at = tweet_created_at(thread).strftime('%Y-%m-%d')
        print(f'<h2>Thread posted at {created_at}</h2>', file=f)

        def print_tweet(t):
            print(f'<p>{html.escape(html.unescape(t["full_text"]))}</p>'.replace('\n', '<br>'), file=f)
            if 'extended_entities' in t:
                entities = t['extended_entities']
                if 'media' in entities:
                    for m in entities['media']:
                        if m['type'] == 'photo':
                            media_url: str = m["media_url_https"]
                            file_name = f'{t["id"]}-{media_url.rsplit("/", 1)[-1]}'
                            print(f'<img src="./data/tweets_media/{file_name}"/><br>', file=f)
                        elif m['type'] == 'video':
                            print('<video controls>', file=f)
                            for variant in m['video_info']['variants']:
                                if variant['content_type'] != 'video/mp4':
                                    continue
                                file_name = f'{t["id"]}-{variant["url"].rsplit("/", 1)[-1].split("?", 1)[0]}'
                                print(f'<source src="./data/tweets_media/{file_name}">', file=f)
                            print('</video><br>', file=f)
            if 'thread_replies' in t:
                for st in t['thread_replies']:
                    print_tweet(st)


        print_tweet(thread)
        print('</article>', file=f)

        print('<hr>', file=f)
    print('</body>', file=f)
