#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import requests
import urllib3
from os import listdir
from os.path import isfile, join
import re
import datetime

urllib3.disable_warnings()

SECONDS_PER_BLOCK = (24 * 3600) / 4608
HARVESTER_REGEX = re.compile(
    r"^([\d\-T\:\.]*)\s+harvester\s+chia.harvester.harvester:\s+"
    r"INFO\s+([\d]*) plots were eligible for farming ([a-z\d]*)"
    r".*Found ([\d]*) proofs.\s+Time: ([\d\.]*)\s+s.\s+Total\s+"
    r"([\d]*)\s+plots\s*$")
HARVESTER_LAST_TS_FILENAME = 'telegraf_harvester_last.ts'


def str_escape(string):
    if string is None:
        return '""'
    if string == "null":
        return '""'
    ret = string.replace(" ", "\\ ")
    ret = ret.replace(",", "\\,")
    #    ret = ret.replace(".", "\\.")
    ret = '"{}"'.format(ret)
    return ret


def float_convert(f):
    if f == "null" or f is None:
        return 0.0
    return float(f)


class LogLine():
    def __init__(self, match):
        self.ts = datetime.datetime.fromisoformat(match[1])
        self.eligible_plots = int(match[2])
        self.challange = str(match[3])
        self.proofs = int(match[4])
        self.time_spent = float(match[5])
        self.total_plots = int(match[6])


class HarvesterLogs():
    def __init__(self, harvester_logs, last_ts, logsdir):
        self.harvester_logs = harvester_logs
        self.last_ts = last_ts
        self.loglines = []
        self.logsdir = logsdir
        self._process_logs()

    def _process_logs(self):
        for harvester_log in self.harvester_logs:
            with open(harvester_log) as f:
                lines = f.read()
                for line in lines.split("\n"):
                    match = re.match(HARVESTER_REGEX, line)
                    if match:
                        lline = LogLine(match)
                        if lline.ts > self.last_ts and (
                                lline.eligible_plots > 0 or lline.proofs > 0):
                            self.loglines.append(lline)
        # place ts
        sorted(self.loglines, key=lambda x: x.ts, reverse=1)
        if len(self.loglines) > 0:
            with open(join(self.logsdir, HARVESTER_LAST_TS_FILENAME),
                      'w+') as f:
                f.write(self.loglines[-1].ts.isoformat())


class Endpoint():
    def __init__(self, chiacert, chiakey, walletcert, walletkey, address,
                 logsdir):
        self.chiakey = chiakey
        self.chiacert = chiacert
        self.walletkey = walletkey
        self.walletcert = walletcert
        self.address = address
        self.logsdir = logsdir
        self.last_ts = self._get_last_ts()

    def _get_last_ts(self):
        if isfile(join(self.logsdir, HARVESTER_LAST_TS_FILENAME)):
            with open(join(self.logsdir, HARVESTER_LAST_TS_FILENAME),
                      'r') as f:
                try:
                    return datetime.datetime.fromisoformat(f.read())
                except Exception:
                    return datetime.datetime.min
        else:
            return datetime.datetime.min

    def get_data(self, endpoint, port, data="{}", cert_type=None):
        url = f"https://{self.address}:{port}/{endpoint}"
        if cert_type is None:
            r = requests.post(url,
                              cert=(self.chiacert, self.chiakey),
                              data=data,
                              verify=False)
        elif cert_type == "wallet":
            r = requests.post(url,
                              cert=(self.walletcert, self.walletkey),
                              data=data,
                              verify=False)
        return r.json()

    def get_harvester_logfiles(self):
        harvester_logs = [
            join(self.logsdir, f) for f in listdir(self.logsdir)
            if isfile(join(self.logsdir, f))
        ]
        harvester_logs = filter(lambda x: 'harvester.log' in x, harvester_logs)
        return harvester_logs


def plots(e, extra_tags):
    plot_tags_escape = [
        'plot-seed', 'plot_public_key', 'pool_public_key',
        'pool_contract_puzzle_hash'
    ]
    plot_tags = ['size']
    plot_values = ['file_size', 'time_modified']
    plot_values_escape = ['filename']
    unique_plot_size = 0.0
    unique_plot_count = 0
    plots = e.get_data('get_plots', 8560)
    for plot in plots['plots']:
        tags = ",".join(
            [f"{k}={v}" for k, v in plot.items() if k in plot_tags])
        tags += ","
        tags += ",".join([
            f"{k}={str_escape(v)}" for k, v in plot.items()
            if k in plot_tags_escape
        ])
        if len(extra_tags) > 0:
            tags += ","
            tags += ",".join([f"{k}={v}" for k, v in extra_tags.items()])
        values = ",".join(
            [f"{k}={v}" for k, v in plot.items() if k in plot_values])
        values += ","
        values += ",".join([
            f"{k}={str_escape(v)}" for k, v in plot.items()
            if k in plot_values_escape
        ])
        print("chia_plots,{} {}".format(tags, values))
        unique_plot_size += plot['file_size']
        unique_plot_count += 1
    tags = ",".join([f"{k}={v}" for k, v in extra_tags.items()])
    values = (f"unique_plot_count={float(unique_plot_count)},"
              f"unique_plot_size={float(unique_plot_size)}")
    print("chia_plots_summary,{} {}".format(tags, values))
    return plots


