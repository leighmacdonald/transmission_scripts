#!/usr/bin/env python
from distutils.core import setup
from os.path import dirname, join
from transmissionscripts import __VERSION__


setup(
    name='transmissionscripts',
    version=__VERSION__,
    include_package_data=True,
    license="MIT",
    requires=['transmissionrpc', 'termcolor'],
    description='Various scripts to manage transmission',
    author='Leigh MacDonald',
    author_email='leigh.macdonald@gmail.com',
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    url='https://github.com/leighmacdonald/transmission_scripts',
    packages=['transmissionscripts'],
    scripts=['scripts/ts_clean.py', 'scripts/ts_cli.py', 'scripts/ts_list.py'],
    download_url='https://github.com/leighmacdonald/transmission_scripts/tarball/{}'.format(__VERSION__),
    keywords=["torrent", "transmission", "p2p"],
    classifiers=[
        "Environment :: Console",
        "Topic :: Utilities"
    ]
)
