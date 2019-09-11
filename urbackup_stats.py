#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urbackup_api
import sys
from datetime import datetime


def str_escape(string):
    ret = string.replace(" ", "\\ ")
    ret = ret.replace(",", "\\,")
    ret = '"{}"'.format(ret)
    return ret


def main():
    """
    ./urbackup_stats.py http://127.0.0.1/x myuser mypwd
    """
    urbackup_server_address = sys.argv[1]
    if len(sys.argv) > 2:
        urbackup_server_user = sys.argv[2]
    else:
        urbackup_server_user = None
    if len(sys.argv) > 3:
        urbackup_server_pw = sys.argv[3]
    else:
        urbackup_server_pw = None

    server = urbackup_api.urbackup_server(urbackup_server_address,
                                          urbackup_server_user,
                                          urbackup_server_pw)
    clients = server.get_status()
    for client in clients:
        last_backup_file = client['lastbackup']
        last_backup_image = client['lastbackup_image']
        status = client['status']
        client['os_version_string'] = str_escape(client['os_version_string'])
        client['name'] = str_escape(client['name'])
        client['os_simple'] = str_escape(client['os_simple'])
        client['client_version_string'] = str_escape(
            client['client_version_string'])
        if client['ip'] == "-":
            client['ip'] = None
        client.pop('lastbackup')
        client.pop('lastbackup_image')
        client.pop('processes')
        client.pop('status')
        now = datetime.now()
        lastbackup_elapsed = (
            now - datetime.fromtimestamp(last_backup_file)).total_seconds()
        lastbackup_image_elapsed = (
            now - datetime.fromtimestamp(last_backup_image)).total_seconds()
        print(
            "urbackup,{} "
            "lastbackup={},lastbackup_image={},status={},"
            "lastbackup_elapsed={},lastbackup_image_elapsed={}"
            .format(
                ",".join([
                    "{}={}".format(k, v) for k, v in client.items() if v != ''
                ]), last_backup_file, last_backup_image, status,
                lastbackup_elapsed, lastbackup_image_elapsed))


if __name__ == "__main__":
    main()
