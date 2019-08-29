#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import re


END_MARK = '</E2ETraceEvent>'
END_MARK_LEN = len(END_MARK)

TIME_RE = re.compile('TimeCreated\s+SystemTime=\"([^\"]+)\"', re.MULTILINE)
LEVEL_RE = re.compile('SubType\s+Name=\"([^\"]+)\"', re.MULTILINE)
SOURCE_RE = re.compile('Source\s+Name=\"([^\"]+)\"', re.MULTILINE)
DESCRIPTION_RE = re.compile('<Description>([\s\S]*?)<\/Description>', re.MULTILINE)
MESSAGE_RE = re.compile('<Message>([\s\S]*?)<\/Message>', re.MULTILINE)
EXCEPTION_RE = re.compile('<ExceptionString>([\s\S]*?)<\/ExceptionString>', re.MULTILINE)
STACK_RE = re.compile('<StackTrace>([\s\S]*?)<\/StackTrace>', re.MULTILINE)


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
        result[1] = result[1].upper()

        for optional in [DESCRIPTION_RE, EXCEPTION_RE, STACK_RE]:
            match = optional.search(data)
            if match:
                result[-1] += '\n' + match.group(1)

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

