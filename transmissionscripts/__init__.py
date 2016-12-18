#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple set of functionality to manage a local or remote transmission instance. You can think of this
as a set of helper functions for interacting with the transmissionrpc python module.
"""
import argparse
import errno
import logging
import math
import sys
from json import dumps, load
from os.path import expanduser, join, exists, isdir
from os import makedirs, environ
from transmissionrpc import Client, DEFAULT_PORT


def _supports_color():
    """ Returns True if the running system's terminal supports color,
    and False otherwise.

    If the FORCE_COLOR environment variable is used, auto detection methods will be skipped.
    - 1 enables force ansi colours
    - 0 to disable it

    """
    plat = sys.platform
    # Silly hack to force use of ansi color codes when cannot be detected properly.
    if 'FORCE_COLOR' in environ:
        return int(environ['FORCE_COLOR']) == 1
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in environ)
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        if plat == 'win32':
            try:
                # noinspection PyUnresolvedReferences
                import colorama
            except ImportError:
                pass
            else:
                colorama.init()
                return True
        return False
    return True


HAS_COLOUR = _supports_color()

logging.basicConfig()

logger = logging.getLogger('transmissionscripts')
logger.setLevel(logging.INFO)

CONFIG_DIR = expanduser("~/.config/transmissionscripts")
CONFIG_FILE = join(CONFIG_DIR, "config.json")

REMOTE_MESSAGES = {
    "unregistered torrent"  # BTN / Gazelle
}

LOCAL_ERRORS = {
    "no data found"
}

# Seed a bit longer than required to account for any weirdness
SEED_TIME_BUFFER = 1.1

RULES_DEFAULT = 'DEFAULT'

CONFIG = {
    'CLIENT': {
        'host': 'localhost',
        'port': DEFAULT_PORT,
        'user': None,
        'password': None
    },
    'RULES': {
        'apollo': {
            'name': 'apollo',
            'min_time': int((3600 * 24 * 30) * SEED_TIME_BUFFER),
            'max_ratio': 2.0
        },
        'landof.tv': {
            'name': 'btn',
            'min_time': int((3600 * 120.0) * SEED_TIME_BUFFER),
            'max_ratio': 1.0
        },
        RULES_DEFAULT: {
            'name': 'default',
            'min_time': int((3600 * 240) * SEED_TIME_BUFFER),
            'max_ratio': 2.0
        }
    }
}


def colored(msg, color=None, on_color=None, attrs=None):
    if HAS_COLOUR:
        from termcolor import colored as c
        return c(msg, color=color, on_color=on_color, attrs=attrs)
    else:
        return msg


def find_rule_set(torrent):
    """ Return the rule set associated with the torrent.

    :param torrent: Torrent instance to search
    :type torrent: transmissionrpc.Torrent
    :return: A matching rule set if it exists, otherwise a default rule set
    :rtype: dict
    """

    for key in CONFIG['RULES']:
        for tracker in torrent.trackers:
            if key in tracker['announce'].lower():
                return CONFIG['RULES'][key]
    return CONFIG['RULES'][RULES_DEFAULT]


# noinspection PyTypeChecker
def find_tracker(torrent):
    for key in CONFIG['RULES']:
        for tracker in torrent.trackers:
            if key in tracker['announce'].lower():
                return CONFIG['RULES'][key]['name']
    return CONFIG['RULES'][RULES_DEFAULT]['name']


def make_arg_parser():
    """ Create a new argparse instance that can optionally be extended to include custom
    options before passing the options into the client as demonstrated below.

    >>> def parse_args():
    >>>     parser = make_arg_parser()
    >>>     parser.add_argument('--sort_progress', action='store_true')
    >>>     return parser.parse_args()
    >>> rpc_client = make_client(parse_args())

    :return: New argparse instance
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--host', '-H', default=None, type=str, help="Transmission RPC Host")
    parser.add_argument('--port', '-p', type=int, default=0, help="Transmission RPC Port")
    parser.add_argument('--user', '-u', default=None, help="Optional username", dest="user")
    parser.add_argument('--password', '-P', default=None, help="Optional password", dest='password')
    parser.add_argument('--generate_config', '-g', dest='generate', action='store_true',
                        help="Generate a config file that can be used to override defaults")
    parser.add_argument('--force', '-f', help="Overwrite existing files",
                        dest='force', action='store_true')
    return parser


