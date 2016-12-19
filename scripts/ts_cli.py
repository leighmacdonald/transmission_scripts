#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""
import argparse
import cmd
import re
from datetime import timedelta, datetime
from transmissionscripts import colored, natural_size, find_all_trackers

try:
    from urllib.parse import urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
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
    _cmd_time = ("time",)

    _args_time = re.compile(r"(?P<dir>[<>])(?P<duration>\d+)(?P<unit>[mhdwMY])")

    def __init__(self, client):
        """

        :param client:
        :type client: transmissionscripts.TSClient
        """
        cmd.Cmd.__init__(self)
        self.client = client
        self.prompt = self._generate_prompt()

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.

        If this method is not overridden, it prints an error message and
        returns.

        """
        args = self._parse_line(line)
        if args[0] in ("total_size",):
            self.total_size()

        self.stdout.write('*** Unknown syntax: %s\n' % line)

    def _generate_prompt(self):
        url = urlparse(self.client.url)
        return "(TS@{}:{})> ".format(url.hostname, url.port)

    def msg(self, msg, prefix=">>>", color="green"):
        print(colored("{} {}".format(prefix, msg), color=color))

    def error(self, msg):
        self.msg(msg, "!!!", "red")

    def help_ls(self):
        print("HELP FOR LS")

    def _parse_line(self, line, sep="|"):
        return [arg.strip().lower() for arg in line.split(sep) if arg]

    def do_ls(self, line):
        parsed_args = self._parse_line(line)
        try:
            torrents = self._apply_functions(self.client.get_torrents(), parsed_args)
            if not parsed_args:
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
            elif arg in ("total_size",):
                self.total_size(torrents)
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

    def do_enablelimits(self, line):
        self.client.set_enabled_limits(True, False)
        self.msg("Enabled speed limits.")

    def do_disablelimits(self, line):
        self.client.set_enabled_limits(False, False)
        self.msg("Disabled speed limits.")

    def do_enablealtlimits(self, line):
        self.client.set_enabled_limits(True, True)
        self.msg("Enabled alt speed limits.")

    def do_disablealtlimits(self, line):
        self.client.set_enabled_limits(False, True)
        self.msg("Disabled alt speed limits.")

    def do_limit(self, line, alt=False):
        args = self._parse_line(line, " ")
        if not args:
            return self.error("Must supply 2 arguments: $upload_speed $download_speed")
        try:
            self.client.set_limits(speed_up=float(args[0]), speed_dn=float(args[1]), alt=alt)
        except TypeError:
            self.error("Failed to parse speeds, formats: 0 or 0.0")
        else:
            self.client.set_enabled_limits(True, alt=alt)
            self.msg("Set speed limits successfully to: {}/s up & {}/s down ".format(
                natural_size(float(args[0]) * 1000), natural_size(float(args[1]) * 1000)
            ))

    def do_altlimit(self, line):
        self.do_limit(line, True)

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

    def total_size(self, torrents=None):
        if torrents is None:
            torrents = self.client.get_torrents()
        self.msg("Total size for {} torrents: {}".format(
            len(torrents), natural_size(sum(t.totalSize for t in torrents))))
        return torrents

    def do_verify(self, line):
        ids = self._parse_line(line, " ")
        self.client.verify_torrent(ids)
        self.msg("Starting verify of {} torrents".format(len(ids)))

    def do_clientstats(self, line):
        torrents = self.client.get_torrents()
        stats = self.client.session_stats()

        # All Time totals
        print("[AllTime] Uploaded: {} Downloaded: {} Files: {} Active: {}".format(
            natural_size(stats.cumulative_stats['downloadedBytes']),
            natural_size(stats.cumulative_stats['uploadedBytes']),
            stats.cumulative_stats['filesAdded'],
            stats.cumulative_stats['secondsActive']
        ))

        # Session stats
        print("[Session] Uploaded: {} Downloaded: {} Files: {} Active: {} Free Space: {}".format(
            natural_size(stats.current_stats['downloadedBytes']),
            natural_size(stats.current_stats['uploadedBytes']),
            stats.current_stats['filesAdded'],
            stats.current_stats['secondsActive'],
            natural_size(stats.download_dir_free_space)
        ))
        print("[Stats  ] Current Speed: Up: {}/s / Dn: {}/s Active Torrents: {}".format(
            natural_size(stats.uploadSpeed),
            natural_size(stats.downloadSpeed),
            stats.torrentCount
        ))

        # Tracker info
        for tracker in find_all_trackers(torrents):
            def filter_tracker(t):
                return tracker.lower() in find_tracker(t).lower()
            tracker_torrents = filter_torrents_by(torrents, key=filter_tracker)
            print("[Tracker] Name: {} Torrents: {} Total Size: {}".format(
                tracker,
                len(tracker_torrents),
                natural_size(sum(t.totalSize for t in tracker_torrents))
            ))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clean out old torrents from the transmission client via RPC',
        parents=[make_arg_parser()]
    )
    parser.add_argument("--exec", "-x", dest="execute", help="Run a single command line string and exit without "
                                                             "opening the REPL.")
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    cli = TorrentCLI(make_client(cli_args))
    try:
        cli.onecmd(cli_args.execute) if cli_args.execute else cli.cmdloop()
    except KeyboardInterrupt:
        print("")
