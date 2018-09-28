"""
Contains all tests related to the SQLHandler

NOTE: all tests must be functions with names defined using
    the following format:

    def test_XXXXX():
    
"""

from BeetleETL.Handlers import SQLHandler
from BeetleETL.Handlers import ConfigHandler
from BeetleETL.Handlers import Package
import pyodbc
import logging
import pytest


@pytest.mark.unittest
def test_setup_connection(config_path, config_name):
    """ assert that a valid sqlhandler object is not none upon setup"""
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    SQLObj = SQLHandler.SQLHandler(ConfigObj.config)
    SQLObj.setup_connection()
    assert SQLObj != None


@pytest.mark.unittest
def test_push_package(config_path, config_name):
    """ test that a small valid package will insert to a sql database 
        and the function will return true if successful
    """
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    SQLObj = SQLHandler.SQLHandler(ConfigObj.config)
    SQLObj.setup_connection()
    # setup simple package with data to push to a valid table 
    dest = {"schema": "dbo", "db": "Sandbox1", "table": "zips.unittest"}            
    PkgObj = Package.Package(dest, ["c1", "c2", "c3"], [None,None,None])
    PkgObj.data = [[1,2,3], [4,5,6], [7,8,9]]

    # assert the assumed valid package inserts to sql and the function returns true
    assert SQLObj.push_package(PkgObj) == True
    SQLObj.cleanup()

@pytest.mark.unittest
def test_generate_sql_update(config_path, config_name):
    """ verify that an expected string is returned from the function """

    # expected output string
    expectedReturnTuple = ("UPDATE [Sandbox1].[dbo].[unittest] SET  [type] = ?, [color] = ? WHERE  [id] = ? AND [number] = ?", ['Ostrich','Mustang brown','54323fhwa',54])

    # sql_dest to test
    dest = "[Sandbox1].[dbo].[unittest]"
    primaryKeys = ['id', 'number']
    columns = ['id', 'type', 'number', 'color']
    values = ['54323fhwa', 'Ostrich', 54, 'Mustang brown']

    # setup objects
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    SQLObj = SQLHandler.SQLHandler(ConfigObj.config)

    # check that the expected value is returned
    assert expectedReturnTuple == SQLObj.generate_sql_update(dest, primaryKeys, columns, values)
    

@pytest.mark.unittest
def test_push_packages(config_path, config_name):
    """ verify that pushing multiple valid packages returns true """
    
    # setup objects
    ConfigObj = ConfigHandler.ConfigHandler(config_path)
    SQLObj = SQLHandler.SQLHandler(ConfigObj.config)
    SQLObj.setup_connection()

    # setup simple packages with data to push to a valid table 
    dest = {"schema": "dbo", "db": "Sandbox1", "table": "zips.unittest"}            
    PkgObj1 = Package.Package(dest, ["c1", "c2", "c3"], [None,None,None])
    PkgObj1.data = [[1,2,3], [4,5,6], [7,8,9]]

    dest = {"schema": "dbo", "db": "Sandbox1", "table": "zips.unittest"}            
    PkgObj2 = Package.Package(dest, ["c1", "c2", "c3"], [None,None,None])
    PkgObj2.data = [[1,2,3], [4,5,6], [7,8,9]]

    pkg_list = [PkgObj1, PkgObj2]

    # assert pushing multiple valid packages returns true
    assert SQLObj.push_packages(pkg_list) == True