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

import json
import re
import subprocess

from collections import namedtuple

RAID_TYPES = {
    '13c1': '3WARE',
    'beef': 'LSI'
}


class RaidInterface(object):

    @staticmethod
    def factory():
        raidtype = RaidInterface.get_raid_vendor_id()
        if raidtype not in RAID_TYPES.keys():
            raise Exception("Unknown RAID type %s" % raidtype)

        if RAID_TYPES[raidtype] == '3WARE':
            return ThreeWareRaidInterface()
        elif RAID_TYPES[raidtype] == 'LSI':
            return LSIRaidInterface()

    @staticmethod
    def get_raid_vendor_id():
        """ This function uses lspci to determine the RAID device. This assumes
        that there is only one RAID card present for the time being.
        """
        cmd = "lspci -nn | grep RAID"
        output = subprocess.check_output(cmd, shell=True)
        matches = re.match('.*\[([A-Za-z0-9]{4}):[A-Za-z0-9]{4}\]', output)
        if not matches:
            raise Exception("Unable to find a RAID device")
        return matches.group(1)

    def _get_disk_hwinfo(self):
        cmd = "lshw -class disk -json 2> /dev/null"
        output = subprocess.check_output(cmd, shell=True)
        jsonout = "[%s]" % output
        data = json.loads(jsonout)
        return data

    def get_blockdev_wwn(self, blockdev):
        data = self._get_disk_hwinfo()
        businfo = None
        for di in data:
            if di['logicalname'] == blockdev:
                businfo = di['businfo']
                break

        if not businfo:
            raise Exception("Could not find businfo for %s" % blockdev)
        return self.get_drive_wwn_from_businfo(businfo)

    def get_drive_wwn_from_businfo(self, businfo):
        raise NotImplementedError()


class LSIRaidInterface(RaidInterface):
    pass


class ThreeWareRaidInterface(RaidInterface):

    #Unit UnitType Status %RCmpl %V/I/M VPort Stripe Size(GB)
    UnitInfo = namedtuple('UnitInfo', 'unit type status rcmpl vim vport stripe size')

    def _chassis_unit_from_businfo(self, businfo):
        match = re.match('scsi@(\d+):\d+\.(\d+)\.\d+', businfo)
        if not match:
            raise Exception("Unable to parse businfo")
        c = int(match.group(1))
        u = int(match.group(2))
        return c, u

    def get_drive_wwn_from_businfo(self, businfo):
        if not businfo:
            return None
        c, u = self._chassis_unit_from_businfo(businfo)
        cmd = "tw-cli /c%d/u%d show" % (c, u)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        entries = []
        for line in iter(proc.stdout.readline, ''):
            if re.match(r'^[\s\-]*$', line) or re.match(r'^Unit', line):
                continue
            else:
                entries.append(ThreeWareRaidInterface.UnitInfo(*re.split('\s+', line.strip())))

        if len(entries) == 0:
            raise Exception("Unable to get wwn for '%s'" % businfo)

        unit = entries[0]
        if unit.type != 'SINGLE':
            raise Exception("Cannot retrieve wwn for raided blockdevs")

        cmd = "tw-cli /c%s/%s show wwn" % (c, unit.vport)
        output = subprocess.check_output(cmd, shell=True)
        wwn = output.split('=')[1].strip()
        return wwn
