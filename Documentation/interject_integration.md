
# MongoToSQL Interject Integration

MongoToSQL allows for integration with Interject Data Systems to work with data in excel. Specifically pulling, transforming and saving data to/from MongoDB.

# Topics
- [Interject Api and Portal Setup](#interject-api-and-portal-setup)
    - [Api Server Setup](#api-server-setup)
    - [Data Connection Setup](#data-connection-setup)
    - [Data Portal Setup](#data-portal-setup)
- [Interject Pull](#interject-pull)
    - [MongoToSQL Config Setup](#mongotosql-config-setup)
- [Interject Save](#interject-save)
    - [Optional Parameters](#optional-parameters)
- [Custom Functions](#custom-functions)
    - [API Appconfig Setup](#api-appconfig-setup)
    - [Custom Python Function](#custom-python-function)
- [Notes](#notes)

# Interject Api and Portal Setup
To perform a pull or save using Interject, there are a few prior requirements.

- An Interject DataPortal and Data Connection must be created
- An Interject Report must be setup with a pull or save
- The Interject python web api must be downloaded, setup and running 

## Api Server Setup
- To setup the server, the Interject Python Api package should be downloaded and installed using the following command when located in the directory with setup.py.

    ```
    pip install -e .
    ```

- The file example_appconfig.py should be renamed to appconfig.py and a new item should be added to the `CONNECTIONSTRINGS` dictionary for the MongoDB uri.

    ```python
    CONNECTIONSTRINGS = {
        "Mongo_example_db" : "mongo+srv//user:pass@host/database"
    }
    ```

- (OPTIONAL) if theres a custom python script you want to run before a pull or push, a path to a python script should also be added to the appconfig.py. More information on [Custom Functions](#custom-functions) can be found later in this document.

    ```python
    CUSTOM_MODULE = "custom_python_script.py"
    ```


## Data Connection Setup
From the Interject profile page under `My Data / Data Connections`, a new data connection can be created:
- `Name` is arbitrary but required
- `Connection Type` should be set to "Web Api"
- `Api Root Uri` should be set to the url of your python api server
- `Api Connection String Name` should be set to the CONNECTIONSTRING specified in appconfig.py.

## Data Portal Setup
From the Interject profile page under `My Data / Data Portals`, a new data connection can be created:
- `Data Portal Code` is the string to use in the Interject report when setting up a pull
- `Connection` is the name of the data connection previously set up
- `Command Type` should be set to "Stored Procedure Name"
- `Stored Procedure / Command` is the name of the config file to use ( i.e. _example_config.json_ )
- `Api Relative Uri` should be set to "MongoDBRequest"


# Interject Pull
Once the presetup requirments are met, an Interject Pull can be built by including the data portal code in a ReportRange() or similar Interject function for the dataportal variable.

## MongoToSQL Config Setup
In order for MongoToSQL to work with the Interject API, a directory named `mongotosql_configs` should be added to the directory containing the api server. Each config acts as a single pull or save and each map in the config mapping section acts as an individual result set for the pull. Therefore a config designed for a pull should contain the field, `"interjectCommand" : "pull"`.

## Custom Filters
It is possible to use the formula parameters from Interject to add custom defined Mongo filters. This can be done by adding the `"interject_filter" : {"alias_name":"mongo_query_object"}` format to the mongotosql_config. Below is an example which pulls documents where a term (INPUT_VALUE) provided by Interject from an input parameter, is contained in the resulting field in MongoDB.

```json
"interject_filter" : {
    "name" : {"name" : {"$regex":"INPUT_VALUE"}}
}
```

# Interject Save
Setting up an Interject Save is similar to the Pull, with some minor differences.

- **IMPORTANT:** All Saves require that document ObjectId's are pulled under the alias `_id`
- Saves should use the configuration, `"interjectCommand" : "save"`
- The `interject_filter` field does not have any functionality in the save operation
- `allowMongoUpdate` is required to be on every `sql_cols` object to be saved.

## Optional Parameters
The following example demonstrates how the report can be setup to only save certain columns from excel back to MongoDB and convert them to strings upon saving to MongoDB. `allowMongoUpdate` signals that a column should be saved back to MongoDB and `mongoUpdateType` specifies what type to cast the data to when inserting back to MongoDB.

```python
"sql_cols": {
    "key_alias" : {
        "mongo_path" : "mongo.path.to.data",
        "mongoUpdateType" : "str",
        "allowMongoUpdate" : true
    }
}
```

# Custom Functions
MongoToSQL has a special integration with Interject that allows a custom python script to transform the data pulled from MongoDB or excel before it reaches its destination.

## API Appconfig Setup
The Interject api configuration is contained in a appconfig.py file in the same directory as the server script. This file needs a new addition; specifically the `CUSTOM_MODULE` variable. This should be set to a python script in the local directory with the custom function to run.

```python
CUSTOM_MODULE = 'etl'
```

## Custom Python Function
All custom functions recieve data from the Interject API as a pandas dataframe and also input parameters from the excel report. The following example demonstrates how a python script can be used to rename any value pulled equal to `Bronx` to a new value, `Tronx`.

```python
import pandas as pd

def interject_custom_func(**kwargs):
    """ Custom defined function which operates on pulled data from excel
        or a dataportal source before sending the data to its final destination

        NOTE: - kwargs contains keys, (dataframe, input_params)
              - expects return value to be a pandas DataFrame() 
    """
    
    d = {'Bronx':"Tronx"}
    df = kwargs['dataframe'].replace(d)
    return df
```

The Interject api first performs a pull from MongoDB using the MongoToSQL package, then passes the data pulled, as a dataframe to the custom function, which is a good reason to utilize python's kwargs function parameter. The dataframe can then be manipulated and returned, which happens to be the data which is sent to excel.

**NOTE:** when using MongoToSQL with Interject, the `stored procedure / command` field in the dataportal is used to specify which MongoToSQL config to use. Because of this, the python api simply looks for a default custom function called `interject_custom_func()`.


# Notes
- `useSecureAuthentication` should be set to false to avoid hanging on the server
- The following MongoToSQL optional parameters have no effect when used with Interject
    - `emailInfo`
    - `useConfig`
    - `sqlErrorHandling`
    - `process`
    - sql_cols options
        - `target_type`
    