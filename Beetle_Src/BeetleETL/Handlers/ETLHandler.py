"""
Manages entire etl process including mongo, sql and config
operations and interactions as specified by mongotosqlcli
"""
from BeetleETL.Handlers import ConfigHandler
from BeetleETL.Handlers import MongoHandler
from BeetleETL.Handlers import SQLHandler
import logging
import json
import smtplib
import os


def logruntimeerror(func):
    """ Decorator Function to catch and log runtime errors encountered
        by the program. This logging is only present in the ETL Handler
        because all other aspects of Beetle will be called from this object.
        So logging runtime errors here will account for errors encounted in 
        other handlers.
    """
    def wrapper(*args, **kwargs):
        try:
          func(*args, **kwargs)
        except Exception as e:
          logging.exception("Found a runtime error: {}".format(e))
          print("Beetle encountered a runtime error:\n -> {}".format(e))
    return wrapper


class ETLHandler():
    """ main entry point for MongoTOSQL, this object handles
        - setup of config file (from ConfigHandler)
        - setup of mongodb/sqlserver controllers
        - execution of pull/push operations defined in mongodb/sql controllers
    """ 
    @logruntimeerror
    def __init__(self, config_file_path=""):
        logging.basicConfig(format='%(asctime)s -- %(levelname)s: %(message)s',filename='ETLactivity.log',level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
        logging.info(" ========== ETL HANDLER INITIATED for ({}) ==========".format(os.path.basename(config_file_path)))
        self.config_path = config_file_path
        self.config_handler = ConfigHandler.ConfigHandler(config_file_path)
        

        # check config handler config exists and is formatted correctly
        if self.config_handler.config == None:
            logging.error("Config json could not be loaded or is invalid, exiting ETL handler")
            print("ERROR: Config json could not be loaded or is invalid, exiting")
            
        self.is_config_valid = self.config_handler.verify_format()
        
        if self.is_config_valid is False:
            logging.error("Config format is invalid, exiting ETL handler")
            print("ERROR: invalid config format, exiting")
            
        else:
            logging.info("Config format is valid")

        self.mongo_handler = None
        self.sql_handler = None
        self.package_queue = []   # packages to send to destination db 
        
        # setup handlers
        self.setup_handles()

    @logruntimeerror
    def setup_handles(self):
        """ initializes and parses information from the config handler then
            attempts to establish connections for the mongo_handle and sql_handle
        """

        # setup mongo handler
        self.mongo_handler = MongoHandler.MongoHandler(self.config_handler.config)

        # setup sql handler
        self.sql_handler = SQLHandler.SQLHandler(self.config_handler.config)

    @logruntimeerror
    def get_from_mongo(self, filter_dict=None, add_index=False):
        """ pulls collections specified in the config from the mongo handler
            and returns the parsed packages in a list.

            Arguments:
                filter {string} -- custom mongo query to use

            Return:
                [list of Packages] -- sets self.package_queue to list of Handlers.Package
                                      objects with data and information
                                   -- None, if an empty list is returned from pull_collection()
        """
        # decide whether to use the default filter, custom filter or no filter
        if filter_dict is None and self.mongo_handler.mongo_filter:
            filter_dict = self.mongo_handler.mongo_filter

        # pull documents from MongoDB into package_queue list
        self.package_queue = self.mongo_handler.pull_collection(filter_dict, add_index)

        # if nothing got returned let the user know
        if not self.package_queue or len(self.package_queue) == 0:
            logging.warning("Something may be wrong: nothing was pulled from mongo")
            return None
       
    @logruntimeerror
    def xml_to_dataframe(self, xml_string):
        """ converts an xml string to a pandas dataframe """
        return self.mongo_handler.xml_to_dataframe(xml_string)

    @logruntimeerror
    def save_dataframe_to_mongo(self, dataframe, save_msg=None):
        """ takes xml as a string and then converts it to a list of dicts which are then compared
            to the self.package_queue variable. all paths in sql_cols from the config which have the
            parameter "interjectSave" : true, will be used to upsert back into mongo
        """    
        
        # first convert the dataframe to a python dict
        result_list = self.mongo_handler.dataframe_to_dict(dataframe)
        
        # perform update calls on each (query, update) tuple in result_list
        return self.mongo_handler.save_collection(result_list, save_msg)

    @logruntimeerror
    def push_to_sql(self, update_config=True):
        """ pushes all packages in self.package_queue to the sql connection OR
            if queue is not none, pushes a custom queue of packages.

            Arguments:
                queue {list of Packages} -- custom queue to send

            Return:
                [bool] -- true, successfully sent all packages
        """
        # call SQLHandler function to insert a list of packages
        if self.package_queue == [] or self.package_queue == None: 
            return False

        return_value = self.sql_handler.push_packages(self.package_queue)

        # update config file
        if update_config and return_value:
            self.config_handler.save_config()
            return True
        else:
            logging.warning("got False back from SQLHandler, not saving last_pulled_mongo_id")
            return False
    
    @logruntimeerror
    def update_config(self):
        """allows the user to specify if they want changes made to the config to be saved"""
        
        self.config_handler.save_config()
        return True

    @logruntimeerror
    def get_most_recent_logs(self):
        """ scans from newest log insertions till the identifier is found """
        try:
            with open('ETLactivity.log') as file:
                output = []

                # open log to scan
                log_lines = file.read().splitlines()

                # reverse list so we scan from end of list
                log_lines.reverse()
                s = " ========== ETL HANDLER INITIATED for ({}) ==========".format(
                        os.path.basename(self.config_path)
                        )
                
                # scan and add lines to output
                for idx in range(len(log_lines)):
                    if s in log_lines[idx]:
                        output.append(log_lines[idx])
                        break
                    else:
                        output.append(log_lines[idx])

                # reverse again so log is in proper order
                output.reverse()
                return output
        except Exception as err:
            logging.error("Could not open log for email update\n  -> {}".format(err))
            return None

    @logruntimeerror
    def send_email_update(self, message=""):
        """ creates an email of all log information since the program last ran
            
            Arguments:
                message {string} -- allows the overriding of the email to send
            Returns:
                [bool] -- true if everything works 
        """
        if 'emailInfo' not in self.config_handler.config or \
            self.config_handler.config["emailInfo"]["useEmailNotify"] is False:
            return False

        if message == "":
            message = self.get_most_recent_logs()
            if not isinstance(message, list):
                logging.error("No content to email")
                return False
            message = " \n".join(message)
            if len(message) < 1:
                logging.warn("not enough information in log to email")
                return False

        # setup email message
        email_message = """\
From: {}
To: {}
Subject: {}

{}
        """.format(self.config_handler.config["emailInfo"]["fromEmail"],\
            ",".join(self.config_handler.config["emailInfo"]["toEmail"]),\
            self.config_handler.config["emailInfo"]["subject"],\
            message)

        try:
            # port should match your SMTP server
            server = smtplib.SMTP(\
                self.config_handler.config["emailInfo"]["smtpHost"],\
                self.config_handler.config["emailInfo"]["smtpPort"])

            logging.info("Successfully setup SMTP server on {}:{}".format(\
                self.config_handler.config["emailInfo"]["smtpHost"],
                self.config_handler.config["emailInfo"]["smtpPort"]))
            
            server.starttls()

            server.login(self.config_handler.config["emailInfo"]["fromEmail"],\
                self.config_handler.config["emailInfo"]["fromPass"])

            logging.info("Successfully setup logged into email {}".format(\
                self.config_handler.config["emailInfo"]["fromEmail"]))

            logging.info("Successfully sent notification to email ({})".format(\
                ",".join(self.config_handler.config["emailInfo"]["toEmail"])))

            # could not get sendmail to iterate over multiple emails
            # NOTE: this is a manual solution
            for email in self.config_handler.config["emailInfo"]["toEmail"]: 
                server.sendmail(self.config_handler.config["emailInfo"]["fromEmail"], \
                    email, \
                    email_message)

            server.quit()
            return True
            
        except Exception as err:
            logging.error("could not send email notification due to:\n  -> {}".format(err))
            return False
    