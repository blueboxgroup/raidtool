#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014, Blue Box Group, Inc.
# Copyright (c) 2014, Craig Tracey <craigtracey@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

import argparse
import sys

from raidtool.raid_interface import RaidInterface


def wwn(args):
    blockdev = args.blockdev
    raidint = RaidInterface.factory()
    try:
        wwn = raidint.get_blockdev_wwn(blockdev)
        if not blockdev:
            print >> sys.stderr, "Unable to find wwn for '%s'" % blockdev
            sys.exit(-1)
    except Exception as e:
        print >> sys.stderr, "Error: %s" % e
        sys.exit(-1)
    print wwn


def main():
    parser = argparse.ArgumentParser(description=
                                     'a tool for querying & manipulating raid devices')
    subparsers = parser.add_subparsers()

    parser_wwn = subparsers.add_parser('wwn')
    parser_wwn.add_argument('blockdev', type=str, help="blockdevice like '/dev/sdb'")
    parser_wwn.set_defaults(func=wwn)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
