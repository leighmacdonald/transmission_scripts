#!/usr/bin/env python
# -*- coding: utf-8 -*-
from transmissionscripts import make_client, remove_unknown_torrents, remove_local_errors, clean_min_time_ratio

if __name__ == "__main__":
    rpc_client = make_client()
    remove_unknown_torrents(rpc_client)
    remove_local_errors(rpc_client)
    clean_min_time_ratio(rpc_client)
