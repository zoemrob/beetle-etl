#!/usr/bin/env python
"""
Script to build all the executables

USE:
    > python builder.py
"""

import sys
import os
import subprocess as sp
from BeetleETL import __version__ as BV

# run main function only when script is called as a program rather then a module 
if __name__ == '__main__':
    
    # get current version of build
    vers = BV
    print(BV)
    # choose name of export
    nm = "beetle"


    # OUTPUT NAMES: build export file strings (name of file)
    wincmd_i = "{}_{}.py".format(nm, "wincmd")
    win_i    = "{}_{}.py".format(nm,"win")
    linux_i  = "{}_{}.py".format(nm,"linux")
    osx_i    = "{}_{}.py".format(nm,"osx")
    osxcmd_i = "{}_{}.py".format(nm,"osxcmd")
    cli_i    = "{}_{}.py".format(nm,"cli")

    # OUTPUT NAMES: build export file strings (name of file)
    wincmd_o = "{}_{}_{}".format(nm, "wincmd", vers)
    win_o    = "{}_{}_{}".format(nm,"win",vers)
    linux_o  = "{}_{}_{}".format(nm,"linux",vers)
    osx_o    = "{}_{}_{}".format(nm,"osx",vers)
    osxcmd_o = "{}_{}_{}".format(nm,"osxcmd", vers)
    cli_o    = "{}_{}_{}".format(nm,"cli",vers)

    
    sp.run(["pyinstaller",  "-F", "--onefile", win_i, "--name", win_o])
    sp.run(["pyinstaller", "-F", "--console", "--onefile", wincmd_i, "--name", wincmd_o])
    #sp.run(["pyinstaller", "--console", "--onefile", linux])
    #sp.run(["pyinstaller", "--onefile", cli])




