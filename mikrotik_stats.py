#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# TODO:
# - Fetch ipnei
#
#
import argparse
from easysnmp import Session
uplinks = []


def is_uplink(descr):
    global uplinks
    if uplinks is not None and descr in uplinks:
        return True
    return False


def parse_int(string):
    try:
        ret = int(string)
    except ValueError:
        ret = -1
    return ret


def str_escape(string):
    if string is None:
        return None
    if " " in string or "," in string or "=" in string:
        ret = string.replace(" ", "\\ ")
        ret = ret.replace(",", "\\,")
        ret = ret.replace("=", "\\=")
        ret = '{}'.format(ret)
    else:
        ret = string
    return ret


def get_basic_info(sess):
    ret = {
        'tags': {
            'model':
            str_escape(sess.get('sysDescr.0').value),
            'hostname':
            str_escape(sess.get('sysName.0').value),
            'location':
            str_escape(sess.get('sysLocation.0').value),
            'contact':
            str_escape(sess.get('sysContact.0').value),
            'serial':
            str_escape(sess.get('MIKROTIK-MIB::mtxrSerialNumber.0').value),
        },
        'fields': {
            'firmware_version':
            "\"{}\"".format(
                str_escape(
                    sess.get('MIKROTIK-MIB::mtxrFirmwareVersion.0').value)),
            'version':
            "\"{}\"".format(
                str_escape(sess.get('MIKROTIK-MIB::mtxrLicVersion.0').value)),
            'dhcp_leases':
            sess.get('MIKROTIK-MIB::mtxrDHCPLeaseCount.0').value,
            'sysUpTime':
            sess.get('sysUpTime.0').value,
        }
    }
    return ret


def get_interfaces(sess, basic_tags):
    interfaces = []
    ifindexes = sess.walk('IF-MIB::ifIndex')
    iftypes = {v.oid_index: v for v in sess.walk('IF-MIB::ifType')}
    ifdescr = {v.oid_index: v for v in sess.walk('IF-MIB::ifDescr')}
    ifmtu = {v.oid_index: v for v in sess.walk('IF-MIB::ifMtu')}
    ifspeeds = {v.oid_index: v for v in sess.walk('IF-MIB::ifSpeed')}
    ifadminstatus = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifAdminStatus')
    }
    ifoperstatus = {v.oid_index: v for v in sess.walk('IF-MIB::ifOperStatus')}
    ifinoctets = {v.oid_index: v for v in sess.walk('IF-MIB::ifHCInOctets')}
    ifinucastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifHCInUcastPkts')
    }
    ifinmcastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifHCInMulticastPkts')
    }
    ifinbcastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifHCInBroadcastPkts')
    }
    ifoutoctets = {v.oid_index: v for v in sess.walk('IF-MIB::ifHCOutOctets')}
    ifoutucastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifHCOutUcastPkts')
    }
    ifoutmcastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifHCOutMulticastPkts')
    }
    ifoutbcastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifHCOutBroadcastPkts')
    }

    ifindiscards = {v.oid_index: v for v in sess.walk('IF-MIB::ifInDiscards')}
    ifinerrors = {v.oid_index: v for v in sess.walk('IF-MIB::ifInErrors')}
    ifoutdiscards = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifOutDiscards')
    }
    ifouterrors = {v.oid_index: v for v in sess.walk('IF-MIB::ifOutErrors')}
    for ifindex_row in ifindexes:
        ifindex = ifindex_row.value
        iface = {
            'tags': {
                'ifindex': int(ifindex),
                'description': str_escape(ifdescr[ifindex].value),
                'interface_type': int(iftypes[ifindex].value),
                'speed': int(ifspeeds[ifindex].value),
                'mtu': int(ifmtu[ifindex].value),
                'uplink': is_uplink(ifdescr[ifindex].value)
            },
            'fields': {
                'adminstatus': ifadminstatus[ifindex].value,
                'operstatus': ifoperstatus[ifindex].value,
                'bytes_in': ifinoctets[ifindex].value,
                'ucast_pkts_in': ifinucastpkts[ifindex].value,
                'multicast_pkts_in': ifinmcastpkts[ifindex].value,
                'broadcast_pkts_in': ifinbcastpkts[ifindex].value,
                'bytes_out': ifoutoctets[ifindex].value,
                'ucast_pkts_out': ifoutucastpkts[ifindex].value,
                'multicastcast_pkts_out': ifoutmcastpkts[ifindex].value,
                'broadcast_pkts_out': ifoutbcastpkts[ifindex].value,
                'discards_in': ifindiscards[ifindex].value,
                'errors_in': ifinerrors[ifindex].value,
                'discards_out': ifoutdiscards[ifindex].value,
                'errors_out': ifouterrors[ifindex].value,
            }
        }
        iface['tags'].update(basic_tags)
        interfaces.append(iface)
    return interfaces


def _convert_octetstr_to_mac(mac):
    return ":".join(format(ord(x), '02X') for x in mac)


