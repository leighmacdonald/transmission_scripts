#!/usr/bin/env python3
"""

"""
# -*- coding: utf-8 -*-
import argparse
from transmissionscripts import make_client, remove_unknown_torrents, remove_local_errors, clean_min_time_ratio, \
    make_arg_parser


def parse_args():
    parser = argparse.ArgumentParser(
        description='Clean out old torrents from the transmission client via RPC',
        parents=[make_arg_parser()]
    )
    return parser.parse_args()


if __name__ == "__main__":
    rpc_client = make_client(parse_args())
    remove_unknown_torrents(rpc_client)
    remove_local_errors(rpc_client)
    clean_min_time_ratio(rpc_client)
