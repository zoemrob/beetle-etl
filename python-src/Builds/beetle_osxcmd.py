#!/usr/bin/env python
"""
User access point to the MongoTOSQL package
"""

from BeetleETL.Handlers import ETLHandler
import logging
import sys
import os
import json

CONFIG_DIR_PATH = "beetle_configs"

# main event for client
def main():
    logging.info("==================== CLIENT INITIATED ====================")

    try:
        if not os.path.isdir(CONFIG_DIR_PATH):
            logging.error("could not find config directory ({})".format(CONFIG_DIR_PATH))
            print("could not find config directory")
            return
    except:
        return
    
    for config in os.listdir(CONFIG_DIR_PATH):
        config_relative_path = os.path.join(CONFIG_DIR_PATH, config)

        # open config to see if it should be used
        config_dict = open_config_file(config_relative_path)
        

        if "useConfig" in config_dict and not config_dict['useConfig']:
            logging.info("Not using config ({})".format(config))
            print("Skipping config ({})".format(config))
            continue
        else:
            logging.info("Using config ({})".format(config))
            print("Using config ({})".format(config))

        # setup handles for config, mongo, and sql
        ETL = ETLHandler.ETLHandler(config_relative_path) 
        if not ETL:
            return

        logging.info(" <CLIENT> attempting to get from mongo")
        ETL.get_from_mongo()
        logging.info(" <CLIENT> successfully pulled from mongo")
        ETL.push_to_sql()
        logging.info(" <CLIENT> pushed to sql server")
        ETL.send_email_update()

    #except Exception as err:
    #    logging.error("could not run MongoToSQL on all configs\n -> {}".format(err))
    

def open_config_file(file):
    """ returns the config file as a python dict """
    with open(file, "r") as file_open:
        return json.load(file_open)



# run main function only when script is called as a program rather then a module 
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s -- %(levelname)s: %(message)s',filename='ETLactivity.log',level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
    main()

    input("< Enter Any Key to Exit >")

    #exit normally
    logging.info("exiting normally")
    exit(0)