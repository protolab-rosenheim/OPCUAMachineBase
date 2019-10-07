import argparse
import logging
import logging.config
import os
import json
import time

from common.config_manager import ConfigManager
from opcua_stuff.opcua_server import OPCUAServer
from machines.machine_factory import BHXFactory


def setup_logging(path_to_config, default_level=logging.INFO):
    if os.path.exists(path_to_config):
        with open(path_to_config, 'rt') as config_file:
            config = json.load(config_file)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


if __name__ == '__main__':
    commandline_parser = argparse.ArgumentParser(description='Path to config file folder')
    commandline_parser.add_argument('str', type=str, metavar='N', help='path to the config file folder')
    config_folder = commandline_parser.parse_args()
    check_threads_sleep_time = 5
    thread_list = []
    machine = None

    # Init ConfigManager
    ConfigManager(config_folder.str)
    base_config = ConfigManager.get_base_cfg()

    # Setup logger
    setup_logging(config_folder.str + '/logging.json')
    logger = logging.getLogger(__name__)

    # Starting BHX if bhx == true in config file
    if base_config.getboolean('machine', 'bhx'):
        machine = BHXFactory.create_bhx(ConfigManager.get_bhx_cfg())
        machine.start_thread()
        thread_list.append(machine.thread)

    # Starting OPCUAServer
    if machine:
        opcua_server = OPCUAServer(base_config['opcua_server']['ip_address'], base_config['opcua_server']['port'],
                                   machine)
        opcua_server.start_server()
        thread_list.append(opcua_server.thread)

    # Run till every thread has finished
    while thread_list:
        time.sleep(check_threads_sleep_time)
        for thread in thread_list:
            if not thread.isAlive():
                thread_list.remove(thread)
