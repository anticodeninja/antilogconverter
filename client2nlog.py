#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import re


TIME_RE = re.compile('Time:\s*([^\n]+)\s*', re.MULTILINE)
LEVEL_RE = re.compile('Type:\s*([^\n]+)\s*', re.MULTILINE)
SOURCE_RE = re.compile('Source:\s*([^\n]+)\s*', re.MULTILINE)
COMMENT_RE = re.compile('Comment:\s*([\S\s]+)\s*', re.MULTILINE)
TIME_REORDER_RE = re.compile('(\d+)\.(\d+)\.(\d+)\s+(\d+:\d+:\d+\.\d+)')


parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('output', nargs='?')
args = parser.parse_args()

buf = []

def extract(re, string):
    match = re.search(string)
    return match.group(1).strip() if match else None

def flush():
    if len(buf) == 0:
        return

    data = ''.join(buf)
    buf.clear()

    try:
        result = [extract(x, data) for x in (TIME_RE, LEVEL_RE, SOURCE_RE, COMMENT_RE)]

        result[0] = '{2}-{1}-{0} {3}'.format(*TIME_REORDER_RE.match(result[0]).groups())

        if result[1] is None:
            result[1] = 'INFO'
        else:
            result[1] = result[1].upper()
            if result[1] == 'INFORMATION':
                result[1] = 'INFO'

        if result[2] is None:
            result[2] = 'UNKNOWN'

        print('|'.join(result), file=output_file)
    except Exception as e:
        print(e, '\n', data.encode())

with open(args.input, 'r', encoding='utf-8') as input_file:
    with open(args.output or os.path.splitext(args.input)[0] + '_nlog.log', 'w', encoding='utf-8') as output_file:
        for line in input_file:
            if '-----------------------------------------------' in line:
                flush()
            buf.append(line)
        flush()
