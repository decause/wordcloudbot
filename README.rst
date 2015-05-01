wordcloudbot
============

How it's going to work
~~~~~~~~~~~~~~~~~~

.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/twitter-diagram.png
   :width: 900px

----

It's dangerous to go alone! Take this!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    sudo yum install fedmsg
    sudo yum install python-fedmsg-meta-fedora-infrastructure
    sudo yum install python-fabulous
    sudo yum install tweepy

----

Your first fedmsg script
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    import fedmsg
    import pprint

    print "Posting up to listen on the fedmsg bus.  Waiting for a message..."
    for name, endpoint, topic, msg in fedmsg.tail_messages():
        pprint.pprint(msg)

Give it a run.

----

It's like a million voices cried out and then were silent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    #topic_filter = 'fedbadges'     # We really want this, but its rare
    topic_filter = 'fedoratagger'   # This is much easier to test with

    for name, endpoint, topic, msg in fedmsg.tail_messages():
        if topic_filter not in topic:
            # Bail out if the topic doesn't match
            continue

        pprint.pprint(msg)

See http://fedmsg.com/en/latest/topics for more

----

Some config at the top
~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    import fedmsg.config
    import logging.config

    # First, load the fedmsg config from fedmsg.d/
    config = fedmsg.config.load_config()

    # Then, configure the python stdlib logging to use fedmsg's logging config
    logging.config.dictConfig(config.get('logging'))

----

So meta
~~~~~~~

.. code:: python

    import fedmsg.meta

    # Initialize fedmsg's "meta" module if you have the fedora infra plugin
    fedmsg.meta.make_processors(**config)

    for name, endpoint, topic, msg in fedmsg.tail_messages():
        if topic_filter not in topic:
            continue

        # Only act on your own messages -- things that *you* did.
        if 'YOUR_FAS_USERNAME' not in fedmsg.meta.msg2usernames(msg, **config):
            continue

        # Use it to make nice text and other things
        # See also: msg2icon, msg2link, msg2usernames, msg2packages...
        subtitle = fedmsg.meta.msg2subtitle(msg, **config)
        print subtitle

----

A picture is worth a thousand words
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    import tempfile
    import urllib
    import os

    import fabulous.image

    for name, endpoint, topic, msg in fedmsg.tail_messages():
        # This returns a URL (most of the time)
        icon = fedmsg.meta.msg2icon(msg, **config)

        _, filename = tempfile.mkstemp(suffix='.png')
        print "Downloading", icon, "to", filename
        urllib.urlretrieve(icon, filename)

        print fabulous.image.Image(filename)

        print "Cleaning up %r" % filename
        os.remove(filename)


Intermezzo
==========

We have a neat working script that gets fedmsg messages pushed to it.  It can
extract neato stuff and print it.

But... if we want to move to the next step, we have to take a break from our
happy hacking to go and deal with Twitter, its API, and API keys.

The Twitter API
===============

We're going to have to:

1) Create our own "app".  Visit https://apps.twitter.com/app/new
2) Modify that app's permission to include **"Read and Write"**.
3) Authorize that app with our own account, which yields *oauth tokens*.
   To do this, click the **"Create my access token"** button at the bottom of
   your app's detail page.

We will keep those tokens a secret and our little bot will use them to login
and tweet on our behalf.  You'll get **four** secret strings.

Storing those secrets
~~~~~~~~~~~~~~~~~~~~~

First, add a directory called ``fedmsg.d/`` to your current working directory.

In it, put a file called ``fedmsg.d/twitter-secrets.py`` that looks like this:

.. code:: python

    config = dict(
        consumer_key        = "your api key goes here",
        consumer_secret     = "your api secret goes here",
        access_token_key    = "your access token goes here",
        access_token_secret = "your access token secret goes here",
    )

Test that fedmsg can read in that new config file by looking for them in:

.. code:: bash

    fedmsg-config | less

----

Using those secrets
~~~~~~~~~~~~~~~~~~~

