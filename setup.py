#!/usr/bin/env python
from distutils.core import setup

setup(
    name='transmissionscripts',
    version='0.2',
    requires=['transmissionrpc', 'termcolor'],
    description='Various scripts to manage transmission',
    author='Leigh MacDonald',
    author_email='leigh.macdonald@gmail.com',
    url='https://github.com/leighmacdonald/transmissionscripts',
    packages=['transmissionscripts'],
    scripts=['scripts/ts_clean.py', 'scripts/ts_cli.py', 'scripts/ts_list.py'],
    download_url='https://github.com/leighmacdonald/transmission_scripts/tarball/0.2',
    keywords=["torrent", "transmission", "p2p"]
)
