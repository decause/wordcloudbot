#!/usr/bin/env python2
"""
Using custom colors
====================
Using the recolor method and custom coloring functions.
"""

from os import path
from scipy.misc import imread
import matplotlib.pyplot as plt
import random
import tempfile

from wordcloud import WordCloud, STOPWORDS

import requests


def get_meeting_log(url):
    """ get some logs and return them for you lol """
    response = requests.get(url)
    return response.text


def scrub_logs(text):
    lines = text.split("\n")

    # Strip timestamp and the nick of speakers
    lines = [
        line[8:].split('> ', 1)[-1].split(' * ', 1)[-1].strip()
        for line in lines
        if line.strip()
    ]

    text = "\n".join(lines)
    return text


def test_scrub_logs():
    scrubbed_logs = scrub_logs("""
    there once was a guy who was cool
    blahblahblah <threbean> this is the shit.
    1234567890 * pingou lol
    """)

    print scrubbed_logs


def grey_color_func(word, font_size, position, orientation, random_state=None):
    return "hsl(0, 0%%, %d%%)" % random.randint(60, 100)


def generate_word_cloud(text, mask_filename):
    d = path.dirname(__file__)  #??
    mask = imread(path.join(d, mask_filename))

    # adding movie script specific stopwords
    stopwords = STOPWORDS.copy()
    stopwords.add("info")
    stopwords.add("meetbot")
    stopwords.add("supybot")

    wc = WordCloud(max_words=1000, mask=mask, stopwords=stopwords, margin=10,
                random_state=1).generate(text)

    wc.recolor(color_func=grey_color_func, random_state=3)

    _, tmpfilename = tempfile.mkstemp('-wordcloud.png')
    wc.to_file(tmpfilename)
    return tmpfilename


def test_generate_word_cloud():

    # preprocessing text to remove timestamps
    filename = "infrastructure.2015-04-30-18.00.log.txt"
    with open(filename, "r") as f:
        lines = f.readlines()
    text = "\n".join(lines)
    scrubbed = scrub_logs(text)
    fname = generate_word_cloud(scrubbed, "Fedora_logo_simple.png")
    print fname

test_generate_word_cloud()
