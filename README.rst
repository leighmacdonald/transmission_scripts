===================
transmissionscripts
===================

A set of scripts and functions to help managing a [Transmission](https://transmissionbt.com/) instance via
its RPC interface.

----------------
Included Scripts
----------------

Below is a list of the scripts along with simple descriptions of their functionality.

-----------
ts_clean.py
-----------

This script will scan active torrents for those which qualify to be removed from the client. This
tool reads in the config file and uses the tracker rules definitions defined in there to make decisions
as to what to remove.

---------
ts_cli.py
---------

A unix shell like interpreter. You can chan commands together similar to using pipes in any
standard unix-like shell. Filters and commands are separated by | characters.

The main initial command to use is `ls`. If you give no arguments it will just list
out all torrents, similar to ls on a unix command line listing files.

Some filters available:


- Filter by name: n=prefix_to_search_for
- Filter by tracker: t=tracker_key_prefix
- Filter by status: all, active, downloading, seeding, stopped, finished

Sorting options:

- Sort by: id, progress, name, size, ratio, total speed, up/dl speed, status, queue position, age
- Reverse sort

Some Commands available:

- start: Start all the torrents passed to it.
- stop: Stop all the torrents passed to it.
- count: Count the current torrents including filtering.
- any integer: Using any positive integer will limit torrent results to that value.
- print: print the results in a simple list

Example Syntax and Usage
------------------------

List torrents filtering by those starting with fred and additionally also active.::

        (TS@172.16.1.9:9091)> ls | n=fred | active
        [548] Freddie Gibbs - 2013 - ESGN 18% 0.0 [downloading]
        [549] Freddie Gibbs - 2012 - Baby Face Killa (CD) [FLAC] 10% 0.0 [downloading]
        [550] Freddie Gibbs - Cold Day In Hell [FLAC] 8% 0.0 [downloading]


Stop all torrents starting with fred.::

        (TS@172.16.1.9:9091)> ls | n=fred | stop
        > Stopping 3 torrents.

Start all torrents stopped torrents::

        (TS@172.16.1.9:9091)> ls | stopped | start
        > Starting 5 torrents.

Get a total count of torrents registered within the client.::

        (TS@172.16.1.9:9091)> ls | count
        598

An example of limiting output to a specific number of lines, In this case 5.::

        (TS@172.16.1.9:9091)> ls | 5 | count
        5

Counting the number of torrents using the btn tracker.::

        (TS@172.16.1.9:9091)> ls | t=btn | c
        296

Running commands without invoking the REPL prompt. All commands from the REPL interface are supported::

    $ ts_cli.py --exec "ls|age|r|5"
    [667] [DEF] Snowden.2016.720p.BluRay.x264 2% ra: 0.0 up: 0.0 kB/s dn: 95.0 kB/s [downloading]
    [666] [BTN] Saturday.Night.Live.S42E10.Casey.Affleck.720p.HDTV 100% ra: 0.0513 up: 16.0 kB/s dn: 0.0 kB/s [seeding]
    [665] [BTN] the.daily.show.2016.12.14.michael.k.williams.720p.hdtv.x264 100% ra: 0.0961 up: 0.0 kB/s dn: 0.0 kB/s [seeding]
    [664] [BTN] The.Last.Leg.S09E10.720p.HDTV.mkv 100% ra: 0.1106 up: 0.0 kB/s dn: 0.0 kB/s [seeding]
    [663] [BTN] Stephen.Colbert.2016.12.14.Neil.Patrick.Harris.720p 100% ra: 0.1875 up: 0.0 kB/s dn: 0.0 kB/s [seeding]

