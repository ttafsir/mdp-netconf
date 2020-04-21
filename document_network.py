#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""

Usage:
    $ python get_bgp_config.py

"""
import os
import json

from dotenv import load_dotenv
from ncclient import manager
from ncclient.transport.errors import SSHError
import yaml
import xmltodict

from utils import from_yaml


def backup_config(conn, device, hostname):
    """
    Connect to device and write config locally as JSON

    Args:
        conn (object): Instance or ncclient.manager
        device (dict): dictionary with device donnection details
        hostname (str): device hostname

    Returns: None
    """
    # Get the running configuration and extra the 'data' xml
    resp = conn.get_config('running').data_xml

    # load xml data as OrderedDict
    resp_dict = xmltodict.parse(resp)

    # write JSON data to file
    output_filepath = f"outputs/{hostname}_{device['host']}.json"
    print(f'Backing up config for: {hostname} dest: {output_filepath}')
    with open(output_filepath, 'w') as fp:
        json.dump(resp_dict, fp, indent=2)


def main():
    """
    Entrypoint for script
    """

    # load environment vars from a .env file
    load_dotenv()

    # load hosts inventory
    hosts = from_yaml('netconf/hosts.yml')
    combined_hosts = { **hosts['spoke'], **hosts['hub'] }


    for hostname, attrs in combined_hosts.items():

        device = {
            'host': attrs['host'],
            'username': os.getenv('NETCONF_USER'),
            'password': os.getenv('NETCONF_PASSWORD'),
            'port': attrs['netconf_port'],
            'hostkey_verify': False,
            'device_params': {'name': "csr"}
        }

        try:
            print(f'connecting to: {hostname}')
            with manager.connect(**device) as mgr:
                backup_config(mgr, device, hostname)
            print('status: success')

        except SSHError:
            print('status: SSH transport error')
            continue

        except Exception as e:
            print(f'status: {str(e)}')
            continue


if __name__ == '__main__':
    main()