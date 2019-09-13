#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# TODO:
# - fetch capsman related stuff
# - Fetch ipnei
# - Fetch env values
#
#
import argparse
from easysnmp import Session


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
            'description':
            str_escape(sess.get('sysDescr.0').value),
            'name':
            str_escape(sess.get('sysName.0').value),
            'objectid':
            str_escape(sess.get('sysObjectID.0').value),
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


def get_interfaces(sess):
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
    ifinoctets = {v.oid_index: v for v in sess.walk('IF-MIB::ifInOctets')}
    ifinucastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifInUcastPkts')
    }
    ifinnucastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifInNUcastPkts')
    }
    ifindiscards = {v.oid_index: v for v in sess.walk('IF-MIB::ifInDiscards')}
    ifinerrors = {v.oid_index: v for v in sess.walk('IF-MIB::ifInErrors')}
    ifinunknownprotos = {
        v.oid_index: v
        for v in sess.walk('ifInUnknownProtos')
    }
    ifoutoctets = {v.oid_index: v for v in sess.walk('IF-MIB::ifOutOctets')}
    ifoutucastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifOutUcastPkts')
    }
    ifoutnucastpkts = {
        v.oid_index: v
        for v in sess.walk('IF-MIB::ifOutNUcastPkts')
    }
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
            },
            'fields': {
                'adminstatus': ifadminstatus[ifindex].value,
                'operstatus': ifoperstatus[ifindex].value,
                'bytes_in': ifinoctets[ifindex].value,
                'ucast_pkts_in': ifinucastpkts[ifindex].value,
                'nonucast_pkts_in': ifinnucastpkts[ifindex].value,
                'discards_in': ifindiscards[ifindex].value,
                'errors_in': ifinerrors[ifindex].value,
                'unknown_protos_in': ifinunknownprotos[ifindex].value,
                'bytes_out': ifoutoctets[ifindex].value,
                'ucast_pkts_out': ifoutucastpkts[ifindex].value,
                'nonucast_pkts_out': ifoutnucastpkts[ifindex].value,
                'discards_out': ifoutdiscards[ifindex].value,
                'errors_out': ifouterrors[ifindex].value,
            }
        }
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


def get_wireless(sess):
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
        ssid_ret.append(ret)
    return (clients_ret, ssid_ret)


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
                        choices=[1, 2],
                        required=True)
    parser.add_argument("-c",
                        "--community",
                        type=str,
                        help="Community string",
                        required=True)
    args = parser.parse_args()
    snmp_sess = Session(hostname=args.ip,
                        community=args.community,
                        version=args.version,
                        use_sprint_value=False)
    stats = {}
    stats['basic'] = [get_basic_info(snmp_sess)]
    stats['interfaces'] = get_interfaces(snmp_sess)
    stats['wireless_clients'], stats['wireless_basic'] = get_wireless(
        snmp_sess)
    print_influx_lines(stats)


if __name__ == "__main__":
    main()
