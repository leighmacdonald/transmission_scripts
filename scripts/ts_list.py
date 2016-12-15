#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script that will output a list of the currently loaded torrents. Various formatting, colouring, sorting
and filtering options exist.
"""
import argparse
from transmissionscripts import make_client, sort_torrents_by, Sort, print_torrent_line, make_arg_parser, Filter, \
    filter_torrents_by


def parse_args():
    parser = argparse.ArgumentParser(parents=[make_arg_parser()])
    parser.add_argument('--sort', choices=Sort.names, default="id", help="Sort output by: id, progress, name, size")
    parser.add_argument('--filter', choices=Filter.names,
                        default="all", help="Filter to: all, active, downloading, seeding, paused, finished.")
    return parser.parse_args()


if __name__ == "__main__":
    # Get options and configure
    args = parse_args()
    rpc_client = make_client(args)

    # Fetch torrents performing filtering/sorting if requested
    torrents = rpc_client.get_torrents()
    if args.filter:
        torrents = filter_torrents_by(torrents, key=getattr(Filter, args.filter))
    if args.sort:
        torrents = sort_torrents_by(torrents, key=getattr(Sort, args.sort), reverse=False)

    # Output the results
    for torrent in torrents:
        print_torrent_line(torrent)