def _convert_oid_index_to_mac_ssid(oid_index):
    mac = oid_index.split(".")[:-1]
    ssid_index = int(oid_index.split(".")[-1])
    mac = ":".join(format(int(x), '02X') for x in mac)
    return (mac, ssid_index)


def _convert_oid_index_to_mac(oid_index):
    mac, _ = _convert_oid_index_to_mac_ssid(oid_index)
    return mac


def _convert_oid_index_to_ssid(oid_index):
    _, ssid = _convert_oid_index_to_mac_ssid(oid_index)
    return ssid


def get_wireless(sess, basic_tags):
    clients = sess.walk('MIKROTIK-MIB::mtxrWlCMRtabAddr')
    dhcpclients = {
        _convert_octetstr_to_mac(x.value):
        ".".join(x.oid_index.split(".")[1:])
        for x in sess.walk('IP-MIB::ipNetToMediaPhysAddress')
    }
    uptimes = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabUptime')
    }
    ssids = {
        _convert_oid_index_to_ssid(x.oid_index): x.value
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabSsid')
    }
    txstr = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabTxStrength')
    }
    rxstr = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabRxStrength')
    }
    txbytes = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabTxBytes')
    }
    rxbytes = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabRxBytes')
    }
    txpackets = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabTxPackets')
    }
    rxpackets = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabRxPackets')
    }
    txrate = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabTxRate')
    }
    rxrate = {
        x.oid_index: int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRtabRxRate')
    }
    regclients = {
        int(x.oid_index): int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMRegClientCount')
    }
    authclients = {
        int(x.oid_index): int(x.value)
        for x in sess.walk('MIKROTIK-MIB::mtxrWlCMAuthClientCount')
    }
    clients_ret = []
    ssid_ret = []
    for client_row in clients:
        clientindex = client_row.oid_index
        mac = _convert_octetstr_to_mac(client_row.value)
        ret = {
            'tags': {
                'macaddress': mac,
                'address': dhcpclients.get(mac, None),
                'ssid_id': _convert_oid_index_to_ssid(clientindex),
                'ssid': ssids[_convert_oid_index_to_ssid(clientindex)],
            },
            'fields': {
                'txstrength': txstr[clientindex],
                'rxstrength': rxstr[clientindex],
                'uptime': uptimes[clientindex],
                'txbytes': txbytes[clientindex],
                'rxbytes': rxbytes[clientindex],
                'txpackets': txpackets[clientindex],
                'rxpackets': rxpackets[clientindex],
                'txrate': txrate[clientindex],
                'rxrate': rxrate[clientindex],
            }
        }
        ret['tags'].update(basic_tags)
        clients_ret.append(ret)
    for ssid_id, ssid_name in ssids.items():
        ret = {
            'tags': {
                'ssid': ssid_name,
                'ssid_id': ssid_id,
            },
            'fields': {
                'regclientcount': regclients.get(ssid_id, 0),
                'authclientcount': authclients.get(ssid_id, 0),
            }
        }
        ret['tags'].update(basic_tags)
        ssid_ret.append(ret)
    return (clients_ret, ssid_ret)


