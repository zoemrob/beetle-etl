"""
Settings for pytest

TO RUN:
    1. cd to tests folder and run
    
    > pytest -v -m <suite> --config_path="path_to_config" --config_name="VALID"

    <suite> -- unittest
    <suite> -- functest
"""

import pytest


def pytest_addoption(parser):
    parser.addoption("--config_path", action="append", default=[],
        help="path to config file to use")
    
    parser.addoption("--config_name", action="append", default=[],
        help="title for the config (i.e. valid, empty, invalid)")

def pytest_generate_tests(metafunc):
    if 'config_path' in metafunc.fixturenames:
        metafunc.parametrize(
            "config_path", 
            metafunc.config.getoption('config_path'),
            ids=["CONFIG"]
            )

    if 'config_name' in metafunc.fixturenames:
        metafunc.parametrize(
            "config_name", 
            metafunc.config.getoption('config_name')
            )