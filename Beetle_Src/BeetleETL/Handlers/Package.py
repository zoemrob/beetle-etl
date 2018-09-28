"""
Manages any data pulled from a database with intention of inserting
it into another destination database.
"""

class Package():
    """ class to manage all recoreds destined for one sql table

    """

    def __init__(self, dest="", c_names=[], dest_types=[]):
        self.data = []                  # list of lists containing col data
        self.dest = dest                # target destination information for package
        self.setup_runtime = 0          # amount of time spent by mongohandler building this package
        self.col_names = c_names        # list of column names from config map
        self.dest_types = dest_types    # sql or mongo (our case it will always be sql)
        self.cardinality = 0            # number of column names (needed to validate insertions)

    def insert_data(self, row):
        """ insert a list of data into package data list
        """
        # need to check that cardinality of row matches data
        if len(row) != self.cardinality:
            
            print("ERROR: invalid cardinality for row")
            print(" * column names = {}".format(self.col_names))
            print(" *     row data = {}".format(row))
            return False
        else:
            self.data.append(row)
            return True
    
    def set_cardinality(self):
        """ sets the cardinality to the length of the col_names """
        self.cardinality = len(self.col_names)