Go back to ``yourwordcloudbot.py`` and add the following:

.. code:: python

    import tweepy

    consumer_key        = config['consumer_key']
    consumer_secret     = config['consumer_secret']
    access_token_key    = config['access_token_key']
    access_token_secret = config['access_token_secret']

    auth_handler = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth_handler.set_access_token(access_token_key, access_token_secret)
    twitter_api = tweepy.API(auth_handler)

----

And further down
~~~~~~~~~~~~~~~~

.. code:: python

    for name, endpoint, topic, msg in fedmsg.tail_messages():

        subtitle = fedmsg.meta.msg2subtitle(msg, **config)
        link = fedmsg.meta.msg2link(msg, **config)
        icon = fedmsg.meta.msg2icon(msg, **config)

        _, filename = tempfile.mkstemp(suffix='.png')
        print "Downloading", icon, "to", filename
        urllib.urlretrieve(icon, filename)

        # Construct and post our tweet.
        #print fabulous.image.Image(filename)
        content = subtitle + " " + link
        print "Tweeting %r" % content
        twitter_api.update_with_media(filename, content)

        print "Cleaning up %r" % filename
        os.remove(filename)

----

Does it work?
=============


systemd for real
~~~~~~~~~~~~~~~~

Make a new file called ``wordcloudbot.service`` with these contents::

    [Unit]
    Description=A Twitter bot for your Fedora Badges.  Wow.
    After=network.target
    Documentation=http://fedmsg.com

    [Service]
    ExecStart=/usr/local/bin/wordcloudbot.py
    Type=simple
    User=fedmsg
    Group=fedmsg

    [Install]
    WantedBy=multi-user.target


install.sh
==========

.. code:: bash

    #!/bin/bash -x
    # install.sh - (re)install and (re)start the wordcloudbot

    # Install our script
    cp wordcloudbot.py /usr/local/bin/wordcloudbot.py

    # Make sure no one else can read our secrets.
    cp fedmsg.d/twitter-secrets.py /etc/fedmsg.d/.
    chown fedmsg:fedmsg /etc/fedmsg.d/twitter-secrets.py
    chmod o-r /etc/fedmsg.d/twitter-secrets.py

    # Copy in service file for systemd
    cp wordcloudbot.service /usr/lib/systemd/system/wordcloudbot.service
    systemctl daemon-reload
    systemctl restart wordcloudbot

----

Watch the journal::

    sudo journalctl -u wordcloudbot --follow


fedmsg: what it is?
===================


The `Fedora Infrastructure Message Bus <http://fedmsg.com>`_ is a
python package and API used around Fedora Infrastructure to send
and receive messages to and from applications.


.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/topology.png
   :height: 485px


It is *publicly subscribable* -- hit up ``tcp://hub.fedoraproject.org:9940``
with a ``zmq.SUB`` socket.

It has Fedora in the name, but `Debian Infrastructure started picking it up
<http://lists.debian.org/debian-qa/2013/04/msg00010.html>`_
last summer.  They've `made progress
<http://blog.olasd.eu/2013/07/bootstrapping-fedmsg-for-debian/>`_ to the point
that we had to change the name to mean the *FEDerated Message Bus* instead.

`data.gouv.fr <https://data.gouv.fr>`_ is using it too.  Maybe others?  We get
questions and clarifications on the `deployment docs
<http://fedmsg.com/en/latest/deployment>`_ from time to time.


fedmsg: what it do?
~~~~~~~~~~~~~~~~~~~

There are two aspects to this workshop:

- **A historical component**.  I want to show you briefly how to use
  `datagrepper <https://apps.fedoraproject.org/datagrepper>`_ which has been
  the most surprisingly useful piece of the fedmsg infrastructure.

- **A realtime component**.  I want to go over some of the current applications
  of fedmsg briefly.  After that, I'll go into depth -- step-by-step -- to show
  you how to write your own script that connects to the live fedmsg stream and
  does something "useful" with it.

