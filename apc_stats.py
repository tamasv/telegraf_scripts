#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import os
from apcaccess import status as apc


def str_escape(string):
    ret = string.replace(" ", "\\ ")
    ret = ret.replace(",", "\\,")
    ret = '"{}"'.format(ret)
    return ret


ups = apc.parse(apc.get(), strip_units=True)
watts = float(os.getenv('WATTS', ups.get('NOMPOWER', 0.0))) * \
    0.01 * float(ups.get('LOADPCT', 0.0))
results = {
    'measurement': 'apcaccess_status',
    'fields': {
        'WATTS': watts,
        'STATUS': str_escape(ups.get('STATUS')),
        'LOADPCT': float(ups.get('LOADPCT', 0.0)),
        'BCHARGE': float(ups.get('BCHARGE', 0.0)),
        'TONBATT': float(ups.get('TONBATT', 0.0)),
        'TIMELEFT': float(ups.get('TIMELEFT', 0.0)),
        'NOMPOWER': float(ups.get('NOMPOWER', 0.0)),
        'CUMONBATT': float(ups.get('CUMONBATT', 0.0)),
        'BATTV': float(ups.get('BATTV', 0.0)),
        'OUTPUTV': float(ups.get('OUTPUTV', 0.0)),
        'ITEMP': float(ups.get('ITEMP', 0.0)),
    },
    'tags': {
        'serial': str_escape(ups.get('SERIALNO', None)),
        'ups_alias': str_escape(ups.get('UPSNAME', None)),
    }
}
print("{},{} {}".format(
    results['measurement'], ",".join(
        ["{}={}".format(k, v) for k, v in results['tags'].items() if v != '']),
    ",".join([
        "{}={}".format(k, v) for k, v in results['fields'].items() if v != ''
    ])))
