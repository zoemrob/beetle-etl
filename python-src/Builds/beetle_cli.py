#!/usr/bin/env python
"""
User access point to the Beetle package

USE:
0                1     2         3
./beetle_cli -conf FILE_PATH start
"""

from BeetleETL.Handlers import ETLHandler
from BeetleETL.DaemonHandler import Daemon
import logging
import sys
import json

# main event for client
def main():
    logging.info("==================== CLIENT INITIATED ====================")

    # parse user command line args
    options = parse_cli_args()
    if not options:
        return
    # setup ETL handler
    ETL = ETLHandler.ETLHandler(options["config"]) # here i setup handles for config, mongo, and sql
    
    # after passing path as string to ETL setup json as dict
    options['config'] = open_config_file(options['config'])

    # run process manually, as service or as daemon
    if "process" not in options["config"] or options["config"]['process'] == "manual":
        logging.info(" <CLIENT> attempting to get from mongo")
        return_value = ETL.get_from_mongo()
        if return_value != []:
            logging.info(" <CLIENT> successfully pulled from mongo")
            ETL.push_to_sql()
        else:
            logging.info(" <CLIENT> pulling from mongo returned nothing or something went wrong")
        
        ETL.send_email_update()
    
    elif options["config"]['process'] == "daemon" and 'TriggerFrequencyHrs' in ETL.config_handler.config:

        # setup daemon handler
        DaemonHandler = Daemon(ETL, options['config']['TriggerFrequencyHrs'])
        print("daemon setup properly")

        # depending on command connect with daemon and run command
        if options['command'] == "start":
            print("starting daemon")
            DaemonHandler.start()

        elif options['command'] == "stop":
            DaemonHandler.stop()

    
def try_to_get_next(command_list, idx, err_msg=""):
    """ attempts to return the command at a index """
    try:
        return command_list[idx]
    except Exception as err:
        logging.error(" <CLIENT> Invalid command line arg: {}\n  -> {}".format(err_msg, err))


def open_config_file(file):
    """ returns the config file as a python dict """
    with open(file, "r") as file_open:
        return json.load(file_open)


def parse_cli_args():
    """ returns a dict of options """
    options = dict()
    argc = len(sys.argv)

    # make sure there are commands (config is minimum needed)
    if argc < 2:
        logging.error(" <CLIENT> No config file specified")
        print("ERROR: invalid number of arguments, must specify config file")
        return False

    # if only 1 arg exists it should be considered the config file
    if argc == 2:
        options["config"] = sys.argv[1]
        options["command"] = "start"
    
    elif argc == 3:
        options["config"] = sys.argv[1]
        if sys.argv[2] != 'start' and sys.argv[2] != 'stop':
            logging.error(" <CLIENT> invalid option for command")
            return False
        options["command"] = sys.argv[2]

    elif argc > 3:
        # if more args exist try to parse them out into options
        # NOTE: this is where we can add all command line parameters
        for cmd in range(len(sys.argv)):
            if "-conf" in sys.argv[cmd]:
                options['config'] = try_to_get_next(sys.argv, cmd, "config file" )
            elif "-cmd" in sys.argv[cmd]:
                options['command'] = try_to_get_next(sys.argv, cmd, "command, (should be 'start' or 'stop')")

    return options


# run main function only when script is called as a program rather then a module 
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s -- %(levelname)s: %(message)s',
                        filename='ETLactivity.log',
                        level=logging.DEBUG, 
                        datefmt='%m/%d/%Y %I:%M:%S %p'
                        )
    main()
