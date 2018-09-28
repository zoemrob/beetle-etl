"""
Contains all tests related to the ETLHandler

NOTE: all tests must be functions with names defined using
    the following format:

    def test_XXXXX():
    
"""

from BeetleETL.Handlers import ConfigHandler
from BeetleETL.Handlers import MongoHandler
import logging
import os
import pytest


@pytest.mark.unittest
def test_custom_mongo_uri_overwrites_and_fails(config_path, config_name):
    """ verifies that setting a bad customURI overwrites other settings 
        and returns false when attempting to setup a connection
    """

    # setup config object and moddify the customMongoURI setting
    configObj = ConfigHandler.ConfigHandler(config_path)
    configObj.config['connectionInfo']['customMongoURI'] = ""

    # assert that setting up a connection with a valid uri works
    ValidMongoObj = MongoHandler.MongoHandler(configObj.config)
    assert ValidMongoObj.setup_connection() is True
    
    ValidMongoObj.close_connection() # close connection from the mongo server

    # moddify the custom uri to be a invalid server
    configObj.config['connectionInfo']['customMongoURI'] = "mongo://www.fake.com"

    # setup mongo handler object with config
    InvalidMongoObj = MongoHandler.MongoHandler(configObj.config)

    # assert that setting up a connection fails with a bad custom uri
    assert InvalidMongoObj.setup_connection() is False

    InvalidMongoObj.close_connection() # close connection from the mongo server

@pytest.mark.unittest
def test_setup_connection_pos(config_path, config_name):
    """ positive unit test: verify that valid information connects a returns
        true from setup_connection 
    """

    # setup config object and mongo object
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    MongoObj = MongoHandler.MongoHandler(ConfigObj.config)

    # setup connection and assert its valid
    response = MongoObj.setup_connection()
    assert response == True

    # close connection
    MongoObj.close_connection()

@pytest.mark.unittest
def test_setup_connection_neg(config_path, config_name):
    """ negative unit test: verify that invalid information does not connect and
        returns false from setup_connection 
    """

    # setup config object and mongo object
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    ConfigObj.config['connectionInfo']['mongoServerHost'] = "www.fake.com"
    MongoObj = MongoHandler.MongoHandler(ConfigObj.config)

    # setup connection and assert its valid
    response = MongoObj.setup_connection()
    assert response == False

    # close connection
    MongoObj.close_connection()

@pytest.mark.unittest
def test_get_val_from_dict_simple():
    """ test that a simple recurse finds the correct value"""

    # setup object to use
    test_dict = {"level1":{"level2":{"level3":"value"}}}
    response = []

    # setup instance of mongohandler to use
    MongoHandler.MongoHandler().get_val_from_dict(
        test_dict,
        ["level1", "level2", "level3"],
        out=response
    )

    assert [ "value" ] == response

@pytest.mark.unittest
def test_get_val_from_dict_all():
    """ test that a object with lists will find the correct value """

    # setup object to use
    test_dict = {"level1":[[1,2,3], [4,5,6], [7,8,9]]}
    response = []

    # setup instance of mongohandler to use
    MongoHandler.MongoHandler().get_val_from_dict(
        test_dict,
        ["level1[all][all]"],
        out=response
    )
    
    # assert that the end result matches our expected outcome
    assert [1,2,3,4,5,6,7,8,9] == response

@pytest.mark.unittest
def test_get_val_from_dict_all_nested_obj():
    """ test that a object with lists will find the correct value """

    # setup object to use
    test_dict = {"level1":[[{"ne":"v1"},1], [{"ne":"v2"},4], [{"ne":"v3"},7]]}
    response = []

    # setup instance of mongohandler to use
    MongoHandler.MongoHandler().get_val_from_dict(
        test_dict,
        ["level1[all][all]", "ne"],
        out=response
    )
    
    # assert that the end result matches our expected outcome
    assert ["v1", None, "v2", None, "v3", None] == response

@pytest.mark.unittest
def test_get_val_from_dict_valid_type():
    """ test that a object with lists will find the correct value """

    # setup object to use
    test_dict = {"level1":[[{"ne":"v1"},1], [{"ne":"v2"},4], [{"ne":"v3"},7]]}
    response = []

    # setup instance of mongohandler to use
    MongoHandler.MongoHandler().get_val_from_dict(
        test_dict,
        ["level1[all][all]", "ne"],
        out=response,
        valid_types=["str"]
    )
    
    # assert that the end result matches our expected outcome
    assert ["v1", "v2", "v3"] == response

@pytest.mark.unittest
def test_get_val_from_dict_valid_type_dict():
    """ test that a object with lists will find the correct value """

    # setup object to use
    test_dict = {"level1":[[{"ne":"v1"},1], [{"ne":"v2"},4], [{"ne":"v3"},7]],
        "level2" : {"key1":3, "key2":4}
        }
    response = []

    # setup instance of mongohandler to use
    MongoHandler.MongoHandler().get_val_from_dict(
        test_dict,
        ["level1[all][all]"],
        out=response,
        valid_types=["dict"],
        target_type="str"
    )
    
    # assert that the end result matches our expected outcome
    assert ["{'ne': 'v1'}", "{'ne': 'v2'}", "{'ne': 'v3'}"] == response

    response = []
    # setup instance of mongohandler to use
    MongoHandler.MongoHandler().get_val_from_dict(
        test_dict,
        ["level2"],
        out=response,
        valid_types=["dict"],
        target_type="str"
    )
    assert ["{'key1': 3, 'key2': 4}"] == response or ["{'key2': 4, 'key1': 3}"] == response


@pytest.mark.unittest
def test_cast_to_target_type():
    """ verify that int,str,list and dict are properly handled when casting """

    # check casting int to int
    assert type(MongoHandler.cast_to_target_type(1, "int")) == int

    # check casting int to invalid type returns None
    assert type(MongoHandler.cast_to_target_type(1, "false")) == type(None)

    # check casting dict to int or date fails
    assert type(MongoHandler.cast_to_target_type({"key":"val"}, "int")) == type(None)
    assert type(MongoHandler.cast_to_target_type({"key":"val"}, "date")) == type(None)

    # check casting dict to str passes
    assert type(MongoHandler.cast_to_target_type({"key":"val"}, "str")) == str


@pytest.mark.unittest
def test_pull_required_value_missing(config_path, config_name):
    """ verify that int,str,list and dict are properly handled when casting """

    # setup config object and mongo object
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    ConfigObj.config['mapping'][0]['sql_cols']['grade'] = {
                                            "mongo_path" : "grades[0].grade",
                                            "required" : True
                                            }  
    MongoObj = MongoHandler.MongoHandler(ConfigObj.config)

    # setup connection and assert its valid
    MongoObj.setup_connection()

    # assert a pull will fail because not all documents will have a value for zipcode
    assert MongoObj.pull_collection() == []

    # close connection
    MongoObj.close_connection()
