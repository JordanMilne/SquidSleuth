.. role:: python(code)
   :language: python

SquidSleuth
===========

.. image:: https://travis-ci.org/JordanMilne/SquidSleuth.svg?branch=master
    :target: https://travis-ci.org/JordanMilne/SquidSleuth/
.. image:: https://codecov.io/github/JordanMilne/SquidSleuth/coverage.svg?branch=master
    :target: https://codecov.io/github/JordanMilne/SquidSleuth

Stuff for watching active connections on Squid servers with publicly accessible
debugging endpoints. See who's actually accessing what and when.

I was dealing with some abuse from a user of an open proxy on a small service I administer.
I happened to find these endpoints when trying to figure out who the user really was, and
figured it'd be neat to have some tools to run a backtrace without needing to make a Visual
Basic GUI interface.

Installing
==========

* Run `setup.py install`
* install any relevant database APIs (psycopg2, etc.)
* Set connection string via `export SQUIDSLEUTH_CONNSTR="sqlite:///sleuth.db"` (I actually recommend Postgres)
* Run `setup.py bootstrap` to set up the database schema

Usage
=====

* Run `squidsleuth http://<PROXY ADDRESS>/`
* Results should start streaming into configured database.

Mitigations
===========

Don't want people doing this on your server? Don't do [this](http://wiki.squid-cache.org/Features/CacheManager#default),
deny everyone access to `manager`. You almost definitely don't even care about accessing manager yourself.

Don't want people snooping on your connections when you're using a proxy? Don't use crappy open proxies, duh.
