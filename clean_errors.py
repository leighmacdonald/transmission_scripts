#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from transmissionrpc import Client, DEFAULT_PORT
"""
Simple script to clean out torrents that are no longer registered with
a tracker.
"""

REMOTE_MESSAGES = {
    "unregistered torrent"  # BTN / Gazelle
}

LOCAL_ERRORS = {
    "no data found"
}


def parse_args():
    parser = argparse.ArgumentParser(description='Clean out old torrents from the transmission client via RPC')
    parser.add_argument('--host', '-H', default='localhost', type=str, help="Transmission RPC Host")
    parser.add_argument('--port', '-p', default=DEFAULT_PORT, type=int, help="Transmission RPC Port")
    return parser.parse_args()


def make_client():
    args = parse_args()
    return Client(args.host, port=args.port)


def remove_unknown_torrents(client):
    for torrent in client.get_torrents():
        if torrent.error >= 2 and torrent.errorString.lower() in REMOTE_MESSAGES:
            client.stop_torrent(torrent.hashString)
            client.remove_torrent(torrent.hashString)
            print("Removed: {} {}\nReason: {}".format(
                torrent.name, torrent.hashString, torrent.errorString))


def remove_local_errors(client):
    for torrent in client.get_torrents():
        if torrent.error == 3:
            for errmsg in LOCAL_ERRORS:
                if errmsg in torrent.errorString.lower():
                    if torrent.status != "stopped":
                        client.stop_torrent(torrent.hashString)
                    client.remove_torrent(torrent.hashString)
                    print("Removed: {} {}\nReason: {}".format(
                        torrent.name, torrent.hashString, torrent.errorString))
                    break


if __name__ == "__main__":
    rpc_client = make_client()
    remove_unknown_torrents(rpc_client)
    remove_local_errors(rpc_client)
