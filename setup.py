#!/usr/bin/env python3
from distutils.core import setup
from os.path import dirname, join
import sys

VERSION = "0.3.2"

if sys.platform == "win32":
    install_requires = ['transmissionrpc', 'termcolor', 'colorama', 'win_unicode_console']
else:
    install_requires = ['transmissionrpc', 'termcolor']

setup(
    name='transmissionscripts',
    version=VERSION,
    include_package_data=True,
    license="MIT",
    install_requires=install_requires,
    description='Various scripts to manage transmission',
    author='Leigh MacDonald',
    author_email='leigh.macdonald@gmail.com',
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    url='https://github.com/leighmacdonald/transmission_scripts',
    packages=['transmissionscripts'],
    scripts=['scripts/ts_clean.py', 'scripts/ts_cli.py', 'scripts/ts_list.py'],
    download_url='https://github.com/leighmacdonald/transmission_scripts/tarball/{}'.format(VERSION),
    keywords=["torrent", "transmission", "p2p"],
    classifiers=[
        "Environment :: Console",
        "Topic :: Utilities"
    ]
)
