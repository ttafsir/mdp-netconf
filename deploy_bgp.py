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


# load hosts and configuration data
HOSTS = from_yaml('netconf/hosts.yml')
HOST_VARS = from_yaml('netconf/host_vars', directory=True)
HUB_DATA = from_yaml('netconf/hub.yml')
SPOKE_DATA = from_yaml('netconf/spoke.yml')



def build_hostvars(hostname):
    """
    Build combined dict for host variables
    """
    _vars = HOST_VARS[hostname]

    if hostname in HOSTS['spoke']:
        _vars.update(SPOKE_DATA)
    else:
        _vars.update(HUB_DATA)

    return _vars


def build_bgp(bgp_data: dict ) -> dict:
    """
    Returns YANG-structured dict that for Cisco
    IOS-XE native YANG data model
    """

    bgp = {
        "@xmlns": "http://cisco.com/ns/yang/Cisco-IOS-XE-bgp",
        **bgp_data
    }
    return bgp


def build_interface(intf_data: dict) -> dict:
    pass


def build_xml_payload(host_vars):
    """
    Returns YANG-structured dict for the Cisco IOS-XE
    native data model configuation
    """

    interface_content = None
    bgp_content = None

    payload_shell = {
        "config": {
            "native": {
                "@xmlns": "http://cisco.com/ns/yang/Cisco-IOS-XE-native",

            }
        }
    }

    if (interface_data := host_vars.get('interface')) is not None:
        interface_content = build_interface(interface_data)
        payload_shell['config']['native'].update(
            {"interface": interface_content}
        )

    if (bgp_data := host_vars.get('router_bgp')) is not None:
        bgp_content = build_bgp(bgp_data)
        payload_shell['config']['native'].update(
            {"router": {"bgp": bgp_content}}
        )

    return xmltodict.unparse(payload_shell)




def main():
    """
    Entrypoint for script
    """

    # load environment vars from a file
    load_dotenv()

    # combine hubs and spoke into single dict
    combined_hosts = { **HOSTS['spoke'], **HOSTS['hub'] }

    for hostname, attrs in combined_hosts.items():

        device = {
            'host': attrs['host'],
            'username': os.getenv('NETCONF_USER'),
            'password': os.getenv('NETCONF_PASSWORD'),
            'port': attrs['netconf_port'],
            'hostkey_verify': False,
            'device_params': {'name': "csr"}
        }

        host_vars = build_hostvars(hostname)
        payload = build_xml_payload(host_vars)

        if payload is None:
            continue

        with manager.connect(**device) as mgr:
            print(f'connecting to: {hostname}', end=" ")
            resp = mgr.edit_config(target='running', config=payload)
            print(f'DONE')


if __name__ == '__main__':
    main()