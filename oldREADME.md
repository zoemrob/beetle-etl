# Beetle
A python package for pulling/pushing data to/from a document store database (i.e. MongoDB) and transforming that data to a relational database (i.e. SQL Server).

*last update: 9/18/2018 by robby boney*

# Topics
- [Install And Setup](#install-and-setup)
    - [Download or Install](#download-or-install)
    - [Downloads](#downloads)
    - [Python Package](#python-package)
        - [Install dependencies](#install-dependencies)
        - [Installing Beetle Locally](#installing-beetle-locally)
- [Use Beetle Executable](#use-beetle-executable)
- [Beetle Config](#beetle-config)
    - [Minimal Setup](#minimal-setup)
- [Mapping Explained](#mapping-explained)
    - [Mapping Rules](#mapping-rules)
    - [Mapping Example](#mappings-example)
    - [Unique case 1](#case-1-non-matching-lengths)
    - [Unique case 2](#case-2-nested-listall)
    - [Unique case 3](#case-3-lists-of-lists)
- [All Optional Parameters](#all-optional-parameters)
- [Use Beetle As A Python Package](#use-beetle-python-package)
    1. [The Python Script](#the-python-script)
    2. [Run The Script](#run-the-script)
- [Emailing Notifications](#emailing-notifications)
- [SQL Error Handling](#sql-error-handling)
- [Interject Integration](#interject-integration)
- [Logging](#logging)
- [Secure Authentication](#secure-authentication)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)


# Install And Setup
## Download or Install
Beetle comes in three primary forms: a standalone executable, a command line script or installable pythone package. Executables are bundled with pyinstaller and therefore do not require any installation other then download.

## Downloads
**Current Release**

|Release | Version | Posted | Platform | Notes |
|--------|---------|--------|----------|-------|
|[win](https://drive.google.com/open?id=16OuBfz5EVOvkpoxq9gXZvYJWAGeUDqEJ) | 1.0.5 | 9-18-2018 | windows| - |
|[wincmd](https://drive.google.com/open?id=1_JM2YPQo-bqgd1evT776zy4FxKOnJgJG) | 1.0.5 | 9-18-2018 | windows| - |
|[linux](https://drive.google.com/open?id=1ZWIG1mm0AWDB6b1BxcXdcws8UQmakF2v) | 1.0.0 | 6-8-2018 | linux | runs as cli binary |
 
 \
**Previous Releases**

|Release | Version | Posted | Platform | Notes |
|--------|---------|--------|----------|-------|
|[win](https://drive.google.com/open?id=1c0VIstj7AKfQylIQbI8cKvOcCgtXkQyQ) | 1.0.0 | 6-7-2018 | windows| - |
|[wincmd](https://drive.google.com/open?id=14F680US8CYuWLv_EUY2EDs5nqybaGaDs) | 1.0.0 | 6-29-2018 | windows| - |
 
 \
**NOTES**: 
- All executables with `cmd` in the name, will display a console window when run that will display imediate runtime results to user, whereas other executables will not.
- `useSecureAuthentication` should not be used with executables lacking a console.

## Python Package 
If you want to install Beetle as a python package the following steps must be followed.


### Install dependencies
The first step is to ensure the right packages are installed either with pip, anaconda or another python module environment manager. These include:

- python >= 3.0
- pymongo >= 3.6.0
- pyodbc  >= 4.0.23
- pandas >= 0.20.0


### Basic Beetle Install

``` 
pip install BeetleETL
```

For more information, see our PyPi Page (https://pypi.org/project/BeetleETL/).


### Installing Beetle From Gitlab

1. clone the repo

    ``` git clone repo_path```

2. install the python package locally

    ``` pip install -e .``` (for developper mode)

    ``` pip install .``` (for standard mode)

3. The python package can now be imported using:
    
    ```python
    from BeetleETL.Handlers import ETLHandler
    ```

# Use Beetle Executable
The executable program only requires that a folder named `beetle_configs` be in the same folder as the executable. This folder can contain multiple config files, each with different parameters. The executable will attempt to run Beetle on any config file which does not contain the field `"useConfig" : false`. All output will be written to a file, `ETLActivity.log`.


# Beetle Config

The config file contains all the parameters needed for the program to run. These include:
- Config Info
- Mongo/SQL Server connection Info
- Daemon/WindowsService Info
- Email Notification Info
- Mapping Schema (what data to pull from mongo and where to send it in SQL)
- Stat info, such as last pulled mongo objectid

## Minimal Setup
Below is an example config file with the minimal required parameters. The Beetle Config uses the JSON file format; more information about [JSON can be found here](https://www.json.org/).

```json
{
    "useSecureAuthentication" : false,
    "connectionInfo" : {
        "useWindowsAuth" : false,
        "sqlServerDriver": "ODBC Driver 13 for SQL Server",
        "sqlServerHost" : "",
        "sqlServerUser" : "",
        "sqlServerPass" : "",
        "sqlServerPort" : "",
        "sqlServerDatabase" : "",
        "useMongoURISRV" : false,
        "mongoServerHost" : "",
        "mongoServerUser" : "",
        "mongoServerPass" : "",
        "mongoServerPort" : "",
        "mongoDatabase" : "",
        "mongoCollection" : ""
    },
    "sqlErrorHandling": {},
    "emailInfo" : {
        "useEmailNotify" : false
    },
    "mapping":[
        {
            "sql_dest" : {
                "db" : "",
                "schema" : "",
                "table" : ""
            },
            "sql_cols" : {
                "_id" : {"mongo_path": "_id"},
                "single_value" : {"mongo_path": "value"},
                "single_value_in_object" : {"mongo_path": "obj.value"},
                "list_value" : {"mongo_path": "obj.list[0]"},
                "all_values_in_list" : {"mongo_path" : "obj[all].value1"}
            }
        }
    ]
}
```
Details on optional parameters can be found in the following section.

In addition to this minimal config setup it should be noted that any additional parameters 
for personal organization needed can be add to this file. For example to keep track of various versions of config files the following could be added: `"version" : "1.0.0"`.


# Mapping Explained

We will now explain how to effectively use the mapping in the config file to build a query from a mongo collection
with a set destination in a SQL Server database.

```json
"mapping":[
    {
        "sql_dest" : {
            "db" : "",
            "schema" : "",
            "table" : ""
        },
        "sql_cols" : {
            "_id" : {"mongo_path": "_id"},
            "single_value" : {"mongo_path": "value"},
            "single_value_in_obj" : {"mongo_path": "obj.value"},
            "list_value" : {"mongo_path": "obj.list[0]"},
            "all_values_in_list" : {"mongo_path" : "obj[all].value1"}
        }
    }
] 
```

## Mapping Rules
The high level details of the mapping object are as follows:
- `"mapping"` is a list of objects
- each object in the list should have: 
    - a `"sql_dest"` object with information for the sql table destination
        - db = the name of the database you are wanting to insert into
        - schema = the name of the schema you are wanting to insert into
        - table = the name of the table you are wanting to insert into
    - a `"sql_cols"` object with each sql column name and mongo data path
        - keys = SQL table column names
        - value = object with the required `"mongo_path"` string where a single data point resides
- `"mongo_path"` can follow various formats:
    - `"value"` = when a single value is desired from the document
    - `"obj.value"` = when a single value is desired from an object
    - `"obj.list[INDEX]"` = when a single value is desired which is nested in a list
    - `"obj.list[all]"` = when all values in a list are desired
    - `"obj.list[all].value"` = when all values from a object in a list are desired
- any time `"list[all]"` is specified multiple records will be made
    - when a single value and list are specified in the same map, the single value is duplicated through each record ([see below](#Mapping-Example))
    - when multiple `"list[all]"` are used in 1 map, NULLs will be added to any list which does not match the length of the longest list ([Unique case 1](#Case-1:-Non-Matching-Lengths))

Below is an example mongo document, a corresponding map and the result output.

## Mapping Example

Document From Mongo Collection, __People__
```json
{
    "_id" : "asj128s73h2g2j",
    "name" : "joe fro",
    "friends" : [ 
        {"name":"arny", "years_known":5},
        {"name":"lisa", "years_known":2},
        {"name":"regy", "years_known":1}
    ],
    "parents" : ["mary fro", "danny fro"] 
}
``` 

Mapping
```json
"mapping":[
    {
        "sql_dest" : {
            "db" : "demodb",
            "schema" : "dbo",
            "table" : "people"
        },
        "sql_cols" : {
            "id" : {"mongo_path": "_id"},
            "name" : {"mongo_path": "name"},
            "mother" : {"mongo_path" : "parents[0]"},
            "father" : {"mongo_path" : "parents[1]"}
        }
    },
    {
        "sql_dest" : {
            "db" : "demodb ",
            "schema" : "dbo",
            "table" : "friends"
        },
        "sql_cols" : {
            "id" : {"mongo_path": "_id"},
            "name" : {"mongo_path": "friends[all].name"},
            "years_known" : {"mongo_path": "friends[all].years_known"}
        }
    }
] 
```

Resulting Records to insert into SQL
```
       TABLE = demodb.dbo.[people]
COLUMN NAMES = (id             , name     , mother    , father     )
    RECORD 1 = ("asj128s73h2g2", "joe fro", "mary fro", "danny fro")

       TABLE = demodb.dbo.[friends]
COLUMN NAMES = (id             , name     , years_known)
    RECORD 1 = ("asj128s73h2g2", "arny"   , 5          )
    RECORD 2 = ("asj128s73h2g2", "lisa"   , 2          )
    RECORD 3 = ("asj128s73h2g2", "regy"   , 1          )
```

## Unique Mapping Cases
Here we show how the mapping will work in more unique examples. 

### Case 1: Non-Matching Lengths
If multiple `"List[all]"` are specified, which end up having different lengths the program will fill in `Nulls` for the empty data. Using the original __People__ collection example, we can see that combining the parents list and the friends list will result in parents recieving a `Null` for record 3. 

Mapping
```json
"mapping":[
    {
        "sql_dest" : {
            "db" : "demodb",
            "schema" : "dbo",
            "table" : "example"
        },
        "sql_cols" : {
            "id" : {"mongo_path": "_id"},
            "name" : {"mongo_path": "name"},
            "parents" : {"mongo_path" : "parents[all]"},
            "friend_names" : {"mongo_path" : "friends[all].name"}
        }
    }
]
```

Resulting Records to insert into SQL
```
       TABLE = demodb.dbo.[example]
COLUMN NAMES = (id             , name     , parents    , friend_names)
    RECORD 1 = ("asj128s73h2g2", "joe fro", "mary fro" , "arny"      )
    RECORD 2 = ("asj128s73h2g2", "joe fro", "danny fro", "lisa"      )
    RECORD 3 = ("asj128s73h2g2", "joe fro", NULL       , "regy"      )
```

### Case 2: Nested `List[all]`
It is completely possible to pull data from a list within a list. Situations like this will result in **SUM (Each List Length's)** number of records being made. For example if we create a new mongo document in a collection called **FamilyTrees** we can see how a nested `List[all]` will result in a larger number of records.

Document From Mongo Collection, __FamilyTrees__ 
```json
{
    "_id" : "asj128s73h2g2j",
    "surname" : "Jackson",
    "parents" : [
        {"name" : "john", "children" :[
            "joe", "beth", "arny"
        ]},
        {"name" : "suzy", "children" :[
            "jack", "john"
        ]},
        {"name" : "suzy", "children" :[
            "mary", "ruth", "connie"
        ]}
    ]
}
``` 

Mapping
```json
"mapping":[
    {
        "sql_dest" : {
            "db" : "demodb",
            "schema" : "dbo",
            "table" : "example"
        },
        "sql_cols" : {
            "id" : {"mongo_path": "_id"},
            "surname" : {"mongo_path": "surname"},
            "grandkids" : {"mongo_path" : "parents[all].children[all]"},
        }
    }
]
```

Resulting Records to insert into SQL
```
       TABLE = demodb.dbo.[example]
COLUMN NAMES = (id              , surname  , grandkids )
    RECORD 1 = ("asj128s73h2g2j", "Jackson", "joe"     )
    RECORD 2 = ("asj128s73h2g2j", "Jackson", "beth"    )
    RECORD 3 = ("asj128s73h2g2j", "Jackson", "arny"    )
    RECORD 4 = ("asj128s73h2g2j", "Jackson", "jack"    )
    RECORD 5 = ("asj128s73h2g2j", "Jackson", "john"    )
    RECORD 6 = ("asj128s73h2g2j", "Jackson", "mary"    )
    RECORD 7 = ("asj128s73h2g2j", "Jackson", "ruth"    )
    RECORD 8 = ("asj128s73h2g2j", "Jackson", "connie"  )
```


### Case 3: Lists of Lists
Nested lists are also valid and can be parsed in the following manner.

Document From Mongo Collection, __Expenses__ 
```json
{
    "_id" : "asj128s73h2g2j",
    "monthly_expenses" : [
        [900, 20],
        [900],
        [900, 70, 24]
    ]
}
``` 

Mapping
```json
"mapping":[
    {
        "sql_dest" : {
            "db" : "demodb",
            "schema" : "dbo",
            "table" : "example"
        },
        "sql_cols" : {
            "id" : {"mongo_path": "_id"},
            "expenses" : {"mongo_path" : "monthly_expenses[all][all]"},
        }
    }
]
```

Resulting Records to insert into SQL
```
       TABLE = demodb.dbo.[example]
COLUMN NAMES = (id              , expenses )
    RECORD 1 = ("asj128s73h2g2j", 900)
    RECORD 2 = ("asj128s73h2g2j", 20)
    RECORD 3 = ("asj128s73h2g2j", 900)
    RECORD 4 = ("asj128s73h2g2j", 900)
    RECORD 5 = ("asj128s73h2g2j", 70)
    RECORD 6 = ("asj128s73h2g2j", 24)
```


# All Optional Parameters
Below is an example config file with the minimal required parameters.

### Root Options
|Param | Type | Required | Options | Description |
|------|------|----------|---------|----------|
| useConfig | bool |  | true, false | tells an executable to skip this config if false |
| process | string | cli | manual, daemon | tells the linux client to run manually or as a daemon|
| TriggerFrequencyHrs | int |if process is not manual| [integer]| how often to run daemon process|
| useSecureAuthentication | bool | cli, exe | true, false | prompts the user for passwords at runtime (should be set to true only with `cmd` exe's)|


### ConnectionInfo Options
|Param | Type | Required | Options | Description |
|------|------|----------|---------|----------|
|useWindowsAuth |bool |cli, exe |true, false |Use windows authentication when connecting to SQL Server |
|sqlServerDriver |string |cli, exe | |the SQL Server driver to use (i.e. 'ODBC Driver 13 for SQL Server') |
|sqlServerHost |string | | |the SQL Server host to use |
|sqlServerPort |string or int | |"", [number] |optional parameter for host port |
|sqlServerUser |string |cli, exe | |user to login as to SQL Server host |
|sqlServerPass |string | | |password for user login |
|sqlServerDatabase |string |cli, exe | |the SQL Server database to connect to |
|mongoServerHost |string |cli, exe | |the mongodb host to use |
|mongoServerPort |string |cli, exe | |mongodb port for the host (NOTE: srv URI's do not use port) |
|mongoServerUser |string |cli, exe | |mongodb username for host |
|mongoServerPass |string | | |mongodb passwrod for username |
|mongoDatabase |string |cli, exe | |mongodb database to parse from |
|mongoCollection |string |cli, exe | |mongodb collection to parse from |
|[useMongoURISRV](https://docs.mongodb.com/manual/reference/connection-string/#dns-seedlist-connection-format) |bool |cli, exe |true, false |leverage DNS-seedlist to find available servers |
|customMongoURI |string | | "", [string] |custom mongo uri to connection to which allows conenction to replica set or sharded cluster |
|useMongoSSL |bool |cli, exe |true, false |explicitly tells mongo to initiate connection with TLS/SSL (if not specified defaults to true) |



### emailInfo Options
NOTE: all fields in emailInfo are only required if `"useEmailNotify" : true`

|Param | Type | Required | Options | Description |
|------|------|----------|---------|----------|
|useEmailNotify |bool |cli, exe |true, false | tells the program to send the recently added log elements to an email |
|fromEmail |string | | |Email to send the notification from |
|fromPass |string | | |Password for fromEmail to send the notification from |
|toEmail |list of strings | | |Emails to send to |
|subject |string | | |Subject to use in the email header |
|smtpHost |string | | |host for smtp server |
|smtpPort |string | | |option parameter for host port |

### mapping Options
|Param | Type | Required | Options | Description |
|------|------|----------|---------|----------|
|sql_dest |object |cli, exe | |specifies what schema, database and table the mapping will send data to |
|sql_dest.schema |string | | |the SQL Server scheme |
|sql_dest.db |string | | |the SQL Server database |
|sql_dest.table |string | | |the SQL Server table |
|sql_cols.[obj].mongo_path |string |for every object in sql_cols | |specifies where in the mongo collection data should be pulled from |
|sql_cols.[obj].target_type |string | |bool, string, int |Specifies how the program should cast the data from mongo |
|sql_cols.[obj].allowMongoUpdate |bool | |true, false |Specifies if the column should be included in Interject Saves |
|sql_cols.[obj].mongoUpdateType |string | |bool, str, int, float |Specifies explicit type to cast to when inserting to mongo |
|sql_cols[obj].required |bool | | true, false |if no data is found at this objects mongo_path then no packages are created|
|sql_cols[obj].static_val |str | | |sets a static string value to the column for each pull|

### data Options
|Param | Type | Required | Options | Description |
|------|------|----------|---------|----------|
|data.pullOnlyNew |bool | | true, false |if true, will only pull documents more recent then the current ObjectId, if false will record the latest ObjectId but will pull all documents everytime|

# Use Beetle Python Package
The package requires the Beetle package be installed and a client script and config be setup (previously described)


### THE PYTHON SCRIPT
    
The following python code is the minimal client script needed to import the module,
setup the ETLHandler with a custom configuration file, and then use the ETLHandler to
pull from a mongo database and push the data to a SQL Server database.


``` python
from BeetleETL.Handlers import ETLHandler

ETL = ETLHandler.ETLHandler("custom_config.json")

ETL.get_from_mongo()
ETL.push_to_sql()
```


### RUN THE SCRIPT

Now that all the files necessary is setup, we can run the python script and pull our data from mongo and push it to sql using the following command:

- Linux/MacOS
    
    ```bash
    ~$ python script.py
    ```

    or

    ```bash
    ~$ chmod +x script.py
    ~$ ./script.py
    ```

- Windows

    ```cmd
    C:\> python script.py
    ```

# SQL Error Handling
The Beetle program allows the ability for users to define how they want to handle SQL errors encountered while inserting. To define handling of an error add a new element to the sqlErrorHandling section of the config. The name of the new element is a string that is found in the error your wanting to handle and the value is how you want to handle it (update, skip, or break) example below:
```json
    "sqlErrorHandling": {
        "Violation of PRIMARY KEY constraint": "update",
        "Cannot insert the value NULL": "skip"
    }
```
The above example will update a row when it encounters an error that includes the string "Violation of PRIMARY KEY constraint" and will skip inserting a row when it encounters an error that includes the string "Cannot insert the value NULL".

|Option | Function |
|------|------|
|update |will update the row with the new data from mongo. |
|skip |will skip modifying the row. |
|break |will stop the program and rollback all insertions. |

# Logging
The Beetle package logs all actions of the application to a file in the directory where the script is launched
called `ETLactivity.log`. This file contains execution runtime for each map specified in mapping which can be useful for identifying which maps are taking the longest to pull/transform from Mongo as well as insert to SQL Server.

# Emailing Notifications
In addition to logging, email notifications can be setup to send the most recently added content from the log file to a list of emails. This can be done by first adding the following to the config file:

```json
"emailInfo" : {
    "useEmailNotify" : true,
    "smtpHost" : "smtp.gmail.com",
    "smtpPort" : 587,
    "Subject" : "Beetle Update",
    "fromEmail" : "",
    "fromPass" : "",
    "toEmail" : []
}
```

Now all we need to do is include a single line `ETL.send_email_update()` to our client python script in order to get the current log for this execution at that point in the program.

``` python
from BeetleETL.Handlers import ETLHandler

ETL = ETLHandler.ETLHandler("custom_config.json")

ETL.get_from_mongo()
ETL.push_to_sql()
ETL.send_email_update()
```

If you do not wish to use email notifications, simply set `"useEmailNotify" : false` , or do not call `send_email_updates()`

while custom smtpHost and smtpPort can be used, a simple example is to use a gmail with the above specifications and then make sure the `fromEmail` does not have 2-factor authentication activated on gmail settings.

An error may occur where the `fromEmail` recieves a email stating `Less Secure Apps Not Enabled`. In this case, simply 
follow the link in the email to enable Less Secure Apps and retry running the program, a notification with log information
should be sent to the `toEmail` list of emails.

# Secure Authentication
There may be occations when you do not want to store passwords inside a configuration file (i.e. if many users would have access to the configuration file). In scenarios like this it is possible to prompt the user launching the program to input their passwords which will then be used for the program execution, by setting `useSecureAuthentication` to true.

```json
"useSecureAuthentication" : true
```

# Testing
Beetle comes with the ability to run a suite of function tests on a provided config file, which can be helpful for identifying if the setup is properly configured to be executed for production. the tests are run using pytest which can be installed via the instructions on the developper documentation, [Installation and Getting Started](https://docs.pytest.org/en/latest/getting-started.html). 

Beetle is configured to run tests on a provided config file which can be done using the following commands:

```
# cd to Beetle-ETL/Beetle_Src/

# run command
> pytest -v --config_path="<path to config>" --config_name="<name for config>"
```

config_path should be a valid path to config file to test

config_name is a string identifier which pytest will use to print out what tests pass and fail which makes it easy to identify the input parameters of the test run.

# Troubleshooting
Common issues or questions which may arise may include:

- **Cannot connect to my Mongo Database**
    
    Our program utilizes Mongo's URI schema for connecting to a database. It is important to know if your database
    requires a DNS seedlist conenction. If so the parameter should be `"useMongoURISRV" : true` in the configuration file. (More information about Mongo URI schemas can be found [here](https://docs.mongodb.com/manual/reference/connection-string/) )

- **Running the program takes a long time to pull from Mongo and insert to SQL**

    This is most likely do to the following reasons:

    - *The Mongo Database being pulled from is very large*
    - *The Daemon update frequency is set to very large interval*
