"""
Contains all tests related to the ETLHandler

NOTE: all tests must be functions with names defined using
    the following format:

    def test_XXXXX():
    
"""

from BeetleETL.Handlers import ETLHandler
from BeetleETL.Handlers import ConfigHandler
import logging
import pytest


### Functional Tests ###

@pytest.mark.functest
def test_emailupdate(config_path, config_name):
    """ verifies that emailupdate returns true (aka is successful)"""

    ETL = ETLHandler.ETLHandler(config_path)

    ETL.config_handler.config['emailInfo']['useEmailNotify'] = True
    ETL.config_handler.config['emailInfo']['subject'] = "BeetleETL Test Email"
    
    # assert that the emails were sent successfully
    assert ETL.send_email_update(message="BeetleETL: test message") is True


### unit Tests ###

@pytest.mark.unittest
def test_pull_count_from_mongo(config_path, config_name):
    """ verifies the etl handler can pull X documents from mongo """

    ETL = ETLHandler.ETLHandler(config_path)

    # moddify config mapping so we can just pull simple docs
    test_mapping = {
        "sql_dest": {
            "schema": "",
            "db": "",
            "table": ""
        },
        "sql_cols": {
            "_id": { "mongo_path": "_id" }
        }
    }

    ETL.config_handler.config['mapping'] = []
    ETL.config_handler.config['mapping'].append(test_mapping)
    ETL.config_handler.config['data']['last_mongo_id_pulled'] = ""

    # verify mapping change worked
    assert len(ETL.config_handler.config['mapping']) == 1

    # first get the number of docs in the mongodatabase
    collection_size = ETL.mongo_handler.get_collection_size()

    # pull collection
    ETL.get_from_mongo()

    # ensure packages exist
    assert len(ETL.package_queue) == 1

    # assert package length matches the collection size
    assert collection_size == len(ETL.package_queue[0].data)

@pytest.mark.unittest
def test_valid_etl_setup(config_path, config_name):
    """ verifies that the etlhandler will return non-none types 
        for sql and mongo handlers
    """
    ETL = ETLHandler.ETLHandler(config_path)
    
    assert ETL.mongo_handler != None
    assert ETL.sql_handler != None

@pytest.mark.unittest
def test_last_mongo_id_pulled(config_path, config_name):
    """ makes sure nothing is pulled after a previous pull"""

    ETL = ETLHandler.ETLHandler(config_path)
    ETL.config_handler.config['data']['last_mongo_id_pulled'] = ""

    # pull collection
    ETL.get_from_mongo()
    id_save = ETL.config_handler.config['data']['last_mongo_id_pulled']

    # assert the last_mongo_id_pulled is not blank after pull
    assert ETL.config_handler.config['data']['last_mongo_id_pulled'] != ""

    # assert package length matches the collection size
    assert len(ETL.package_queue[0].data) > 0

    # perform second pull
    ETL.get_from_mongo()

    # assert that last_mongo_id_pulled is the same as previous pull
    assert id_save == ETL.config_handler.config['data']['last_mongo_id_pulled']

    # assert that no packages were pulled
    assert ETL.package_queue == []


@pytest.mark.unittest
def test_push_to_sql(config_path, config_name):
    """ verifies that a successful push will return true """

    ETL = ETLHandler.ETLHandler(config_path)

    # pull data from mongo
    ETL.get_from_mongo()

    # attempt to push to sql and check its return value is True
    push_return = ETL.push_to_sql()

    assert push_return == True
    
