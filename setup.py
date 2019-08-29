#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright 2019 Artem Yamshanov, me [at] anticode.ninja

from __future__ import print_function
from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

if sys.version_info < (3, 3):
    print('Sorry, only python>=3.3 is supported', file=sys.stderr)
    sys.exit(1)

with open(path.join(here, 'LICENSE.txt'), encoding='utf-8') as f:
    license = f.read()
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='antilogconverter',
    version='0.8.0',

    description='convert logs from different formats to antilogviewer nlog format',
    long_description=long_description,

    url='https://github.com/anticodeninja/antilogconverter',

    maintainer='anticodeninja',
    author='anticodeninja',

    license=license,

    packages=find_packages(),
    install_requires=[],
    python_requires='>=3.3',

    entry_points={
        'console_scripts' : [
            'antilogconverter=antilogconverter:main',
        ],
    },
)
