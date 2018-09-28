"""
Manages configuration file options
"""

import json
import os
import getpass
import logging
from pydoc import locate
from collections import OrderedDict


class ConfigHandler():
    """ Simple class to manage the config json file
    """

    def __init__(self, config_file=""):
        self.config_path = config_file
        self.config = self.setup_config(config_file)
        self.valid = True # represents the state of the config as usable or not
        
    def setup_config(self, file):
        """ parses config file into

            Arguments: fl {string} -- path of json config file
            Returns: 
                [dict] -- if successful, python dict of config file
                [None] -- if error occurs parsing valid json
        """
        logging.info("Setting up configuration settings based on config file")

        # verify that the json file is a regular file
        # first attempt to open provided file and if fails, looks for default file
        if not os.path.isfile(file):
            logging.error("ERROR: {}: {}".format("FileNotFoundError", "Could not find config"))
            return None     

        # open the json file and return it as a dict
        with open(file, "r") as file_open:
            try:
                json_loaded = json.load(file_open, object_pairs_hook=OrderedDict)
                logging.info("Successfully set up configuration settings")
                
                # check if secure auth should be used for passwords
                try:
                    if json_loaded["useSecureAuthentication"]:
                        logging.info("Using secure authentication")
                        json_loaded = self.setup_auth(json_loaded)
                except Exception as err:
                    logging.error("no parameter for 'useSecureAuthentication', should be true/false\n  -> {}".format(err))
                    return None
                return json_loaded
            except Exception as e:
                logging.error("could not parse config file\n  -> {}".format(e))
                return None

    @staticmethod
    def setup_auth(json_loaded):
        """ prompts the user for mongodb/sql server password 
        """
        json_loaded["connectionInfo"]["mongoServerPass"] = getpass.getpass("Provide Mongodb Password> ")
        json_loaded["connectionInfo"]["sqlServerPass"] = getpass.getpass("Provide Sql Server Password> ")
        if json_loaded["emailInfo"]["useEmailNotify"]:
            json_loaded["emailInfo"]["fromPass"] = getpass.getpass("Provide email Password> ")

        return json_loaded

    def check_key(self, key, obj, 
        expected_type=None, isfile=False, valid_values=None, alt_title=None, verbose=False):
        """ 
            Arguments:
                key {string} -- key to check in obj
                obj {dict} -- obj where key should be
                
            Optional Arguments:
                expected_types {list of type obj} -- the expected typse of obj[key]
                isfile {bool} -- performs additional check if obj[key] is a file
                valid_values {list} -- performs extra check to see if obj[key] is in list
                alt_title {string} -- alternate key to print out
                verbose {string} -- only print out INVALID messages
        """
        if not alt_title:
            alt_title = key
        passes = True
        
        # check if value exists
        value = None
        try:
            value = obj[key]
        except:
            advprint((alt_title, "INVALID", "missing/misspelled"))
            self.valid = False
            return

        # if it exists check type
        if expected_type is not None:
            
            if not isinstance(value, expected_type) and value is not None:
                advprint((
                    alt_title, 
                    "INVALID", 
                    "found: " + type(value).__name__, 
                    "expected: " + expected_type.__name__
                    ))
                passes = False
        
        # check for file if specified
        if isfile:
            if not os.path.isfile(value):
                advprint((alt_title, "INVALID", "not valid path"))
                passes = False
        
        # check if value is in list
        if valid_values is not None and value not in valid_values:
            advprint((
                alt_title, 
                "INVALID", 
                "found: " + value,
                "expecting one: ({})".format(",".join(valid_values))
                ))
            passes = False

        # if the key passes it can be displayed to the user
        if passes:
            if verbose:
                advprint((alt_title, "VALID"))
        else:
            self.valid = False
                 
                
    def verify_format(self):
        """ Checks the config after setup, to make sure a proper format is used

            Returns:
                [bool] -- True if all required fields are valid or False
        """

        # top level keys
        #self.check_key('useSecureAuthentication', self.config, bool)
        if "process" in self.config:
            self.check_key('process', self.config, str, valid_values=("manual", "daemon"))
            if  self.config['process'] != "manual":
                self.check_key('TriggerFrequencyHrs', self.config, int)
       
        # check connectionInfo keys
        if 'connectionInfo' in self.config and isinstance(self.config['connectionInfo'], dict):

            if 'customMongoURI' in self.config['connectionInfo'] and self.config['connectionInfo']['customMongoURI'] != "":
                self.check_key('customMongoURI', self.config['connectionInfo'], str)
            else:
                self.check_key('useMongoURISRV', self.config['connectionInfo'], bool)
                self.check_key('mongoServerHost', self.config['connectionInfo'], str)
                self.check_key('mongoServerUser', self.config['connectionInfo'], str)
                if not self.config['useSecureAuthentication']:
                    self.check_key('mongoServerPass', self.config['connectionInfo'], str)
                if 'useMongoSSL' in self.config['connectionInfo']:
                    self.check_key('useMongoSSL', self.config['connectionInfo'], bool)
            
            self.check_key('mongoDatabase', self.config['connectionInfo'], str)
            self.check_key('mongoCollection', self.config['connectionInfo'], str)            

            self.check_key('useWindowsAuth', self.config['connectionInfo'], bool)
            self.check_key('sqlServerDriver', self.config['connectionInfo'], str)
            self.check_key('sqlServerHost', self.config['connectionInfo'], str)
            self.check_key('sqlServerUser', self.config['connectionInfo'], str)
            self.check_key('sqlServerPass', self.config['connectionInfo'], str)
            self.check_key('sqlServerDatabase', self.config['connectionInfo'], str)
            if not self.config['useSecureAuthentication']:
                    self.check_key('sqlServerPass', self.config['connectionInfo'], str)

        else:
            advprint(('connectionInfo', 'INVALID', 'missing'))
            self.valid = False

        # check sql error handling keys
        if 'sqlErrorHandling' in self.config and isinstance(self.config['sqlErrorHandling'], dict):
            expected = ("break", "skip", "update")
            for key, val in self.config['sqlErrorHandling'].items():
                if val not in expected:
                    location = 'sqlErrorHandling/' + key
                    advprint((location, 'INVALID', 'found: ' + str(val), 'Expected One: ' + str(expected)))
                    self.valid = False
        else:
            advprint(("sqlErrorHandling", 'INVALID', 'missing'))
            self.valid = False

        # check email information keys
        if 'emailInfo' in self.config and isinstance(self.config['emailInfo'], dict):
            self.check_key('useEmailNotify', self.config['emailInfo'], bool)
            if 'useEmailNotify' in self.config['emailInfo'] and self.config['emailInfo']['useEmailNotify'] == True:
                self.check_key('smtpHost', self.config['emailInfo'], str)
                self.check_key('smtpPort', self.config['emailInfo'], int)
                self.check_key('subject', self.config['emailInfo'], str)
                self.check_key('fromEmail', self.config['emailInfo'], str)
                self.check_key('fromPass', self.config['emailInfo'], str)
                self.check_key('toEmail', self.config['emailInfo'], list)
                if len(self.config['emailInfo']['toEmail']) < 1:
                    advprint(('toEmail', 'INVLAID', 'requires at least 1 email'))        
                    self.valid = False
        else:
            advprint(('emailInfo', 'INVALID', 'missing'))
            self.valid = False

        # verify mapping
        if "mapping" in self.config:
            idx = 1
            for m in self.config['mapping']:
                parent = "map"+str(idx)
                if 'sql_dest' in m:
                    self.check_key('schema', m['sql_dest'], str, alt_title=parent+"/schema", verbose=False)
                    self.check_key('db', m['sql_dest'], str, alt_title=parent+"/db", verbose=False)
                    self.check_key('table', m['sql_dest'], str, alt_title=parent+"/table", verbose=False)
                else:
                    advprint((parent+'/sql_dest', "INVALID", 'missing'))
                    self.valid = False

                if 'sql_cols' in m:
                    for val in m['sql_cols'].values():
                        if 'mongo_path' in val:
                            self.check_key('mongo_path', val, str, alt_title=parent+"/mongo_path", verbose=False)
                        
                        if 'target_type' in val:
                            self.check_key('target_type', val, str, 
                                alt_title=parent+"/target_type", 
                                verbose=False,
                                valid_values=("date", "str", "int")
                                )
                        if 'required' in val:
                            self.check_key('required', val, bool, alt_title=parent+"/required")
                        if 'allowMongoUpdate' in val:
                            self.check_key('allowMongoUpdate', val, bool, alt_title=parent+"/allowMongoUpdate")
                            if 'mongoUpdateType' in val:
                                self.check_key('mongoUpdateType', val, str, alt_title=parent+"/mongoUpdateType", valid_values=["str", "int", "float", "date"])
                else:
                    advprint((parent+'/sql_cols', "INVALID", 'missing'))
                    self.valid = False
                idx += 1
        else:
            advprint(('mapping', 'INVALID', 'missing'))
            self.valid = False

        # make sure data field exists and create it if it does not
        self.check_data_field()

        return self.valid

    def check_data_field(self):
        """ verify the data field exists and contains the required fields """

        if 'data' not in self.config:
            self.config['data'] = {}
        
        # initialize / check pullOnlyNew option
        if 'pullOnlyNew' not in self.config['data']:
            self.config['data']['pullOnlyNew'] = False

        self.check_key('pullOnlyNew', self.config['data'], bool, alt_title="data/pullOnlyNew")

        if 'lastMongoIdPulled' not in self.config['data']:
            self.config['data']['lastMongoIdPulled'] = ''

    def save_config(self):
        """ saves the current values int self.config to its path """
        basename = os.path.basename(self.config_path)
        try:
            with open(self.config_path, "w") as file:
                json.dump(self.config, file, indent=4)
                logging.info("Successfully updated config ({}) to file".format(basename))
        except Exception as err:
            logging.critical("Could not write config ({}) to file\n -> {}".format(basename, err))



################### STATIC HELPER FUNCTIONS ###################

def advprint(args):
    """ spaces out elements in a list and prints them """
    s = "{:.<30}".format(args[0])
    s += "".join( "{:<19}".format(i) for i in args[1:] )
    print("Config: " + s) 
    logging.info("Config: " + s)


            
