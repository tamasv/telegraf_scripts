#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import requests
import urllib3
urllib3.disable_warnings()


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
    plot_tags = ['plot-seed', 'plot_public_key', 'pool_public_key', 'size']
    plot_values = ['filename', 'filesize', 'time_modified']
    plots = e.get_data('get_plots', 8560)
    for plot in plots['plots']:
        tags = ",".join(
            [f"{k}={v}" for k, v in plot.items() if k in plot_tags])
        if len(extra_tags):
            tags += ","
            tags += ",".join([f"{k}={v}" for k, v in extra_tags.items()])
        values = ",".join(
            [f"{k}={v}" for k, v in plot.items() if k in plot_values])
        print("chia_plots,{} {}".format(tags, values))


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
    if len(extra_tags):
        tags += ","
        tags += ",".join([f"{k}={v}" for k, v in extra_tags.items()])
    values = ",".join(
        [f"{k}={float(v)}" for k, v in balance.items() if k in balance_values])
    print("chia_wallet,{} {}".format(tags, values))


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
    plots(e, tags)
    wallet_balance(e, tags)


if __name__ == "__main__":
    main()
