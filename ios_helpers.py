# Device information
import os
from getpass import getpass
import napalm
import json
from napalm import get_network_driver
from typing import Union
import socket
from pprint import pprint

# Class to facilitate work with IOS devices
class IosNetworkDevice():

    def __init__(self, hostname: str, username: str, password: str, device_type: str = "ios", *args, **kwargs):
        self.hostname = hostname
        self.password = password
        self.username = username
        self.device_type = device_type

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, host: str):
        self.__hostname = host
        try:
            self.__ip_address = socket.gethostbyname(host)
        except (socket.herror, socket.gaierror) as e:
            print(e)
            msg = f"Can't resolve hostname {host}"
            raise ValueError(msg)

    @property
    def ip_address(self):
        return self.__ip_address

    @property
    def json(self):
        return {
            "hostname": self.__hostname,
            "username": self.username,
            "password": self.password,
            "device_type": self.device_type
        }

    def __str__(self):
        return str(self.json)


def load_json_data(file_name: str) -> dict:
    """
    The function facilitates parameters load from JSON file
    :param file_name:
    :return: dictionary
    """
    # Reading JSON file
    path_input_file: Union[bytes, str] = os.path.abspath(file_name)
    if os.path.exists(path_input_file) and os.access(path_input_file, os.R_OK):
        with open(path_input_file, mode='r', encoding='utf-8') as input_config_file:
            try:
                data = json.load(input_config_file)
            except json.JSONDecodeError as de:
                print('JSON format decode error.', de)
                raise
        return data
    else:
        msg = "Can't access file {}".format(file_name)
        raise ValueError(msg)

def create_napalm_connection(device: dict) -> napalm.base.base.NetworkDriver:
    dev_type = device.pop("device_type")
    driver = get_network_driver(dev_type)
    node_instance = driver(**device)
    node_instance.open()
    return node_instance


def create_checkpoint(device: napalm.base.base.NetworkDriver, conf_delta: str = "") -> bool:
    chkp = device._get_checkpoint_file()
    with open(file="nxos_chkp.conf", mode='w') as fh:
        fh.write(chkp)
        if len(conf_delta) > 1:
            fh.write(conf_delta)
    if chkp:
        return True
    else:
        return False


def create_backup(conn_node_instance: napalm.base.base.NetworkDriver, filename: str = None):
    """
    Creating node backup of running configuration in current working directory with name <FQDN>.cfg
    :param conn_node_instance:
    :return:
    """
    config = conn_node_instance.get_config()
    running_config: str = config["running"]
    lines = running_config.splitlines(keepends=True)
    if filename:
        with open(file=filename, mode='w') as fh:
            fh.writelines(lines)
    else:
        facts = conn_node_instance.get_facts()
        config = conn_node_instance.get_config()
        running_config: str = config["running"]
        with open(file=facts['fqdn'] + ".cfg", mode='w') as fh:
            fh.writelines(lines)