def get_env(sess, basic_tags):
    env = []
    cputemps = {
        int(x.oid_index): float(x.value)
        for x in sess.walk("MIKROTIK-MIB::mtxrHlCpuTemperature")
    }
    for cpu_id, cputemp in cputemps.items():
        ret = {
            'tags': {
                'cpu_id': cpu_id,
            },
            'fields': {
                'temperature': float(cputemp) / 10,
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    boardtemps = {
        int(x.oid_index): float(x.value)
        for x in sess.walk("MIKROTIK-MIB::mtxrHlBoardTemperature")
    }
    for board_id, boardtemp in boardtemps.items():
        ret = {
            'tags': {
                'board_sensor_id': board_id,
            },
            'fields': {
                'temperature': float(boardtemp) / 10,
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    temp_sensors = {
        int(x.oid_index): float(x.value)
        for x in sess.walk("MIKROTIK-MIB::mtxrHlTemperature")
    }
    for sensor_id, temp_sensor in temp_sensors.items():
        ret = {
            'tags': {
                'sensor_id': sensor_id,
            },
            'fields': {
                'temperature': float(temp_sensor) / 10,
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    voltage_sensors = {
        int(x.oid_index): float(x.value)
        for x in sess.walk("MIKROTIK-MIB::mtxrHlVoltage")
    }
    for sensor_id, voltage_sensor in voltage_sensors.items():
        ret = {
            'tags': {
                'sensor_id': sensor_id,
            },
            'fields': {
                'voltage': float(voltage_sensor) / 10,
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    fan_sensors = {
        int(x.oid_index): x.value
        for x in sess.walk("MIKROTIK-MIB::mtxrHlActiveFan")
    }
    for sensor_id, fan_sensor in fan_sensors.items():
        ret = {
            'tags': {
                'sensor_id': sensor_id,
            },
            'fields': {
                'value': parse_int(fan_sensor),
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    cpu_freqs = {
        int(x.oid_index): x.value
        for x in sess.walk("MIKROTIK-MIB::mtxrHlProcessorFrequency")
    }
    for cpu_id, cpu_freq in cpu_freqs.items():
        ret = {
            'tags': {
                'cpu': cpu_id,
            },
            'fields': {
                'freq': cpu_freq,
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    cpu_utils = {
        int(x.oid_index): float(x.value)
        for x in sess.walk(".1.3.6.1.2.1.25.3.3.1.2")
    }
    for cpu_id, cpu_util in cpu_utils.items():
        ret = {
            'tags': {
                'cpu': cpu_id,
            },
            'fields': {
                'util': cpu_util,
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    mem_types = {
        int(x.oid_index): str(x.value)
        for x in sess.walk("HOST-RESOURCES-MIB::hrStorageType")
    }
    mem_names = {
        int(x.oid_index): str(x.value)
        for x in sess.walk("HOST-RESOURCES-MIB::hrStorageDescr")
    }
    mem_units = {
        int(x.oid_index): int(x.value)
        for x in sess.walk("HOST-RESOURCES-MIB::hrStorageAllocationUnits")
    }
    mem_size = {
        int(x.oid_index): int(x.value)
        for x in sess.walk("HOST-RESOURCES-MIB::hrStorageSize")
    }
    mem_used = {
        int(x.oid_index): int(x.value)
        for x in sess.walk("HOST-RESOURCES-MIB::hrStorageUsed")
    }
    mem_alloc_failures = {
        int(x.oid_index): float(x.value)
        for x in sess.walk("HOST-RESOURCES-MIB::hrStorageAllocationFailures")
    }
    for mem_id, mem_name in mem_names.items():
        ret = {
            'tags': {
                'memory_id': mem_id,
                'memory_name': str_escape(mem_names[mem_id]),
                'memory_units': mem_units[mem_id],
                'memory_type': str_escape(mem_types[mem_id])
            },
            'fields': {
                'size':
                mem_size[mem_id] * mem_units[mem_id],
                'used':
                mem_used[mem_id] * mem_units[mem_id],
                'used_percent':
                float(mem_used[mem_id] * mem_units[mem_id]) /
                float(mem_size[mem_id] * mem_units[mem_id]),
                'allocation_failures':
                mem_alloc_failures[mem_id]
            }
        }
        ret['tags'].update(basic_tags)
        env.append(ret)
    return env


def print_influx_lines(stats):
    for measurement, stat_a in stats.items():
        measurement = "mikrotik_{}".format(measurement)
        for stat in stat_a:
            print("{},{} {}".format(
                measurement, ",".join([
                    "{}={}".format(k, v) for k, v in stat['tags'].items()
                    if v != ''
                ]), ",".join([
                    "{}={}".format(k, v) for k, v in stat['fields'].items()
                    if v != ''
                ])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip",
                        help="IP address of the network device",
                        type=str)
    parser.add_argument("-v",
                        "--version",
                        type=int,
                        help="SNMP protocol version",
                        choices=[2, 3],
                        required=True)
    parser.add_argument("-c", "--community", type=str, help="Community string")
    parser.add_argument("-s",
                        "--security",
                        type=str,
                        help="Security v3",
                        choices=[
                            'no_auth_or_privacy', 'auth_without_privacy',
                            'auth_with_privacy'
                        ])
    parser.add_argument("-u", "--username", type=str, help="Username v3")
    parser.add_argument("-pp",
                        "--privacy_password",
                        type=str,
                        help="Privacy password v3")
    parser.add_argument("-ap",
                        "--auth_password",
                        type=str,
                        help="Auth password v3")
    parser.add_argument("-aproto",
                        "--auth_protocol",
                        type=str,
                        help="Auth password v3",
                        choices=['DM5', 'SHA'])
    parser.add_argument("-pproto",
                        "--privacy_protocol",
                        type=str,
                        help="Auth password v3",
                        choices=['DES', 'AES'])
    parser.add_argument("-uplink",
                        "--uplink_port",
                        type=str,
                        help="Tag the matching port with uplink tag",
                        nargs="+")
    args = parser.parse_args()
    global uplinks
    uplinks = args.uplink_port
    if args.version == 2:
        snmp_sess = Session(hostname=args.ip,
                            community=args.community,
                            version=args.version,
                            use_sprint_value=False)
    else:
        snmp_sess = Session(hostname=args.ip,
                            version=args.version,
                            auth_protocol=args.auth_protocol,
                            auth_password=args.auth_password,
                            security_username=args.username,
                            privacy_protocol=args.privacy_protocol,
                            privacy_password=args.privacy_password,
                            security_level=args.security,
                            use_sprint_value=False)
    stats = {}
    stats['basic'] = [get_basic_info(snmp_sess)]
    stats['interfaces'] = get_interfaces(snmp_sess, stats['basic'][0]['tags'])
    stats['wireless_clients'], stats['wireless_basic'] = get_wireless(
        snmp_sess, stats['basic'][0]['tags'])
    stats['env'] = get_env(snmp_sess, stats['basic'][0]['tags'])
    print_influx_lines(stats)


if __name__ == "__main__":
    main()
