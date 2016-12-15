# transmissionscripts

## What Is This?

A set of scripts and functions to help managing a [Transmission](https://transmissionbt.com/) instance via
its RPC interface.

## Included Scripts

Below is a list of the scripts along with simple descriptions of their functionality.

### ts_clean.py

This script will scan active torrents for those which qualify to be removed from the client. This
tool reads in the config file and uses the tracker rules definitions defined in there to make decisions
as to what to remove.

### ts_cli.py

A unix shell like interpreter. You can chan commands together similar to using pipes in any
standard unix-like shell. Filters and commands are separated by | characters.

The main initial command to use is `ls`. If you give no arguments it will just list
out all torrents, similar to ls on a unix command line listing files.

Some filters available:

- Filter by name: n=prefix_to_search_for
- Filter by tracker: t=tracker_key_prefix
- Filter by status: all, active, downloading, seeding, stopped, finished

Some Commands available:

- start: Start all the torrents passed to it.
- stop: Stop all the torrents passed to it.
- count: Count the current torrents including filtering.
- any integer: Using any positive integer will limit torrent results to that value.


    (TS@172.16.1.9:9091)> ls | n=fred | active
    [548] Freddie Gibbs - 2013 - ESGN 18% 0.0 [downloading]
    [549] Freddie Gibbs - 2012 - Baby Face Killa (CD) [FLAC] 10% 0.0 [downloading]
    [550] Freddie Gibbs - Cold Day In Hell [FLAC] 8% 0.0 [downloading]
    (TS@172.16.1.9:9091)> ls | n=fred | stop
    > Stopping 3 torrents.
    (TS@172.16.1.9:9091)> ls | stopped | start
    > Starting 5 torrents.
    (TS@172.16.1.9:9091)> ls | count
    598
    (TS@172.16.1.9:9091)> ls | 5 | count
    5
    (TS@172.16.1.9:9091)>

