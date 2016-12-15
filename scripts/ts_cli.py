#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import argparse
import cmd
from urllib.parse import urlparse

from transmissionscripts import make_client, make_arg_parser, print_torrent_line, Filter, Sort, filter_torrents_by, \
    sort_torrents_by


class TorrentCLI(cmd.Cmd):

    prompt = "(TS)$ "

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.prompt = self._generate_prompt()

    def _generate_prompt(self):
        url = urlparse(self.client.url)
        return "(TS@{}:{})> ".format(url.hostname, url.port)

    def do_ls(self, line):
        torrents = self._apply_filters(line, self.client.get_torrents())
        for torrent in torrents:
            print_torrent_line(torrent)

    def _apply_filters(self, line, torrents):
        for arg in [arg.strip().lower() for arg in line.split("|") if arg]:
            if arg in Filter.names:
                torrents = filter_torrents_by(torrents, key=getattr(Filter, arg))
            elif arg in Sort.names:
                torrents = sort_torrents_by(torrents, key=getattr(Sort, arg))
            elif arg in ("stop", "pause"):
                for torrent in torrents:
                    self.client.stop_torrent(torrent.hashString)
            elif arg in ("start", "start"):
                for torrent in torrents:
                    self.client.start_torrent(torrent.hashString)
            elif "=" in arg:
                cmd_name, cmd_arg = arg.split("=")
                if cmd_name in ("n", "name"):
                    def filter_name(torrent):
                        return torrent.name.lower().startswith(cmd_arg)
                    torrents = filter_torrents_by(torrents, key=filter_name)
        return torrents


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clean out old torrents from the transmission client via RPC',
        parents=[make_arg_parser()]
    )
    return parser.parse_args()


if __name__ == "__main__":
    TorrentCLI(make_client(parse_args())).cmdloop()