def parse_args():
    """ Trivial shortcut to calling the default argparse.parse_args()

    :return:
    """
    return make_arg_parser().parse_args()


def find_config():
    if not exists(CONFIG_FILE):
        return None
    return CONFIG_FILE


def mkdir_p(path):
    try:
        makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and isdir(path):
            pass
        else:
            raise


def generate_config(overwrite=False):
    if exists(CONFIG_FILE) and not overwrite:
        logger.fatal("Config file exists already! Use -f to overwrite it.")
        return False
    if not exists(CONFIG_DIR):
        mkdir_p(CONFIG_DIR)
    with open(CONFIG_FILE, 'w') as cf:
        cf.write(dumps(CONFIG, sort_keys=True, indent=4, separators=(',', ': ')))
    return True


def load_config(path=None):
    global CONFIG
    if not path:
        path = find_config()
    if path and exists(path):
        CONFIG = load(open(path))
        logger.debug("Loaded config file: {}".format(path))
    return False


class TSClient(Client):
    def get_torrents_by(self, sort_by=None, filter_by=None, reverse=False):
        torrents = self.get_torrents()
        if filter_by:
            torrents = filter_torrents_by(torrents, key=getattr(Filter, filter_by))
        if sort_by:
            torrents = sort_torrents_by(torrents, key=getattr(Sort, sort_by), reverse=reverse)
        return torrents


def make_client(args=None):
    """ Create a new transmission RPC client

    If you want to parse more than the standard CLI arguments, like when creating a new customized
    script, you can append your options to the argument parser.

    :param args: Optional CLI args passed in.
    :return:
    """
    if args is None:
        args = parse_args()
    if args.generate:
        generate_config(args.force)
    load_config()
    return TSClient(
        args.host or CONFIG['CLIENT']['host'],
        port=args.port or CONFIG['CLIENT']['port'],
        user=args.user or CONFIG['CLIENT']['user'],
        password=args.password or CONFIG['CLIENT']['password']
    )


class Filter(object):
    names = (
        "all",
        "active",
        "downloading",
        "seeding",
        "stopped",
        "finished"
    )

    @staticmethod
    def all(t):
        return t

    @staticmethod
    def active(t):
        return t.rateUpload > 0 or t.rateDownload > 0

    @staticmethod
    def downloading(t):
        return t.status == 'downloading'

    @staticmethod
    def seeding(t):
        return t.status == 'seeding'

    @staticmethod
    def stopped(t):
        return t.status == 'stopped'

    @staticmethod
    def finished(t):
        return t.status == 'finished'

    @staticmethod
    def paused(t):
        return t.status == 'paused'


def filter_torrents_by(torrents, key=Filter.all):
    """

    :param key:
    :param torrents:
    :return: []transmissionrpc.Torrent
    """
    filtered_torrents = []
    for torrent in torrents:
        if key(torrent):
            filtered_torrents.append(torrent)
    return filtered_torrents


class Sort(object):
    """ Defines methods for sorting torrent sequences """

    names = (
        "id",
        "progress",
        "name",
        "size",
        "ratio",
        "speed",
        "speed_up",
        "speed_down"
    )

    @staticmethod
    def progress(t):
        return t.progress

    @staticmethod
    def name(t):
        return t.name.lower()

    @staticmethod
    def size(t):
        return t.totalSize

    @staticmethod
    def id(t):
        return t.id

    @staticmethod
    def ratio(t):
        return t.ratio

    @staticmethod
    def speed(t):
        return t.rateUpload + t.rateDownload

    @staticmethod
    def speed_up(t):
        return t.rateUpload

    @staticmethod
    def speed_down(t):
        return t.rateDownload


