import os
from getpass import getpass
import napalm
import json
from napalm import get_network_driver
from typing import Union
import socket
from pprint import pprint
import yaml


class NapalmYMLActionIterator:
    _functions = []
    _arguments = []
    _current = 0

    def __init__(self, func: list = [], args: list = [], yml_file: str = ''):
        # TODO: Read yaml file and populate functions and arguments. In case no arguments, set it to None.

        if yml_file:
            with open(yml_file) as f:
                yaml_out = yaml.load(f, Loader=yaml.FullLoader)
        print(yaml_out)
        self._functions = yaml_out['func']
        self._arguments = yaml_out['args']

    def __next__(self):
        print("NEXT!")
        if self._current < len(self._functions):
            n = self._current
            self._current += 1
            return self._functions[n], self._arguments[n]
        raise StopIteration()

    def __iter__(self):
        print("ITER!")
        return self

    def __getitem__(self, item):
        return self._functions[item], self._arguments[item]

    def __len__(self):
        return len(self._functions)

    def get_funcs(self, node: napalm.base.base.NetworkDriver):
        for func, args in self:
            try:
                func = eval("node" + "." + func)
            except AttributeError as att_err:
                print(f"Function name is incorrect or not implemented by the object {node}")
                raise
            yield func, args


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


def load_func_from_yml(host: str) -> tuple:
    """Used to load napalm functions to be executed per device with arguments."""
    functions = [sr.get_facts, sr.cli]
    arguments = [None, "show ip inerface brief"]
    for f, a in functions, arguments:
        yield f, a
