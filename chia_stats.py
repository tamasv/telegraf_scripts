#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import requests
import urllib3

urllib3.disable_warnings()

SECONDS_PER_BLOCK = (24 * 3600) / 4608


def str_escape(string):
    if string is None:
        return ""
    ret = string.replace(" ", "\\ ")
    ret = ret.replace(",", "\\,")
    #    ret = ret.replace(".", "\\.")
    ret = '"{}"'.format(ret)
    return ret


def float_convert(f):
    if f == "null" or f is None:
        return 0.0
    return float(f)


class Endpoint():
    def __init__(self, chiacert, chiakey, walletcert, walletkey, address):
        self.chiakey = chiakey
        self.chiacert = chiacert
        self.walletkey = walletkey
        self.walletcert = walletcert
        self.address = address

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


def plots(e, extra_tags):
    plot_tags_escape = ['plot-seed', 'plot_public_key', 'pool_public_key']
    plot_tags = ['size']
    plot_values = ['file_size', 'time_modified']
    plot_values_escape = ['filename']
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
    tags = "example=tag"
    print("chia_blockstate,{} {}".format(tags, values))
    return info['space'], info['difficulty']


def main():
    parser = argparse.ArgumentParser(
        description="Chia stats to influx expoter")
    parser.add_argument('--cert', help="Chia cert")
    parser.add_argument('--key', help="Chia key")
    parser.add_argument('--walletcert', help="Chia wallet cert")
    parser.add_argument('--walletkey', help="Chia wallet key")
    parser.add_argument('address', help="Ip address of the rest api")
    args = parser.parse_args()
    e = Endpoint(chiacert=args.cert,
                 chiakey=args.key,
                 walletcert=args.walletcert,
                 walletkey=args.walletkey,
                 address=args.address)
    tags = {}
    network_name, network_prefix = network_info(e)
    tags['network_name'] = network_name
    tags['network_prefix'] = network_prefix
    space, difficulty = blockchain_state(e, tags)
    tags['network_space'] = space
    tags['network_difficulty'] = difficulty
    plot = plots(e, tags)
    wallet_balance(e, tags)
    estimated_time(e, plot, space, tags)


if __name__ == "__main__":
    main()