def sort_torrents_by(torrents, key=Sort.name, reverse=False):
    return sorted(torrents, key=key, reverse=reverse)

_reset_color = colored("", "white")


def white_on_blk(t):
    return colored(t, "white")


def green_on_blk(t):
    return colored(t, "green") + _reset_color


def yellow_on_blk(t):
    return colored(t, "yellow") + _reset_color


def red_on_blk(t):
    return colored(t, "red") + _reset_color


def cyan_on_blk(t):
    return colored(t, "cyan") + _reset_color


def print_torrent_line(torrent, colourize=True):
    print("[{}] [{}] {} {:.0%}{} ra: {} up: {} dn: {} [{}]".format(
        white_on_blk(torrent.id),
        find_tracker(torrent),
        print_pct(torrent) if colourize else torrent.name,
        torrent.progress / 100.0,
        white_on_blk(""),
        red_on_blk(torrent.ratio) if torrent.ratio < 1.0 else green_on_blk(torrent.ratio),
        green_on_blk(natural_size(float(torrent.rateUpload)) + "/s") if torrent.rateUpload else "0.0 kB/s",
        green_on_blk(natural_size(float(torrent.rateDownload)) + "/s") if torrent.rateDownload else "0.0 kB/s",
        yellow_on_blk(torrent.status)
    ))


def print_pct(torrent, complete='green', incomplete='red'):
    completed = int(math.floor(len(torrent.name) * (torrent.progress / 100.0)))
    t = "{}{}".format(
        colored(torrent.name[0:completed], complete, attrs=['bold']),
        colored(torrent.name[completed:], incomplete, attrs=['bold'])
    )
    return t


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
    logger.info("Removed: {} {}\nReason: {}".format(torrent.name, torrent.hashString, reason))


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
        rule_set = find_rule_set(torrent)
        if torrent.ratio > rule_set['max_ratio']:
            remove_torrent(client, torrent, "max_ratio threshold passed", dry_run=False)
        if torrent.secondsSeeding > rule_set['min_time']:
            remove_torrent(client, torrent, "min_time threshold passed", dry_run=False)


suffixes = {
    'decimal': ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
    'binary': ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    'gnu': "KMGTPEZY",
}


# noinspection PyUnboundLocalVariable
def natural_size(value, binary=False, gnu=False, fmt='%.1f'):
    """ Format a number of byteslike a human readable filesize (eg. 10 kB).  By
    default, decimal suffixes (kB, MB) are used.  Passing binary=true will use
    binary suffixes (KiB, MiB) are used and the base will be 2**10 instead of
    10**3.  If ``gnu`` is True, the binary argument is ignored and GNU-style
    (ls -sh style) prefixes are used (K, M) with the 2**10 definition.
    """
    if gnu:
        suffix = suffixes['gnu']
    elif binary:
        suffix = suffixes['binary']
    else:
        suffix = suffixes['decimal']

    base = 1024 if (gnu or binary) else 1000
    bytes = float(value)

    if bytes == 1 and not gnu:
        return '1 Byte'
    elif bytes < base and not gnu:
        return '%d Bytes' % bytes
    elif bytes < base and gnu:
        return '%dB' % bytes

    for i, s in enumerate(suffix):
        unit = base ** (i + 2)
        if bytes < unit and not gnu:
            return (fmt + ' %s') % ((base * bytes / unit), s)
        elif bytes < unit and gnu:
            return (fmt + '%s') % ((base * bytes / unit), s)
    if gnu:
        return (fmt + '%s') % ((base * bytes / unit), s)
    return (fmt + ' %s') % ((base * bytes / unit), s)
