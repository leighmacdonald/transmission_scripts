import argparse
import sys
from time import sleep

from transmissionscripts import filesystem, natural_size
from transmissionscripts import make_client, make_arg_parser
try:
    # noinspection PyUnresolvedReferences
    import curses
except ImportError:
    if sys.platform == "win32":
        print("Please install the UniCurses package")
    else:
        print("Please install the python curses module")
    exit(1)

HEADER_SIZE = 4
BODY_SIZE = 6


def draw_header(scr):
    max_height, max_width = scr.getmaxyx()
    drives = {"/"}
    scr.addstr(0, 1, "Disk free: {}".format(", ".join(
        ["{} ({})".format(natural_size(filesystem.get_free_space(d)), d) for d in drives]
    )))
    scr.addstr(1, 1, "1")
    scr.addstr(2, 1, "2")
    scr.addstr(3, 1, "3s")
    scr.refresh()


def draw_footer(scr):
    max_height, max_width = scr.getmaxyx()
    scr.addstr(max_height-1, 2, "{}".format(max_height))
    scr.refresh()


def draw_body(scr):
    max_height, max_width = scr.getmaxyx()
    for i in range(0, max_height - 1):
        scr.addstr(i, 1, '10 divided by {}'.format(i))
    scr.refresh()


def top(args):
    scr = curses.initscr()
    #scr.start_color()
    curses.noecho()
    curses.cbreak()
    hx, wm = scr.getmaxyx()
    scr.keypad(True)
    try:
        header = curses.newwin(HEADER_SIZE, wm, 0, 0)
        body = curses.newwin(BODY_SIZE, wm, HEADER_SIZE, 0)
        while True:
            draw_header(header)
            draw_body(body)
            draw_footer(scr)
            sleep(0.2)
    except KeyboardInterrupt:
        curses.nocbreak()
        scr.keypad(False)
        curses.echo()
        curses.endwin()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Top like curses client for transmission',
        parents=[make_arg_parser()]
    )
    parser.add_argument("--rate", "-r", dest="rate", help="Update rate for data display", default=5.0, type=float)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        cli = make_client(cli_args)
        top(cli_args)
    except KeyboardInterrupt:
        print("")
