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
import transmissionrpc


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
        'port': transmissionrpc.DEFAULT_PORT,
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


# noinspection PyPackageRequirements,PyUnresolvedReferences
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
                import colorama
                import win_unicode_console
            except ImportError:
                logger.warning("Failed to import color/unicode support for win32")
            else:
                win_unicode_console.enable()
                colorama.init()
                return True
        return False
    return True


HAS_COLOUR = _supports_color()


def colored(msg, color=None, on_color=None, attrs=None):
    """Print a message to the console using colorized ANSI codes.

    :param msg: Message to colorize
    :type msg: str
    :param color: One of `termcolor.COLORS`
    :type color: str
    :param on_color: Background color
    :type on_color: str
    :param attrs:
    :return: str
    """
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
    """ Find the tracker that the torrent is associated with. This uses the announce
    url to determine it based on the configured trackers. It will return default if it
    cannot find a matching tracker or if you have not configured any custom tracker rules.

    :param torrent: Torrent to search
    :type torrent: transmissionrpc.Torrent
    :return:
    """
    for key in CONFIG['RULES']:
        for tracker in torrent.trackers:
            if key in tracker['announce'].lower():
                return CONFIG['RULES'][key]['name']
    return CONFIG['RULES'][RULES_DEFAULT]['name']