def network_info(e):
    info = e.get_data('get_network_info', 8555)
    return info['network_name'], info['network_prefix']


def wallet_balance(e, extra_tags):
    balance = e.get_data('get_wallet_balance',
                         9256,
                         data='{"wallet_id": 1}',
                         cert_type="wallet")['wallet_balance']
    balance_tags = ['wallet_id']
    balance_values = [
        'confirmed_wallet_balance', 'max_send_amount', 'pending_change',
        'spendable_balance', 'unconfirmed_wallet_balance'
    ]
    tags = ",".join(
        [f"{k}={v}" for k, v in balance.items() if k in balance_tags])
    if len(extra_tags) > 0:
        tags += ","
        tags += ",".join([f"{k}={v}" for k, v in extra_tags.items()])
    values = ",".join(
        [f"{k}={float(v)}" for k, v in balance.items() if k in balance_values])
    print("chia_wallet,{} {}".format(tags, values))


def estimated_time(e, plots, space, extra_tags):
    tags = ""
    total_plot_size = sum([x['file_size'] for x in plots['plots']])
    info = e.get_data('get_blockchain_state', 8555)['blockchain_state']
    if info['peak']['height'] < 600:
        avg_block_time = SECONDS_PER_BLOCK
    header_hash = info['peak']['prev_hash']
    curr = None
    past_curr = None
    while curr is None or curr['timestamp'] is None:
        curr = e.get_data('get_block_record',
                          8555,
                          data='{"header_hash": "' + header_hash +
                          '"}')['block_record']
        header_hash = curr['prev_hash']
    past_curr = e.get_data('get_block_record_by_height',
                           8555,
                           data='{"height": ' +
                           str(int(curr['height']) - 500) +
                           '}')['block_record']
    while past_curr is None or past_curr['timestamp'] is None:
        past_curr = e.get_data('get_block_record_by_height',
                               8555,
                               data='{"height": ' +
                               str(int(past_curr['height']) - 500) +
                               '}')['block_record']
    if curr['timestamp'] is not None and not (past_curr['timestamp'] is None):
        avg_block_time = (curr['timestamp'] - past_curr['timestamp']) / (
            curr['height'] - past_curr['height'])
    else:
        avg_block_time = SECONDS_PER_BLOCK
    if space is not None and plots is not None:
        proportion = total_plot_size / space if space else -1
        minutes = ((avg_block_time / 60) / proportion) if proportion else -1
    if len(extra_tags) > 0:
        tags += ",".join([f"{k}={v}" for k, v in extra_tags.items()])
    print("chia_win,{} time_to_win={}".format(tags, minutes))


def blockchain_state(e, extra_tags):
    info = e.get_data('get_blockchain_state', 8555)['blockchain_state']
    info_values = ['height', 'required_iters', 'signage_point_index', 'weight']
    values = ",".join([
        f"{k}={float(v)}" for k, v in info['peak'].items() if k in info_values
    ])
    values += f",fees={float_convert(info['peak']['fees'])}"
    values += f",difficulty={info['difficulty']}"
    values += f",mempool_size={info['mempool_size']}"
    values += f",space={float(info['space'])}"
    values += f",synced={info['sync']['synced']}"
    values += f",sync_mode={info['sync']['synced']}"
    values += f",sync_tip_height={float(info['sync']['sync_tip_height'])}"
    values += (f",sync_progress_height="
               f"{float(info['sync']['sync_progress_height'])}")
    tags = "example=tag"
    print("chia_blockstate,{} {}".format(tags, values))
    return info['space'], info['difficulty']


def logs(e, extra_tags):
    harvester_values = [
        'eligible_plots', 'time_spent', 'proofs', 'total_plots'
    ]
    harvester_logs = e.get_harvester_logfiles()
    logs = HarvesterLogs(harvester_logs, e.last_ts, e.logsdir)
    for log in logs.loglines:
        tags = ""
        if len(extra_tags) > 0:
            tags = ",".join([f"{k}={v}" for k, v in extra_tags.items()])
        values = ",".join([
            f"{k}={v}" for k, v in log.__dict__.items()
            if k in harvester_values
        ])
        print("chia_harvester,{} {} {:.0f}".format(
            tags, values,
            datetime.datetime.timestamp(log.ts) * 10**9))


def main():
    parser = argparse.ArgumentParser(
        description="Chia stats to influx expoter")
    parser.add_argument('--cert', help="Chia cert")
    parser.add_argument('--key', help="Chia key")
    parser.add_argument('--walletcert', help="Chia wallet cert")
    parser.add_argument('--walletkey', help="Chia wallet key")
    parser.add_argument('--logsdir', help="Chia log dir for harvester logs")
    parser.add_argument('address', help="Ip address of the rest api")
    args = parser.parse_args()
    e = Endpoint(chiacert=args.cert,
                 chiakey=args.key,
                 walletcert=args.walletcert,
                 walletkey=args.walletkey,
                 address=args.address,
                 logsdir=args.logsdir)
    tags = {}
    network_name, network_prefix = network_info(e)
    tags['network_name'] = network_name
    tags['network_prefix'] = network_prefix
    space, difficulty = blockchain_state(e, tags)
    # tags['network_space'] = space
    # tags['network_difficulty'] = difficulty
    plot = plots(e, tags)
    wallet_balance(e, tags)
    estimated_time(e, plot, space, tags)
    logs(e, tags)


if __name__ == "__main__":
    main()