Do you want me to cover?

- **Setting up your own local bus**.  It's really pretty easy and we can do it
  in time.  I'm just guessing that nobody here is interested in doing that.
  I'll touch on it but we can talk more about it later if you like.


first
=====
you should get it
~~~~~~~~~~~~~~~~~

.. code:: bash

    sudo yum install fedmsg

There's also a plugin that let's us render **Fedora Infrastructure** messages
nicely.  You should install that too:

.. code:: bash

    sudo yum install python-fedmsg-meta-fedora-infrastructure


A taste of the bus
~~~~~~~~~~~~~~~~~~

Clone the repo from https://github.com/ralphbean/fedmsg2gource

Run::

    python fedmsg2gource.py --days 14 > testing.log
    cat testing.log | \
        gource -i 10 \
            --user-image-dir ~/.cache/avatars/ \
            --log-format custom \
            --viewport 1024x730 \
            -



Explore the datagrepper API
~~~~~~~~~~~~~~~~~~~~~~~~~~~

https://apps.fedoraproject.org/datagrepper


say you wanted your own local bus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    sudo yum install fedmsg-relay
    sudo systemctl start fedmsg-relay
    echo "Hello World." | fedmsg-logger --modname=git --topic=repo.update
    echo '{"a": 1}' | fedmsg-logger --json-input
    fedmsg-logger --message="This is a message."
    fedmsg-logger --message='{"a": 1}' --json-input

or from python:

.. code:: python

    import fedmsg

    fedmsg.publish(
        topic='testing',
        msg={
            'test': 'Hello World',
            'foo': jsonifiable_objects,
            'bar': a_sqlalchemy_object,
        }
    )


if you want to consume
~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    fedmsg-tail --really-pretty

.. code:: python

    {
        "i": 1,
        "timestamp": 1344344053.2337201,
        "topic": "org.fedoraproject.prod.bodhi.update.comment",
        "msg": {
            "comment": {
                "update_title": "nethack4-4.0.0-1.fc20",
                "group": None,
                "author": "ralph",
                "text": "I'm so pumped to pwn those minotaurs!",
                "karma": 1,
                "anonymous": False,
                "timestamp": 1344344050.0
            }
        }
    }


consuming messages from python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    import fedmsg

    for name, endpoint, topic, msg in fedmsg.tail_messages():
        print topic, msg


consuming messages with a daemon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``fedmsg-hub`` is a daemon that can make writing your own
long-running consumers simpler.  There are `docs on fedmsg.com
<http://www.fedmsg.com/en/latest/consuming/#the-hub-consumer-approach>`_
for writing plugins, but they look like this:

.. code:: python

    import pprint
    import fedmsg.consumers


    class MyConsumer(fedmsg.consumers.FedmsgConsumer):
        topic = "org.fedoraproject.*"
        config_key = 'myconsumer.enabled'

        def consume(self, message):
            pprint.pprint(message)


consuming messages at the command line... an aside
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are lots of fun options to ``fedmsg-tail`` like ``--terse``.

.. code:: bash

   fedmsg-tail --terse

.. code:: text

    buildsys.build.state.change -- ausil's tncfhh-0.8.3-14.fc20 completed
    http://koji.fedoraproject.org/koji/buildinfo?buildID=439734
    trac.ticket.update -- kevin closed a ticket on the Fedora Infrastructure trac instance as 'fixed'
    https://fedorahosted.org/fedora-infrastructure/ticket/3904
    bodhi.update.request.testing -- mmckinst submitted nawk-20121220-1.fc18 to testing
    https://admin.fedoraproject.org/updates/nawk-20121220-1.fc18
    wiki.article.edit -- Hguemar made a wiki edit to "Flock:Rideshare"
    https://fedoraproject.org/w/index.php?title=Flock:Rideshare&diff=prev&oldid=347430


Things that use fedmsg
======================


there's a lot of them at this point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


