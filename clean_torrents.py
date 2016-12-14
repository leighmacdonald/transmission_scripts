#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script to clean out torrents that should no longer be tracked within
the client.
"""
import argparse
from transmissionrpc import Client
from transmissionrpc import DEFAULT_PORT


REMOTE_MESSAGES = {
    "unregistered torrent"  # BTN / Gazelle
}

LOCAL_ERRORS = {
    "no data found"
}

# Seed a bit longer than required to account for any weirdness
SEED_TIME_BUFFER = 1.1


RULES_DEFAULT = 'DEFAULT'

RULES = {
    'apollo.rip/': {
        'min_time': (3600 * 24 * 30) * SEED_TIME_BUFFER,
        'max_ratio': 2.0
    },
    'landof.tv/': {
        'min_time': (3600 * 120.0) * SEED_TIME_BUFFER,
        'max_ratio': 1.0
    },
    RULES_DEFAULT: {
        'min_time': (3600 * 240) * SEED_TIME_BUFFER,
        'max_ratio': 2.0
    }
}


def find_rule_set(trackers):
    for key in RULES:
        for tracker in trackers:
            if key in tracker['announce'].lower():
                return RULES[key]
    return RULES[RULES_DEFAULT]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clean out old torrents from the transmission client via RPC')
    parser.add_argument('--host', '-H', default='localhost', type=str, help="Transmission RPC Host")
    parser.add_argument('--port', '-p', default=DEFAULT_PORT, type=int, help="Transmission RPC Port")
    parser.add_argument('--user', '-u', default=None, help="Optional username", dest="user")
    parser.add_argument('--password', '-P', default=None, help="Optional password", dest='password')
    return parser.parse_args()


def make_client():
    args = parse_args()
    return Client(args.host, port=args.port, user=args.user, password=args.password)


def remove_torrent(client, torrent, reason="None", dry_run=False):
    """ Remove a torrent from the client stopping it first if its in a started state.

    :param client: Transmission RPC Client
    :type client: transmissionrpc.Client
    :param torrent: Torrent instance to remove
    :type torrent: transmissionrpc.Torrent
    :param reason: Reason for removal
    :type reason: str
    :param dry_run: Do a dry run without actually running any commands
    :type dry_run: bool
    :return:
    """
    if torrent.status != "stopped":
        if not dry_run:
            client.stop_torrent(torrent.hashString)
    if not dry_run:
        client.remove_torrent(torrent.hashString, delete_data=False)
    print("Removed: {} {}\nReason: {}".format(torrent.name, torrent.hashString, reason))


def remove_unknown_torrents(client):
    """ Remove torrents that the remote tracker no longer tracking for whatever
    reason, usually removed by admins.

    :param client: Transmission RPC Client
    :type client: transmissionrpc.Client
    """
    for torrent in client.get_torrents():
        if torrent.error >= 2 and torrent.errorString.lower() in REMOTE_MESSAGES:
            remove_torrent(client, torrent)


def remove_local_errors(client):
    """ Removed torrents that have local filesystem errors, usually caused by moving data
    outside of transmission.

    :param client: Transmission RPC Client
    :type client: transmissionrpc.Client
    """
    for torrent in client.get_torrents():
        if torrent.error == 3:
            for errmsg in LOCAL_ERRORS:
                if errmsg in torrent.errorString.lower():
                    remove_torrent(client, torrent)
                    break


def clean_min_time_ratio(client):
    """ Remove torrents that are either have seeded enough time-wise or ratio-wise.
    The correct rule set is determined by checking the torrent announce url and
    matching it to a specific rule set defined above.

    :param client: Transmission RPC Client
    :type client: transmissionrpc.Client
    """
    for torrent in client.get_torrents():
        if torrent.error or torrent.status != "seeding":
            continue
        rule_set = find_rule_set(torrent.trackers)
        if torrent.ratio > rule_set['max_ratio']:
            remove_torrent(client, torrent, "max_ratio threshold passed", dry_run=False)
        if torrent.secondsSeeding > rule_set['min_time']:
            remove_torrent(client, torrent, "min_time threshold passed", dry_run=False)


if __name__ == "__main__":
    rpc_client = make_client()
    remove_unknown_torrents(rpc_client)
    remove_local_errors(rpc_client)
    clean_min_time_ratio(rpc_client)
