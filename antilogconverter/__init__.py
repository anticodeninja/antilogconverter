#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright 2019 Artem Yamshanov, me [at] anticode.ninja

import argparse
import os
import re


def extract(re, string):
    match = re.search(string)
    return match.group(1).strip() if match else None


class BaseConverter:

    def __init__(self, source, target):
        self.buf = []
        self.source = source
        self.target = target

    def flush(self):
        data = ''.join(self.buf).strip()
        try:
            if len(data) > 0:
                print(self.convert(data), file=self.target)
        except Exception as e:
            print('Cannot convert log entry: ', e, '\n', data.encode(), '-' * 80)
        self.buf.clear()


class TextConverter(BaseConverter):

    def __init__(self, source, target, delimiter):
        super().__init__(source, target)
        self.delimiter = delimiter

    def handle(self):
        for line in self.source:
            if self.delimiter in line:
                self.flush()
            self.buf.append(line)
        self.flush()


class XmlConverter(BaseConverter):

    def __init__(self, source, target, end_mark):
        super().__init__(source, target)
        self.end_mark = end_mark
        self.end_mark_len = len(end_mark)


    def handle(self):
        for line in self.source:
            while True:
                end = line.find(self.end_mark)
                if end != -1:
                    self.buf.append(line[:end+self.end_mark_len])
                    line = line[end+self.end_mark_len:]
                    self.flush()
                else:
                    self.buf.append(line)
                    break


class PlainConverter(TextConverter):

    TIME_RE = re.compile('Time:\s*([^\n]+)\s*', re.MULTILINE)
    LEVEL_RE = re.compile('Type:\s*([^\n]+)\s*', re.MULTILINE)
    SOURCE_RE = re.compile('Source:\s*([^\n]+)\s*', re.MULTILINE)
    COMMENT_RE = re.compile('Comment:\s*([\S\s]+)\s*', re.MULTILINE)
    TIME_REORDER_RE = re.compile('(\d+)\.(\d+)\.(\d+)\s+(\d+:\d+:\d+\.\d+)')

    def __init__(self, source, target):
        super().__init__(source, target, '-' * 40)

    def convert(self, data):
        result = [extract(x, data) for x in (self.TIME_RE, self.LEVEL_RE, self.SOURCE_RE, self.COMMENT_RE)]

        result[0] = '{2}-{1}-{0} {3}'.format(*self.TIME_REORDER_RE.match(result[0]).groups())
        if result[1] is None:
            result[1] = 'INFO'
        else:
            result[1] = result[1].upper()
            if result[1] == 'INFORMATION':
                result[1] = 'INFO'
        if result[2] is None:
            result[2] = 'UNKNOWN'

        return '|'.join(result)


class WindowsConverter(XmlConverter):

    TIME_RE = re.compile('TimeCreated\s+SystemTime=\'([^\"]+?)\'', re.MULTILINE)
    LEVEL_RE = re.compile('<Level>(\d+)</Level>', re.MULTILINE)
    SOURCE_RE = re.compile('Provider\s+Name=\'([^\']+?)\'', re.MULTILINE)
    MESSAGE_RE = re.compile('<Data>([\s\S]*?)</Data>', re.MULTILINE)
    LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

    def __init__(self, source, target):
        super().__init__(source, target, '</Event>')

    def convert(self, data):
        result = [extract(x, data) for x in (self.TIME_RE, self.LEVEL_RE, self.SOURCE_RE, self.MESSAGE_RE)]

        result[0] = result[0].replace('T', ' ')
        result[1] = self.LEVELS[int(result[1])]

        return '|'.join(result)


class WcfConverter(XmlConverter):

    TIME_RE = re.compile('TimeCreated\s+SystemTime=\"([^\"]+?)\"', re.MULTILINE)
    LEVEL_RE = re.compile('SubType\s+Name=\"([^\"]+?)\"', re.MULTILINE)
    SOURCE_RE = re.compile('Source\s+Name=\"([^\"]+?)\"', re.MULTILINE)
    DESCRIPTION_RE = re.compile('<Description>([\s\S]*?)<\/Description>', re.MULTILINE)
    MESSAGE_RE = re.compile('<Message>([\s\S]*?)<\/Message>', re.MULTILINE)
    EXCEPTION_RE = re.compile('<ExceptionString>([\s\S]*?)<\/ExceptionString>', re.MULTILINE)
    STACK_RE = re.compile('<StackTrace>([\s\S]*?)<\/StackTrace>', re.MULTILINE)

    def __init__(self, source, target):
        super().__init__(source, target, '</E2ETraceEvent>')

    def convert(self, data):
        result = [extract(x, data) for x in (self.TIME_RE, self.LEVEL_RE, self.SOURCE_RE, self.MESSAGE_RE)]

        result[0] = result[0].replace('T', ' ')
        result[1] = result[1].upper()
        result[3] = result[3] or '*** NO MESSAGE ***'
        for optional in [self.DESCRIPTION_RE, self.EXCEPTION_RE, self.STACK_RE]:
            match = extract(optional, data)
            if match:
                result[3] += '\n' + match

        return '|'.join(result)


CONVERTERS = [
    { 'id': 'wcf',  'converter': WcfConverter, 'magic': '<E2ETraceEvent' },
    { 'id': 'windows', 'converter': WindowsConverter, 'magic': '<Events><Event' },
    { 'id': 'plain', 'converter': PlainConverter, 'magic': '-' * 40 },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output', nargs='?')
    parser.add_argument('-f', '--format', action='store', choices = (x['id'] for x in CONVERTERS))
    args = parser.parse_args()

    source = open(args.input, 'r', encoding='utf-8')
    target = open(args.output or os.path.splitext(args.input)[0] + '_nlog.log', 'w', encoding='utf-8')

    if args.format != None:
        converter_info = next(x for x in CONVERTERS if x['id'] == args.format)
    else:
        header = ''.join(source.readline() for x in range(5))
        for info in CONVERTERS:
            if info['magic'] in header:
                converter_info = info
                break
        else:
            raise Exception('Could not determine source format, try to specify it explicitly')
        source.seek(0)

    print(converter_info['id'], 'log converter is used')
    converter = converter_info['converter'](source, target)
    converter.handle()
