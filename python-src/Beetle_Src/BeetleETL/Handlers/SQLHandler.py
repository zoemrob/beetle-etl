"""
Manages all sql server connection and query operations
"""
import pyodbc
import logging
import time
class SQLHandler():
    """
    """

    def __init__(self, config):
        self.config = config
        self.connection = None
        self.cursor = None

    def setup_connection(self):
        """ Sets up a new connection to a sql server database
        """
        logging.info('Attempting to establish connection to SQL database: {}'.format(self.config['connectionInfo']['sqlServerDatabase']))
        
        #If there is no sqlDriver specified to use, get the current
        #list of available drivers and use the newest one
        if self.config['connectionInfo']['sqlServerDriver'] == "":
            driversArray = pyodbc.drivers()
            if len(driversArray) < 1:
                logging.error("Could not connect to SQL server no SQL drivers detected")
                return None
            self.config['connectionInfo']['sqlServerDriver'] = driversArray[-1]

        #If Windows authentication is enabled set up a connection
        #based on the config file (without using credentials)
        if self.config['connectionInfo']['useWindowsAuth']:
            try:
                self.connection = pyodbc.connect('Driver={'+self.config['connectionInfo']['sqlServerDriver']+'};\
                                            Server='+self.config['connectionInfo']['sqlServerHost']+\
                                            ';Database='+self.config['connectionInfo']['sqlServerDatabase']+\
                                            ';Trusted_Connection=yes;')
                self.cursor = self.connection.cursor()
            except Exception as err:
                logging.error("Could not connect to SQL server using windows authentication: {}".format(err))
                return None
        #If windows authentication is disabled use credentials
        else:
            try:
                self.connection = pyodbc.connect('DRIVER={'+self.config['connectionInfo']['sqlServerDriver']+'};\
                                                SERVER='+str(self.config['connectionInfo']['sqlServerHost'])+';\
                                                DATABASE='+str(self.config['connectionInfo']['sqlServerDatabase'])+';\
                                                UID='+str(self.config['connectionInfo']['sqlServerUser'])+';\
                                                PWD='+str(self.config['connectionInfo']['sqlServerPass']))
                self.cursor = self.connection.cursor()
            except Exception as err:
                logging.error("Could not connect to SQL server using login credentials: {}".format(err))
                return None
        logging.info("Connection to SQL database established")

    

    def push_package(self, pkg):
        """ insert a single pkg to the database
            Arguments:
                pkg {class} -- Package object creating while collecting mongoDB data
        """
        columnNames = pkg.col_names
        columnInsertString ="],[".join(columnNames)
        columnInsertString = '[' + columnInsertString + ']'
        
        destinationTable = '['+ pkg.dest['db'] + '].[' + pkg.dest['schema'] + '].[' + pkg.dest['table'] + ']'
        value = ['?'] * len(pkg.col_names)
        value = ",".join(value)

        ErrorCount = 0
        skipCount = 0
        updateCount = 0
        print("INSERTING INTO {} ({}) VALUES ({})".format(destinationTable, columnInsertString, value))
        primaryKeys = []
        
        #Collects the primary keys from the statistics table
        for row in (self.cursor.primaryKeys(pkg.dest['table'], catalog = pkg.dest['db'], schema = pkg.dest['schema'])):   
            primaryKeys += [row[3]] 

        for i in pkg.data:
            try:
                self.cursor.execute("""
                                    INSERT INTO {} 
                                    ({}) VALUES ({})
                                    """.format(destinationTable, columnInsertString, value), i)
            except Exception as err:
                errorHandled = False
                ErrorCount+=1
                for key , val in self.config['sqlErrorHandling'].items():
                    if key in str(err):
                        if val == "skip":
                            skipCount+=1
                            errorHandled = True
                            break

                        elif val == "update":
                            updateCount+=1 

                            #Getting the update string
                            updateString, updateValues = self.generate_sql_update(destinationTable,primaryKeys,columnNames,i)
                            try:
                                self.cursor.execute(updateString,updateValues)
                            except Exception as err:
                                logging.error(" -> Error when updating SQL row for destination {}: {}".format(destinationTable,err))   
                                return None
                            errorHandled = True
                            break
                        else: 
                            break

                if errorHandled == False:
                    logging.error(" -> Error when inserting data into SQL for destination {}: {}".format(destinationTable,err))
                    logging.error(" -> Total insertion errors for destination {}: {}".format(destinationTable,ErrorCount))
                    return None
        
        if ErrorCount > 0:
            logging.warning(" -> Total Handled insertion errors for destination {}: {}".format(destinationTable,ErrorCount)) 
            if skipCount > 0:
                logging.warning(" -> Total skipped insertions for destination {}: {}".format(destinationTable,skipCount))
            else:
                logging.warning(" -> Total updated rows for destination {}: {}".format(destinationTable,updateCount))    
        return True

    def generate_sql_update(self, destinationName, primaryKeys, columnNames, columnValues):
        """ generates a sql update statement string for a single row
            Arguments:
                tableName {str}             -- Name of the table that is being inserted into
                primaryKeys {list}                  -- List of pk names
                columnNames {tuple}         -- list of column names for insertion
                columnValues {tuple}        -- list of column values for insertion
            Returns:
                finalUpdateString {tuple}   -- [0] contains the update string [1] contains the values to insert
        """

        columnValues                = list(columnValues)            #Converting columnValues from tuple to list
        columnNames                 = list(columnNames)
        pkValues                    = []                            #pkValue array for seperating the columnValues and pkValues
        primaryKeysInsertString     = ""
        columnUpdateString          = ""

        currentKey = 0
        while(currentKey < len(primaryKeys)):                               #looping through primary keys
            currentColumn = 0
            while(currentColumn < len(columnNames)):                #for each primary key loop through columns
                if columnNames[currentColumn] == primaryKeys[currentKey]:   #if the pk matches the column
                    primaryKeysInsertString +=""" AND [{}] = ?""".format(columnNames[currentColumn])
                    pkValues+=[columnValues[currentColumn]]         #add it to the insertion string and store its value
                    columnValues.remove(columnValues[currentColumn])#Then remove it from both lists to prevent it from being in
                    columnNames.remove(columnNames[currentColumn])  #the update clause.
                    currentColumn-=1
                currentColumn += 1
            currentKey +=1
        
        for column in columnNames:                                  #Add all columns that are left to colUpdate string
            columnUpdateString += ', [{}] = ?'.format(column) 

        primaryKeysInsertString = primaryKeysInsertString[4:]       #Removing leading AND
        columnUpdateString      = columnUpdateString[1:]            #Remove leading comma
        columnValues            += pkValues                         #appending pk values to end of colValues to prevent injection
        finalUpdateString       = ("""UPDATE {} SET {} WHERE {}""".format(destinationName,columnUpdateString,primaryKeysInsertString), columnValues)
        return finalUpdateString

        


    def push_packages(self, pkg_list):
        """ uses push_package to insert multiple packages to the sql database
            Arguments:
                pkg_list {list} -- list of package objects
        """
        pushStatus = None
        successfullInserts = 0
        self.setup_connection()
        logging.info("Begining to insert {} package(s) into SQL database".format(len(pkg_list)))
        for pkg in pkg_list:
            timeStart = time.clock()
            pushStatus = self.push_package(pkg)
            timeEnd = time.clock()
            elapsedTime = timeEnd - timeStart
            if pushStatus == None:
                break
            else:
                logging.info("  -> Successfully inserted package for {} in {} seconds".format(pkg.dest,elapsedTime))
                successfullInserts += 1
        
        if pushStatus == None:                                      #If one of the packages failed to insert
            logging.error(" -> Rolling back all insertions")        #close the cursor without commiting
            self.cursor.close()
            self.cleanup
            return False
        else:    
            self.connection.commit()                                #Else if the all packages inserted successfully commit
            self.cursor.close()
            logging.info("{}/{} package(s) inserted successfully".format(successfullInserts, len(pkg_list)))
            self.cleanup()
            return True
    
    def cleanup(self):
        """ closes connections created by the sqlHandler
        """
        self.connection.close()