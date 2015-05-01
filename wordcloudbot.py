#!/usr/bin/env python

import os
import site
site.addsitedir(os.path.dirname(__file__))
site.addsitedir('/home/decause/.virtualenvs/word_cloud/lib/python2.7/site-packages/')


import fedmsg.config
import fedmsg.meta
import logging.config

import tweepy
from gencloud import generate_word_cloud, scrub_logs, get_meeting_log

# first load the fedmsg config from fedmsg.d
config = fedmsg.config.load_config()

logging.config.dictConfig(config.get('logging'))

fedmsg.meta.make_processors(**config)

topic_filter = 'meetbot.meeting.complete'

consumer_key        = config['consumer_key']
consumer_secret     = config['consumer_secret']
access_token_key    = config['access_token_key']
access_token_secret = config['access_token_secret']

auth_handler = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth_handler.set_access_token(access_token_key, access_token_secret)
twitter_api = tweepy.API(auth_handler)

fedmsg.init(active=True)

print "STARTING UP.  Listening for fedmsg messages."
for name, endpoint, topic, msg in fedmsg.tail_messages():
    if topic_filter not in topic:
        continue

    link = fedmsg.meta.msg2link(msg, **config)
    subtitle = fedmsg.meta.msg2subtitle(msg, **config)
    url = msg['msg']['url'] + ".log.txt"
    mask = "Fedora_logo_simple.png"

    content = subtitle + " " + link + " " + "#fedora"

    print "Working with url", url

    # get the meeting log
    text = get_meeting_log(url)

    # scrub the meeting log
    text = scrub_logs(text)

    # generate the word_cloud
    word_cloud = generate_word_cloud(text, mask)


    print "Tweeting %r" % content
    twitter_api.update_with_media(word_cloud, content)

    try:
        os.remove(word_cloud)
    except Exception as e:
        print "broked!", str(e)

    fedmsg.publish(topic="log", modname="logger", msg=dict(msg="Tweeted, lol"))

    print "Done."
