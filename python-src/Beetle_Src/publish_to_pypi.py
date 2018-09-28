
"""
This script allows the user to push package to pypi

EXAMPLE:
         0                  1
> python publish_to_pypi.py -repo=<OPT1>

OPT1: 
1.    -repo=test
2.    -repo=live
    
"""
TEST_PYPI_INDEX = "https://test.pypi.org/legacy/"
PKG_SITE = "https://pypi.org/project/"

import sys
from subprocess import call

def parse_cmd_args():
    out = {}    # dict of output parameters

    for i in sys.argv:
        if "-repo=" in i:
            try:
                out['repo'] = i.split("=")[1]
                
            except Exception as err:
                print("Error: Could not parse pkg_index")
        
        elif "-dist=" in i:
            try:
                out['dist'] = i.split("=")[1]
            except Exception as err:
                print("Error: Could not parse custom distribution")
    
    # set defaults if user specifies none
    if 'repo' not in out:
        out['repo'] = "live"
    if 'dist' not in out:
        out['dist'] = "*"

    return out
    
def get_pkg_name():
    try:
        with open("setup.py", "r") as fl:
            return fl.read().split("name=")[1].split(",")[0][1:-1]
    except Exception as err:
        print("Error: Could not parse out name from setup.py")

def main():
    """ """
    args = parse_cmd_args()

    # first create the distribution
    print(" * building distribution")
    call( ["python", "setup.py", "sdist", "bdist_wheel"] )
    
    dist = "dist/" + args['dist']

    # upload to pypi
    if args["repo"] == "test":
        call(["twine", "upload", "--repository-url", TEST_PYPI_INDEX, dist])
        site = TEST_PYPI_INDEX + get_pkg_name() + "/"
        print(" * distribution uploaded, visit ({}) to see package".format(site))
    else:
        call(["twine", "upload", dist])
        site = PKG_SITE + get_pkg_name() + "/"
    print(" * distribution uploaded, visit ({}) to see package".format(site))

    

if __name__ == '__main__':
    main()
    