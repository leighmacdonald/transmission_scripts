#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script that will output a list of the currently loaded torrents. Various formatting, colouring, sorting
and filtering options exist.
"""
import argparse

from transmissionscripts import make_client, sort_torrents_by, Sort, print_torrent_line, make_arg_parser


def parse_args():
    parser = argparse.ArgumentParser(parents=[make_arg_parser()])
    parser.add_argument('--sort_progress', action='store_true')
    parser.add_argument('--sort_name', action='store_true')
    parser.add_argument('--sort_size', action='store_true')
    parser.add_argument('--sort_active', action='store_true')
    parser.add_argument('--sort_id', action='store_true')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rpc_client = make_client(args)
    f = Sort.id
    if args.sort_progress:
        f = Sort.progress
    elif args.sort_name:
        f = Sort.name
    elif args.sort_size:
        f = Sort.size

    for torrent in sort_torrents_by(rpc_client.get_torrents(), key=f, reverse=False):
        print_torrent_line(torrent)

