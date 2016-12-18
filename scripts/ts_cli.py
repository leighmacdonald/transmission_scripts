#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""
import argparse
import cmd
import re
from datetime import timedelta, datetime

from transmissionscripts import colored

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
    _cmd_name = ("n", "name")
    _cmd_tracker = ("t", "tracker")
    _cmd_time = ("time")
    _args_time = re.compile(r"(?P<dir>[<>])(?P<duration>\d+)(?P<unit>[mhdwMY])")

    def __init__(self, client):
        """

        :param client:
        :type client: transmissionrpc.Client
        """
        cmd.Cmd.__init__(self)
        self.client = client
        self.prompt = self._generate_prompt()

    def _generate_prompt(self):
        url = urlparse(self.client.url)
        return "(TS@{}:{})> ".format(url.hostname, url.port)

    def msg(self, msg, prefix=">>>", color="green"):
        print(colored("{} {}".format(prefix, msg), color=color))

    def error(self, msg):
        self.msg(msg, "!!!", "red")

    def help_ls(self):
        print("HELP FOR LS")

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
                if i == len(args):
                    self.print_torrents(torrents)
            elif arg in Filter.names:
                torrents = filter_torrents_by(torrents, key=getattr(Filter, arg))
                if i == len(args):
                    self.print_torrents(torrents)
            elif arg in Sort.names:
                torrents = sort_torrents_by(torrents, key=getattr(Sort, arg))
                if i == len(args):
                    self.print_torrents(torrents)
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
                if cmd_name in self._cmd_name:
                    def filter_name(t):
                        return t.name.lower().startswith(cmd_arg)
                    torrents = filter_torrents_by(torrents, key=filter_name)
                    if i == len(args):
                        self.print_torrents(torrents)
                elif cmd_name in self._cmd_tracker:
                    def filter_tracker(t):
                        return cmd_arg.lower() in find_tracker(t).lower()
                    torrents = filter_torrents_by(torrents, key=filter_tracker)
                    self.conditional_print(torrents, i == len(args))
                elif cmd_name in self._cmd_time:
                    m = self._args_time.match(cmd_arg)
                    if not m:
                        return 0
                    td_args = {}
                    split, duration, unit = m.groups()
                    duration = int(duration)
                    # mhdwMY
                    if unit == "w":
                        td_args['weeks'] = duration
                    elif unit == "m":
                        td_args['minutes'] = duration
                    elif unit == "h":
                        td_args['hours'] = duration
                    elif unit == "d":
                        td_args['days'] = duration
                    elif unit == "M":
                        td_args['days'] = duration * 30.5
                    elif unit == "Y":
                        td_args['days'] = duration * 365
                    filter_date = datetime.now() - timedelta(**td_args)

                    def filter_time(t):
                        if split == ">":
                            return t.date_added < filter_date
                        else:
                            return t.date_added > filter_date

                    torrents = filter_torrents_by(torrents, key=filter_time)
                    self.conditional_print(torrents, i == len(args))

            else:
                raise CmdError("Unknown function: {}".format(arg))
        return torrents

    def do_stop(self, line):
        ids = line.split(" ")
        if not ids:
            self.error("Must supply at least 1 id")
        self.client.stop_torrent(ids)
        self.msg("Stopped {} torrents".format(len(ids)))

    def do_start(self, line):
        ids = line.split(" ")
        if not ids:
            self.error("Must supply at least 1 id")
        self.client.start_torrent(ids)
        self.msg("Started {} torrents".format(len(ids)))

    def do_startall(self, line):
        self.client.start_all()
        self.msg("Started all torrents")

    def conditional_print(self, torrents, condition=False):
        if condition:
            self.print_torrents(torrents)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clean out old torrents from the transmission client via RPC',
        parents=[make_arg_parser()]
    )
    parser.add_argument("--exec", "-x", dest="execute", help="Run a single command line string and exit without "
                                                             "opening the REPL.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cli = TorrentCLI(make_client(args))
    try:
        cli.onecmd(args.execute) if args.execute else cli.cmdloop()
    except KeyboardInterrupt:
        print("")
