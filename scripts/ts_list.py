#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script that will output a list of the currently loaded torrents. Various formatting, colouring, sorting
and filtering options exist.

"""
import argparse
from transmissionscripts import make_client, Sort, print_torrent_line, make_arg_parser, Filter


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
    torrents = rpc_client.get_torrents_by(
        filter_by=args.filter if args.filter else None,
        sort_by=args.sort if args.sort else None
    )

    # Output the results
    for torrent in torrents:
        print_torrent_line(torrent)

