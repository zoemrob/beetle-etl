"""
Contains all tests related to the ConfigHandler

NOTE: all tests must be functions with names defined using
    the following format:

    def test_XXXXX(): 
"""

from BeetleETL.Handlers import ETLHandler
from BeetleETL.Handlers import ConfigHandler
import os
import pytest

@pytest.mark.unittest
def test_valid_config_setup(config_path, config_name):
    """ verify that a valid config file opens and is not None """
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    assert ConfigObj != None

@pytest.mark.functest
def test_valid_config_format(config_path, config_name):
    """ verifies that a valid config passes the formatting test """
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    return_value = ConfigObj.verify_format()
    assert return_value == True

@pytest.mark.unittest
def test_verify_format_simple(config_path, config_name):
    """ verifies a simple config is valid """
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    return_value = ConfigObj.verify_format()
    assert ConfigObj.valid == True and return_value == True

@pytest.mark.unittest
def test_verify_format_invalid(config_path, config_name):
    """ verifies an error in the config returns false """
    ConfigObj = ConfigHandler.ConfigHandler(config_path)

    # moddify the config to be invalid
    del ConfigObj.config['connectionInfo']

    # perform verification
    return_value = ConfigObj.verify_format()

    # assert config is not valid
    assert ConfigObj.valid == False and return_value == False

@pytest.mark.unittest
def test_check_key_simple():
    """ test that a value in a dictionary is the correct type """
    test_dict = {"key" : "value"}

    # setup config object
    ConfigObj = ConfigHandler.ConfigHandler()
    
    # assert check_key is fine with a valid key and object
    ConfigObj.check_key("key", test_dict)
    assert ConfigObj.valid == True 

    # assert check_key errors with a invalid key for object
    ConfigObj.check_key("key", {"wrong_key":"value"})
    assert ConfigObj.valid == False


@pytest.mark.unittest
def test_check_key_optional_checks():
    """ test all the optional parameters in check_key for proper function """
    test_dict = {"key" : "value"}

    # setup config object
    ConfigObj = ConfigHandler.ConfigHandler()
    
    # assert check_key passes if expected_type is found
    ConfigObj.check_key("key", test_dict, expected_type=str)
    assert ConfigObj.valid == True 

    # assert check_key fails if expected_type is not found
    ConfigObj.valid = True # reset config status
    ConfigObj.check_key("key", test_dict, expected_type=int)
    assert ConfigObj.valid == False

    # assert check_key passes if key is in valid_values
    ConfigObj.valid = True # reset config status
    ConfigObj.check_key("key", test_dict, valid_values=["value"])
    assert ConfigObj.valid == True

    # assert check_key fails if key is not in valid_values
    ConfigObj.valid = True # reset config status
    ConfigObj.check_key("key", test_dict, valid_values=["wrong_value"])
    assert ConfigObj.valid == False


@pytest.mark.unittest
def test_check_data_field(config_path, config_name):
    """ verify the data field is properly handled """

    ConfigObj = ConfigHandler.ConfigHandler(config_path)

    # ensure no key is named 'data' in config
    if 'data' in ConfigObj.config:
        del ConfigObj.config['data'] 

    # assert absense of 'data' in the config, results in a new dict
    ConfigObj.check_data_field()

    assert 'data' in ConfigObj.config and 'last_mongo_id_pulled' in ConfigObj.config['data']


@pytest.mark.unittest
def test_empty_config_format(config_path, config_name):
    """ verifies an empty dictionary for the config is not valid """
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    ConfigObj.config = {}
    assert ConfigObj.verify_format() == False


""" example of parameterized variables with custom names
@pytest.mark.parametrize("var", ["var_data"], ids=["var_name"])
def test_config(var):
    """ """
    assert 3 == 3
"""

