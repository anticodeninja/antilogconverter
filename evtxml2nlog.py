#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import re


END_MARK = '</Event>'
END_MARK_LEN = len(END_MARK)

TIME_RE = re.compile('TimeCreated\s+SystemTime=\'([^\"]+)\'', re.MULTILINE)
LEVEL_RE = re.compile('<Level>(\d+)</Level>', re.MULTILINE)
SOURCE_RE = re.compile('Provider\s+Name=\'([^\']+)\'', re.MULTILINE)
MESSAGE_RE = re.compile('<Data>([\s\S]*?)</Data>', re.MULTILINE)
LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('output', nargs='?')
args = parser.parse_args()

buf = []

def flush():
    if len(buf) == 0:
        return

    data = ''.join(buf)
    buf.clear()

    try:
        result = [x.search(data).group(1) for x in (TIME_RE, LEVEL_RE, SOURCE_RE, MESSAGE_RE)]
        result[0] = result[0].replace('T', ' ')
        result[1] = LEVELS[int(result[1])]

        print('|'.join(result), file=output_file)
    except Exception as e:
        print(e, '\n', data.encode())

with open(args.input, 'r', encoding='utf-8') as input_file:
    with open(args.output or os.path.splitext(args.input)[0] + '_nlog.log', 'w', encoding='utf-8') as output_file:
        for line in input_file:
            while True:
                end = line.find(END_MARK)
                if end != -1:
                    buf.append(line[:end+END_MARK_LEN])
                    line = line[end+END_MARK_LEN:]
                    flush()
                else:
                    buf.append(line)
                    break

