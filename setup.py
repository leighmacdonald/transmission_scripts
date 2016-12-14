#!/usr/bin/env python
from distutils.core import setup

setup(
    name='Transmission Scripts',
    version='1.0',
    requires=['transmissionrpc'],
    description='Various scripts to manage transmission',
    author='Leigh MacDonald',
    author_email='leigh.macdonald@gmail.com',
    url='https://github.com/leighmacdonald/transmissionscripts',
    packages=['transmissionscripts'],
    scripts=['scripts/ts_clean.py']
)
