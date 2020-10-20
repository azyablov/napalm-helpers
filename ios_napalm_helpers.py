import napalm
from napalm import get_network_driver
from typing import Union
import socket
from pprint import pprint
from abc import ABCMeta, abstractmethod
import os


class FQDNResolutionError(ValueError):
    def __init__(self, host):
        msg = f"Can't resolve hostname {host}"
        super().__init__(msg)

# Class to facilitate work with IOS devices
class NapalmNetworkDevice(metaclass=ABCMeta):
    def __init__(self, hostname: str, username: str, password: str, *args, **kwargs):
        self.hostname = hostname
        self.username = username
        self.password = password

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, host: str):
        self._hostname = host
        try:
            self._ip_address = socket.gethostbyname(host)
        except (socket.herror, socket.gaierror) as e:
            raise FQDNResolutionError(host + "\n" +str(e))

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def device_type(self):
        return self._device_type

    @property
    def json(self):
        return {
            "hostname": self.hostname,
            "username": self.username,
            "password": self.password,
            #    "device_type": self.device_type
        }

    def create_napalm_connection(self) -> bool:
        """
        Creates and open napalm connection
        :return: True if was opened successfully, otherwise False
        """
        if not isinstance(self.node_instance, napalm.base.base.NetworkDriver):
            driver = get_network_driver(self.device_type)
            self._node_instance = driver(**self.json)
            self._node_instance.open()
            return True
        else:
            # TODO: Check connection state and reopen [?]
            return True

    def close_napalm_connection(self):
        self._node_instance.close()
        self._node_instance = None

    @property
    def ping_ones(self) -> bool:
        if os.system(f"ping -c 1 {self.ip_address} > /dev/null 2>&1") == 0:
            return True
        return False

    @property
    def node_instance(self) -> napalm.base.base.NetworkDriver:
        return self._node_instance

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def create_running_backup(self):
        pass


class IosNetworkDevice(NapalmNetworkDevice):

    _device_type = "ios"
    _node_instance = None

    def __init__(self, hostname: str, username: str, password: str, *args, **kwargs):
        super().__init__(hostname, username, password)

    def __repr__(self):
        if self._node_instance:
            alive = self._node_instance.is_alive()
            return f"<{str(self.__class__)},\n" \
                   f"Alive: {str(alive['is_alive'])},\n" \
                   f"Connection object: {self._node_instance},\n" \
                   f"Parameters: " \
                   f"{str(self.json)}>"
        else:
            return f"Class: {str(self.__class__)}\n" \
                   f"Parameters: " \
                   f"{str(self.json)}"

    def create_running_backup(self, filename: str = None) -> bool:
        """
        Creating node backup of running configuration in current working directory with name <FQDN>.cfg or any
        other name specified in filename argument.
        :return:
        """
        if not self._node_instance:
            self.create_napalm_connection()
        config: dict = self._node_instance.get_config()
        try:
            running_config: str = config["running"]
        except KeyError as e:
            print("Didn't get running configuration.")
            return False
        if filename:
            with open(file=filename, mode='w') as fh:
                fh.writelines(running_config)
        else:
            facts = self._node_instance.get_facts()
            with open(file=facts['fqdn'] + ".cfg", mode='w') as fh:
                fh.writelines(running_config)
        return True