koji stalk
~~~~~~~~~~

David Aquilina's (dwa's) `koji stalk
<http://dwa.fedorapeople.org/wip/koji-stalk.py>`_ monitors koji over fedmsg and
rebuilds packages for arm and ppc.

----

FAS2Trac (ftl) (fama updater)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

herlo's `FAS2Trac fama updater (ftl)
<https://git.fedorahosted.org/cgit/ftl.git>`_ listens to messages indicating
that a user has applied for membership in the ambassadors group -- it then
files a ticket in the `ambassadors' trac instance
<https://fedorahosted.org/fama/>`_ for a potential sponsor via XMLRPC.

----

compose downloader
~~~~~~~~~~~~~~~~~~

p3ck's `fedmsg-download <https://github.com/p3ck/fedmsg-download/>`_
listens for messages that the daily branched and rawhide compose
process has finished -- it then downloads the latest builds from
``rsync://dl.fedoraproject.org/fedora-linux-development``

----

synchronization of package ACLs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

So, it **used** to be that when someone was granted *commit* access to a
package in the `Fedora PackageDB (pkgdb)
<https://apps.fedoraproject.org/#PkgDB>`_, the webapp simply wrote to a
database table indicating the new relationship.  Every *hour*, a cronjob would
run that queried the state of that database and then re-wrote out the ACLs for
gitolite -- the software that manages access to our `package repositories
<http://pkgs.fedoraproject.org>`_.

Consequently, we had lots of *waiting*: you would request commit access to a
repository, then *wait* for an owner to grant you rights, then *wait* for that
cronjob to run before you could actually push.

With `a new fedmsg consumer
<https://github.com/fedora-infra/fedmsg-genacls/blob/develop/fedmsg_genacls.py>`_
that we have in place, those gitolite ACLs are re-written in response to
fedmsg messages from the pkgdb.  It is much faster.

----

notifications to email, irc, the desktop, and android
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There's the new `FMN system <https://apps.fedoraproject.org/>`_ that can
deliver notifications to you via irc, email, and android.

There's also lmacken's `fedmsg-notify <http://lewk.org/blog/fedmsg-notify>`_
which listens for messages and displays a filtered stream on your desktop with
``libnotify``.

.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/fedmsg-notify-0-crop.png
   :height: 300px

----

reports
=======

10 ways from sunday
~~~~~~~~~~~~~~~~~~~

Every week, pingou's `owner changes report tool
<https://lists.fedoraproject.org/pipermail/infrastructure/2013-June/013070.html>`_
emails the devel list with a report of what packages were orphaned, unorphaned
and retired.

.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/ownerchange-screenshot.png
   :height: 420px

----


There's also the `Release Engineering Dashboard
<https://apps.fedoraproject.org/releng-dash>`_ which grabs data from
datagrepper on all the latest updates syncs, composes, image builds, etc.. and
puts their status all in one place.  Pure HTML/javascript -- there's no
server-side app here.

.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/releng-dash-screenshot.png
   :height: 350px

----

fedora badges
=============
for you, and you, and you
~~~~~~~~~~~~~~~~~~~~~~~~~

`Fedora badges <https://badges.fedoraproject.org/>`_ launched last year at
Flock13.  It awards "badges" to Fedora contributors for their activity.

.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/badges_fan.png

Pretty fun.  ``:)``

----

To sum that up
==============

The assimilation of **message producing services** is nearly complete.

There are many **message consuming services** already in place.. but we can
likely make many more.  Which is why you're here, no?

- Presented by Ralph Bean
- http://github.com/ralphbean
- http://twitter.com/ralphbean
- http://threebean.org
- ``2048R/971095FF 2012-12-06``

Go sit in ``#fedora-fedmsg`` on ``irc.freenode.net``.

http://threebean.org/presentations/fedmsg-flock14/

.. image:: http://threebean.org/presentations/images/fedmsg-flock14-img/creative-commons.png
http://threebean.org/presentations/
