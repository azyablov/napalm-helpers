from napalm import get_network_driver
import napalm


def create_napalm_connection(device: dict) -> napalm.base.base.NetworkDriver:
    """
    Create napalm connection in respect of device driver type.
    :param device: dictionary with input params
                 dict(
                    hostname="<hostname>",
                    device_type="<type>",
                    username="<user>",
                    password="password",
                    optional_args={},
                    )
    :return napalm.base.base.NetworkDriver:
    """
    dev_type = device.pop("device_type")
    driver = get_network_driver(dev_type)
    node_conn = driver(**device)
    node_conn.open()
    return node_conn


def create_backup(node_conn: napalm.base.base.NetworkDriver):
    """
    Creating node backup of running configuration in current working directory with name <FQDN>.cfg
    :param node_conn:
    :return:
    """
    facts = node_conn.get_facts()
    config = node_conn.get_config()
    running_config: str = config["running"]
    lines = running_config.splitlines(keepends=True)
    with open(file=facts['fqdn'] + ".cfg", mode='w') as fh:
        fh.writelines(lines)
