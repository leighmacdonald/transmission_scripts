#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import argparse
import cmd

import termcolor

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from transmissionscripts import make_client, make_arg_parser, print_torrent_line, Filter, Sort, filter_torrents_by, \
    sort_torrents_by, find_tracker


class CmdError(Exception):
    pass


class TorrentCLI(cmd.Cmd):

    prompt = "(TS)$ "
    _cmd_print = ("p", "print")
    _cmd_count = ("c", "cnt", "count")
    _cmd_reverse = ("r", "rev", "reverse")

    def __init__(self, client):
        cmd.Cmd.__init__(self)
        self.client = client
        self.prompt = self._generate_prompt()

    def _generate_prompt(self):
        url = urlparse(self.client.url)
        return "(TS@{}:{})> ".format(url.hostname, url.port)

    def msg(self, msg, prefix=">>>", color="green"):
        print(termcolor.colored("{} {}".format(prefix, msg), color=color))

    def error(self, msg):
        self.msg(msg, "!!!", "red")

    def do_ls(self, line):
        args = [arg.strip().lower() for arg in line.split("|") if arg]
        try:
            torrents = self._apply_functions(self.client.get_torrents(), args)
            if not args:
                self.print_torrents(torrents)
        except CmdError as err:
            self.error(err)

    def do_exit(self, line):
        raise KeyboardInterrupt

    def print_torrents(self, torrents):
        for torrent in torrents:
            print_torrent_line(torrent)

    def _apply_functions(self, torrents, args):
        for i, arg in enumerate(args, start=1):
            try:
                if int(arg) <= 0:
                    print("Limit too low, must be positive integer: {}".format(arg))
                    # Bail early
                    return []
            except ValueError:
                is_int = False
            else:
                is_int = True
            if is_int:
                torrents = torrents[0:int(arg)]
                # Special case to print when limit was the last argument
                if i == len(args):
                    self.print_torrents(torrents)
            elif arg in self._cmd_print:
                self.print_torrents(torrents)
            elif arg in self._cmd_count:
                print(len(torrents))
                return []
            elif arg in self._cmd_reverse:
                torrents.reverse()
            elif arg in Filter.names:
                torrents = filter_torrents_by(torrents, key=getattr(Filter, arg))
            elif arg in Sort.names:
                torrents = sort_torrents_by(torrents, key=getattr(Sort, arg))
            elif arg in ("stop", "pause"):
                for torrent in torrents:
                    self.client.stop_torrent(torrent.hashString)
                self.msg("Stopping {} torrents.".format(len(torrents)))
            elif arg in ("start", "start"):
                for torrent in torrents:
                    self.client.start_torrent(torrent.hashString)
                self.msg("Starting {} torrents.".format(len(torrents)))
            elif "=" in arg:
                cmd_name, cmd_arg = arg.split("=")
                if cmd_name in ("n", "name"):
                    def filter_name(t):
                        return t.name.lower().startswith(cmd_arg)
                    torrents = filter_torrents_by(torrents, key=filter_name)
                elif cmd_name in ("t", "tracker"):
                    def filter_tracker(t):
                        return cmd_arg.lower() in find_tracker(t).lower()
                    torrents = filter_torrents_by(torrents, key=filter_tracker)
            else:
                raise CmdError("Unknown function: {}".format(arg))
        return torrents


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clean out old torrents from the transmission client via RPC',
        parents=[make_arg_parser()]
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        TorrentCLI(make_client(parse_args())).cmdloop()
    except KeyboardInterrupt:
        print("")