def make_arg_parser():
    """ Create a new argparse instance that can optionally be extended to include custom
    options before passing the options into the client as demonstrated below.

    >>> def parse_args():
    >>>     parser = argparse.ArgumentParser(
    >>>         description='Clean out old torrents from the transmission client via RPC',
    >>>         parents=[make_arg_parser()]
    >>>     )
    >>>     parser.add_argument("--example", "-e", dest="example", help="Example command")
    >>>     return parser.parse_args()
    >>> args = parse_args()


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


def mkdir_p(path):
    """mimics the standard mkdir -p functionality when creating directories

    :param path:
    :return:
    """
    try:
        makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and isdir(path):
            pass
        else:
            raise


def generate_config(overwrite=False):
    """Generate a new config file based on the value of the CONFIG global variable.

    This function will cause a fatal error if trying to overwrite an exiting file
    without setting overwrite to True.

    :param overwrite: Overwrite existing config file
    :type overwrite: bool
    :return: Create status
    :rtype: bool
    """
    if exists(CONFIG_FILE) and not overwrite:
        logger.fatal("Config file exists already! Use -f to overwrite it.")
        return False
    if not exists(CONFIG_DIR):
        mkdir_p(CONFIG_DIR)
    with open(CONFIG_FILE, 'w') as cf:
        cf.write(dumps(CONFIG, sort_keys=True, indent=4, separators=(',', ': ')))
    return True


def load_config(path=None):
    """Load a config file from disk using the default location if it exists. If path is defined
    it will be used instead of the default path.

    :param path: Optional path to config file
    :type path: str
    :return: Load status
    :rtype: bool
    """
    global CONFIG
    if not path:
        path = CONFIG_FILE
    if path and exists(path):
        CONFIG = load(open(path))
        logger.debug("Loaded config file: {}".format(path))
        return True
    return False


class TSClient(transmissionrpc.Client):
    """ Basic subclass of the standard transmissionrpc client which provides some simple
    helper functionality.
    """

    def get_torrents_by(self, sort_by=None, filter_by=None, reverse=False):
        """This method will call get_torrents and then perform any sorting or filtering
        actions requested on the returned torrent set.

        :param sort_by: Sort key which must exist in `Sort.names` to be valid;
        :type sort_by: str
        :param filter_by:
        :type filter_by: str
        :param reverse:
        :return: Sorted and filter torrent list
        :rtype: transmissionrpc.Torrent[]
        """
        torrents = self.get_torrents()
        if filter_by:
            torrents = filter_torrents_by(torrents, key=getattr(Filter, filter_by))
        if sort_by:
            torrents = sort_torrents_by(torrents, key=getattr(Sort, sort_by), reverse=reverse)
        return torrents

    def set_limits(self, speed_up=None, speed_dn=None, alt=False):
        kwargs = {}
        if alt:
            if speed_up is not None:
                kwargs['alt_speed_up'] = speed_up
            if speed_dn is not None:
                kwargs['alt_speed_down'] = speed_up
        else:
            if speed_up is not None:
                kwargs['speed_limit_up'] = speed_up
            if speed_dn is not None:
                kwargs['speed_limit_down'] = speed_dn
        self.set_session(**kwargs)

    def set_enabled_limits(self, status, alt=False):
        kwargs = {}
        if alt:
            kwargs['alt_speed_enabled'] = status
        else:
            kwargs['speed_limit_down_enabled'] = int(status)
            kwargs['speed_limit_up_enabled'] = int(status)
        self.set_session(**kwargs)

    def set_peer_limit(self, limits, is_global=True):
        if is_global:
            self.set_session(peer_limit_global=limits)
        else:
            self.set_session(peer_limit=limits)

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
    """A set of filtering operations that can be used against a list of torrent objects"""

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
    def lifetime(t):
        return t.date_added


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


def find_all_trackers(torrents):
    trackers = set()
    for torrent in torrents:
        trackers.add(find_tracker(torrent))
    return trackers


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
        "speed_down",
        "status",
        "queue",
        "age",
        "activity"
    )

    @staticmethod
    def activity(t):
        return t.date_active

    @staticmethod
    def age(t):
        return t.date_added

    @staticmethod
    def queue(t):
        return t.queue_position

    @staticmethod
    def status(t):
        return t.status

    @staticmethod
    def progress(t):
        return t.progress

    @staticmethod
    def name(t):
        return t.name.lower()

    @staticmethod
    def size(t):
        return -t.totalSize

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
    return "{}{}".format(colored(t, "green"), _reset_color)


def yellow_on_blk(t):
    return "{}{}".format(colored(t, "yellow"), _reset_color)


def red_on_blk(t):
    return "{}{}".format(colored(t, "red"), _reset_color)


def cyan_on_blk(t):
    return "{}{}".format(colored(t, "cyan"), _reset_color)


def magenta_on_blk(t):
    return "{}{}".format(colored(t, "magenta"), _reset_color)


def print_torrent_line(torrent, colourize=True):
    name = torrent.name
    progress = torrent.progress / 100.0
    print("[{}] [{}] {} {}[{}/{}]{} ra: {} up: {} dn: {} [{}]".format(
        white_on_blk(torrent.id),
        find_tracker(torrent),
        print_pct(torrent) if colourize else name.decode("latin-1"),
        white_on_blk(""),
        red_on_blk("{:.0%}".format(progress)) if progress < 1 else green_on_blk("{:.0%}".format(progress)),
        magenta_on_blk(natural_size(torrent.totalSize)),
        white_on_blk(""),
        red_on_blk(torrent.ratio) if torrent.ratio < 1.0 else green_on_blk(torrent.ratio),
        green_on_blk(natural_size(float(torrent.rateUpload)) + "/s") if torrent.rateUpload else "0.0 kB/s",
        green_on_blk(natural_size(float(torrent.rateDownload)) + "/s") if torrent.rateDownload else "0.0 kB/s",
        yellow_on_blk(torrent.status)
    ))


def print_pct(torrent, complete='green', incomplete='red'):
    """Prints out a torrents name using the complete color and percentage to determine how many characters
    to colourize. The remaining percentage is coloured in the incomplete colour.

    :param torrent: Torrent to use for name data
    :type torrent: transmissionrpc.Torrent
    :param complete: Complete colour keyword
    :type complete: str
    :param incomplete: Incomplete colour keyword
    :type incomplete: str
    :return: Colorized string
    :rtype: str
    """
    name = torrent.name
    completed = int(math.floor(len(name) * (torrent.progress / 100.0)))
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


_SUFFIXES = {
    'decimal': ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
    'binary': ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    'gnu': "KMGTPEZY",
}


# noinspection PyUnboundLocalVariable
def natural_size(value, binary=False, gnu=False, fmt='%.1f'):
    """ Format a number of bytes-like a human readable file size (eg. 10 kB).  By
    default, decimal suffixes (kB, MB) are used.  Passing binary=true will use
    binary suffixes (KiB, MiB) are used and the base will be 2**10 instead of
    10**3.  If ``gnu`` is True, the binary argument is ignored and GNU-style
    (ls -sh style) prefixes are used (K, M) with the 2**10 definition.
    """
    if gnu:
        suffix = _SUFFIXES['gnu']
    elif binary:
        suffix = _SUFFIXES['binary']
    else:
        suffix = _SUFFIXES['decimal']

    base = 1024 if (gnu or binary) else 1000
    byte_total = float(value)

    if byte_total == 1 and not gnu:
        return '1 Byte'
    elif byte_total < base and not gnu:
        return '%d Bytes' % byte_total
    elif byte_total < base and gnu:
        return '%dB' % byte_total

    for i, s in enumerate(suffix):
        unit = base ** (i + 2)
        if byte_total < unit and not gnu:
            return (fmt + ' %s') % ((base * byte_total / unit), s)
        elif byte_total < unit and gnu:
            return (fmt + '%s') % ((base * byte_total / unit), s)
    if gnu:
        return (fmt + '%s') % ((base * byte_total / unit), s)
    return (fmt + ' %s') % ((base * byte_total / unit), s)
