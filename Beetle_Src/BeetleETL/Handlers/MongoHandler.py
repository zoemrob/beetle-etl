"""
Manages all mongodb connection and query operations
"""
import time
import datetime
import xml.etree.ElementTree as etree
from pymongo import MongoClient, errors
from pymongo.collection import ReturnDocument
import pymongo
from BeetleETL.Handlers import Package as PKG
from collections import OrderedDict
from bson.objectid import ObjectId
import logging
import json
import pandas as pd

# parameter types from interject
STRINGS = ["VARCHAR", "VARCHARMAX", "TEXT", "NCHAR", "NTEXT",\
            "NVARCHAR", "NVARCHARMAX", "CHAR"]
NONSTRINGS = ["INT", "BIGINT", "SMALLINT", "SMALLMONEY", "TINYINT", "FLOAT",\
            "MONEY", "DATETIME", "DATE", "SMALLDATETIME", "BIT", "REAL"]

class MongoHandler():
    """ class to handle all interactions with a mongo database, these include
    pulling/pushing data to/from collections and setting up packages for the
    sql handler to work with. 
    """

    def __init__(self, config=""):
        self.config = config
        self.client = None
        self.mongo_filter = {}
        self.last_id_pulled = None

        # setup mongo filter if it exists in the config file
        if "mongoFilter" in self.config:
            filter_dict = {}
            for filter_alias in self.config['mongoFilter']:
                
                # get mongo search query from mongotsql config
                new_query = self.get_mongo_search_query(
                    alias=filter_alias, 
                    input_value=None,
                    cast_to=None
                    )

                # use a deepmerge method to combine the filter dictionary with incoming filter
                # changes (NOTE: this is needed for mongo data embedded in the same object)
                deepmerge_dicts(filter_dict, new_query)

            self.mongo_filter = filter_dict

    def setup_connection(self):
        """ Sets up a new connection to a mongo database
        """
        
        uri = ""

        if 'customMongoURI' in self.config['connectionInfo'] and self.config['connectionInfo']['customMongoURI'] != "":
            uri =  self.config['connectionInfo']['customMongoURI']
            logging.info("using custom mongo uri")
        else:
            uri = self._build_uri()
            logging.info("using assembled mongo uri")
        
        logging.info('Attempting to establish connection to Mongo database')
        try:
            self.client = MongoClient(uri)
            logging.info('Successfully setup client cursor')
            return True
        except errors.InvalidURI as err:
            logging.error('Could not setup mongo client: invalid mongo uri (you may not be using pymongo 3.6, found pymongo {})\n -> {}'.format(pymongo.__version__, err))
            return False
        except Exception as err:
            logging.error('Could not setup mongo client\n -> {}'.format(err))
            return False

    def close_connection(self):
        """ closes a mongodb client connection
        """
        if self.client is not None:
            self.client.close()
            return True
        else:
            logging.warning("Cannot close mongo client: client is None")
            return False

    def _build_uri(self):
        """ builds a valid mongodb uri which can be used to setup a client connection
        """
        _host = self.config["connectionInfo"]["mongoServerHost"]
        _port = self.config["connectionInfo"]["mongoServerPort"]
        _user = self.config["connectionInfo"]["mongoServerUser"]
        _pass = self.config["connectionInfo"]["mongoServerPass"]
        _srv = self.config["connectionInfo"]["useMongoURISRV"]
        s = "mongodb"
        if _srv:
            s += "+srv"
        s += "://"
        if _user != "":
            s += "{}:{}@".format(_user, _pass)
        
        # the host is the main required field in a uri
        s += _host
    
        if _port != isinstance(_port, int) and _port != "":
            s += ":{}".format(_port)

        if 'useMongoSSL' in self.config['connectionInfo']:
            if self.config['connectionInfo']['useMongoSSL']:
                s += "/?ssl=true"
            elif self.config['connectionInfo']['useMongoSSL'] == False:
                s += "/?ssl=false"
                
        return s

    def get_collection_size(self):
        """ gets the number of documents in a collection based on the mongo system info """

        # setup connection
        if self.setup_connection() == False:
            logging.error("Invalid MonoClient login, returning")
            return []
        
        # setup cursor
        _db = self.config["connectionInfo"]["mongoDatabase"]
        db = self.client[_db]
        collection = db[self.config["connectionInfo"]["mongoCollection"]]
        
        return collection.count()


    def pull_collection(self, query_filter={}, add_index=False):
        """ pulls data from a collection then assembles packages for the pull
            
            Arguments:
                filter {dict} -- the query to use when pulling from mongo
                add_index {bool} -- if true, adds the index of the row in 
                                    the package data, to the row
        """

        # setup connection to mongodb and get collection
        if self.setup_connection() == False:
            logging.error("Invalid MonoClient login, returning")
            return []

        logging.info('Pulling data from Mongo')

        _db = self.config["connectionInfo"]["mongoDatabase"]
        db = self.client[_db]
        collection = db[self.config["connectionInfo"]["mongoCollection"]]

        # setup a cursor object with the specified options to:
        #   -> find all docs and sort by most recently added docs
        # NOTE: this ensures only the most recently added docs are pulled
        cur = collection.find(query_filter).sort("$natural", -1)

        # get the most recently added document from the mongo database 
        try:
            newest_pulled_id = str(cur[0]["_id"])
        except Exception as err:
            logging.error("bad connection to mongo\n -> " + str(err))
            return []

        # setup packages to insert data into
        package_list = self.build_packages(self.config)

        # for each document pulled add to packages
        docs_pulled = 0
        
        for doc in cur:

            # check current document id with the last pulled id
            # break when they are the same
            if 'pullOnlyNew' in self.config['data'] and self.config['data']['pullOnlyNew']:
                if str(doc["_id"]) == self.config['data']['lastMongoIdPulled']:
                    break

            docs_pulled += 1
            # iterate over maps 
            map_i = 0
            for maps in self.config["mapping"]:
                
                t1 = time.clock()
                # iterate over sql_cols in maps
                pulled = []
                pulled_indexes = []
                longest = 0
                id_index = -1
                sql_cols_index = 0
                for key, val in maps["sql_cols"].items():
                    
                    # first check if the column should be a static value or data
                    # from a mongo document
                    if 'static_val' in val:
                        pulled.append( [val['static_val']] )

                    elif 'mongo_path' in val:
                        # check for objectid as a valid field
                        if '_id' == val['mongo_path']:
                            id_index = sql_cols_index

                        # first get the values from mongo
                        spl = val["mongo_path"].split(".")
                        
                        # if target type exists, parse it out
                        target_type = ""
                        if "target_type" in val:
                            target_type = val['target_type']

                        if "valid_types" in dict(val):
                            valid_types = val['valid_types']
                        else:
                            valid_types = ["none"]

                        # recurse through mongo doc to find data and track the index of data
                        # if it exists in a list
                        res = []
                        index_res = []
                        self.get_val_from_dict(doc, spl, res, valid_types, target_type, index_res)

                        # Optimization: only build index res if the mongo_path is a list
                        if '[all]' in val["mongo_path"]:    
                            index_res = ["{}::{}".format(key, i) for i in index_res]
                            pulled_indexes.append(index_res)

                        # if this field has the required option and none is the only data point
                        # returned, then stop entire mapping
                        if 'required' in val and val['required'] == True:
                            if res == [None for i in res]:
                                logging.error( 'Found a missing required key ({}) in mongo scrapping packages'.format(key) )
                                return []

                        res_ln = len(res)
                        if res_ln > longest:
                            longest = res_ln

                        # then add values to temp data
                        pulled.append(res)

                    sql_cols_index += 1
       
                # ensure each list in pulled have the same length
                # i.e. pulled = [[0,1,2], ['id'], []] -> translate -> [[0,1,2], ['id','id','id'], [None,None,None]]
                for r in range(len(pulled)):
                    pull_len = len(pulled[r])
                    if pull_len == longest:
                        continue
                    elif pull_len == 1:
                        pulled[r] = [pulled[r][0] for i in range(longest)]
                    elif 1 < pull_len < longest:
                        pulled[r] += [None for i in range(pull_len, longest)]

                    # catch the case where an array has no content
                    else:
                        pulled[r] = [None for i in range(longest)]

                # insert data into package
                # translate the data matrix
                # TODO catch return from insert data
                try:
                    for idx in range(longest):
                        tup = [rec[idx] for rec in pulled]
   
                        # add index to ID for back tracing data location when saving from excel
                        if add_index and id_index != -1:
                            # build return path for data
                            index_tup = []
                            
                            for rec in pulled_indexes:
                                try:
                                    
                                    if rec[0][-1] != ":":
                                        index_tup.append(rec[idx])
                                except:
                                    pass
                            tup[id_index] += "|"+"|".join(index_tup)
                        package_list[map_i].insert_data(tup)
                        t2 = time.clock()
                        package_list[map_i].setup_runtime += (t2-t1)
                except Exception as err:
                    logging.error('longest = {},\npulled = {}\n\n -> {}'.format(longest, pulled, err))
                    return []
                map_i += 1

        # close mongo query cursor
        cur.close()

        # log stats on data pulled and packages made
        db = self.config["connectionInfo"]["mongoDatabase"]
        collection = self.config["connectionInfo"]["mongoCollection"]
        logging.info('Successfully pulled {} documents from Mongo:'.format(docs_pulled))
        for pkg in package_list:
            logging.info('  -> {} records took {} sec for map destination: {} '.format(\
                len(pkg.data), \
                round(pkg.setup_runtime,3), \
                pkg.dest))

        # update last pulled document id from mongo and close connection to mongodb
        # if no documents were pulled return an empty list so sqlhandler will not insert any
        self.close_connection()
        if docs_pulled > 0:
            self.config['data']['lastMongoIdPulled'] = newest_pulled_id
            return package_list          
        else:
            return package_list

    @classmethod
    def get_val_from_dict(self, obj, mongo_path_split, out=[], 
        valid_types=["none"],  target_type="", index_list=[], _index=""):
        """ retrieve data from dict (d) at dictionary location (target)
            Arguments:
                obj {dict}                          -- mongo document to search
                mongo_path_split {list of strings}  -- path in mongo where data exists
                out {list}                          -- the list which results should be added to
                index_list {list of lists of ints}  -- indexes for any time [all] is called
                _index {list of ints}               -- indexes where in mongo the data exists 
            Returns:
                [None] -- all output is added to the var, 'out'
        """
        # when no paths are left, the data is aquired and is added to output list
        path_length = len(mongo_path_split)

        # ADD DATA TO OUT LIST:
        # verify that datapoint is both in the valid types if specified and also
        # is either at the path destination or none
        if path_length < 1 and obj is not None:
            if valid_types == ["none"] or type(obj).__name__ in valid_types:
                # use target_type to cast to sql destination type
                out.append( cast_to_target_type(obj, target_type=target_type) )
                index_list.append(_index[1:])
                
        elif obj is None and "none" in valid_types:
            out.append(obj)
            index_list.append(_index[1:])

        elif path_length > 0:
            field_name = mongo_path_split[0]

            # if the object is being indexed then we need to either recurse into
            # object at index or recurse into all objects if 'all' is specified
            if  "[" in field_name:
                path_idx_split = field_name.replace("]", "").split("[")
                key = path_idx_split[0]

                # Splits path to grab value in brackets i.e. coord[0] -> 0
                idx = path_idx_split[1]

                # add extra indexes to path if they exist (allows for nested list recursion)
                if len(path_idx_split) > 2:
                    l = ["[{}]".format(i) for i in path_idx_split[2:]]
                    mongo_path_split = mongo_path_split[:1] + l + mongo_path_split[1:]
                
                # TODO: needs commenting
                if idx == "all":
                    try:
                        if isinstance(obj, list):
                            for i in range(len(obj)):
                                try:
                                    obj_new = obj[i]
                                except:
                                    obj_new = None
                                finally:
                                    # account for the location is stored
                                    new_index = "_".join([_index, str(i)])
                                    
                                    self.get_val_from_dict(obj_new, 
                                        mongo_path_split[1:], 
                                        out, 
                                        valid_types, target_type, index_list, new_index)
                                                           
                        elif isinstance(obj, dict):
                            for i in range(len(obj[key])):
                                try:
                                    obj_new = obj[key][i]
                                except:
                                    obj_new = None
                                finally:
                                    # account for the location is stored
                                    new_index = "_".join([_index, str(i)])

                                    self.get_val_from_dict(obj_new, 
                                        mongo_path_split[1:], 
                                        out, 
                                        valid_types, target_type, index_list, new_index)
                    except:
                        self.get_val_from_dict(None, 
                            mongo_path_split[1:], 
                            out, 
                            valid_types, target_type, index_list, _index)
                else:
                    try:
                        if isinstance(obj, list):
                            obj = obj[int(idx)]
                        elif isinstance(obj, dict):
                            obj = obj[key][int(idx)]
                        else:
                            obj_new = None  
                        
                    except:
                        obj = None
                    self.get_val_from_dict(obj,
                        mongo_path_split[1:], 
                        out, 
                        valid_types, target_type, index_list, _index)

            # if object is a dict then recurse into object[key] and remove the 
            # path/key from mongo_path_split                
            elif isinstance(obj, dict):
                try:
                    obj = obj[field_name]
                except:
                    obj = None
                self.get_val_from_dict(obj,
                    mongo_path_split[1:],
                    out,
                    valid_types, target_type, index_list, _index)

            else:
                self.get_val_from_dict(None,
                    mongo_path_split[1:],
                    out,
                    valid_types, target_type, index_list, _index)
        return 

    @classmethod
    def build_packages(cls, config):
        """ assembles packages from the config and returns them in a list 

            Arguments:
                config {dict} -- ConfigHandler.config
            
            Return:
                [list of Package's] -- assembled packages to use
        """

        package_list = []
        for maps in config["mapping"]:

            ##### setup new package for map #####
            dest = maps["sql_dest"]
            c_names = list(maps["sql_cols"].keys())
            
            # grab any optional target types
            trg_types = []
            for col in maps["sql_cols"].values():
                if "target_type" in col:
                    trg_types.append(col["target_type"])
                else:
                    trg_types.append(None)
            
            # create package and add it to output package list
            new_pkg = PKG.Package(dest, c_names, trg_types)
            new_pkg.set_cardinality()
            package_list.append(new_pkg)
        
        return package_list

    def get_mongo_search_query(self, alias, input_value=None, cast_to=""):
        """ looks through config for mongoFilter and attempts to return a
            search query to use in a mongo query

            Arguments:
                alias {string} -- the key in mongoFilter to look for
            
            Returns:
                [dict] -- search term to add to mongo filter                       
        """
        
        try:
            if 'mongoFilter' not in self.config:
                query = {alias : input_value}
            else:
                # open mongoFilter dictionary from config file and parse to string
                dictionary = json.loads(json.dumps(self.config['mongoFilter'][alias]))
                query_str = str( dictionary )
                query_str = query_str.replace("'", '"')

                # if a filter requires user input then replace the value to be input
                if "INPUT_VALUE" in query_str:
                    if cast_to in STRINGS:
                        query_str = query_str.replace('INPUT_VALUE', input_value)
                    elif cast_to in NONSTRINGS:
                        query_str = query_str.replace('"INPUT_VALUE"', input_value)
                    else:
                        query_str = query_str.replace('INPUT_VALUE', input_value)
            
                    query = json.loads(query_str)
                else:
                    query = dictionary

        except Exception as err:
            logging.warning("found no interject filter for key ({}) --> {}".format(alias,err))
            query = {alias : input_value}
        finally:
            # if objectid is included convert id to ObjectId Type
            if "_id" in query:
                query['_id'] = ObjectId(query['_id'])

            return query

    def save_collection(self, update_dict, save_msg=None):
        """ attempts to update a single query (update_info[query]) 
            in mongo with a object (update_info[data])

            Arguments:
                update_dict {dict} -- dictionary with each element
        """ 

        # setup connection to mongodb and get collection
        if self.setup_connection() == False:
            logging.error("Invalid MonoClient login, returning")
            return []

        logging.info('Pulling data from Mongo')

        _db = self.config["connectionInfo"]["mongoDatabase"]
        db = self.client[_db]
        collection = db[self.config["connectionInfo"]["mongoCollection"]]
        result = None
        i = 0
        
        for update_info in update_dict.values():
            
            if update_info['data']['$set'] != None and update_info['data']['$set'] != {}:

                # verify is saveable
                result = collection.find_one_and_update(
                    filter=update_info['query'], 
                    update=update_info['data'], 
                    array_filters=update_info['options']['arrayFilters'],
                    return_document=ReturnDocument.BEFORE,
                    upsert=True
                    )
                
                # check if document was changed                
                doc = collection.find_one(update_info['query'])
                if doc != result:
                    print("===> Change Made({},{})\n *R* {}\n *O* {}".format(i,'MsgToUser',result, doc))
                    save_msg.at[i,'MessageToUser'] = "document updated"
                else:
                    save_msg.at[i,'MessageToUser'] = "no change"

                i += 1
        self.close_connection()
        return [save_msg]
       
    @classmethod
    def xml_to_dataframe(cls, xml, package_index=0):
        """ takes xml (from interject currently) and parses it out to be
        able to work with the data in dataframe format. 
        
        NOTE: Row is parsed out in order to associate data from excel and data saved
        to allow for save messages to be sent back to Interject.
        """

        root = etree.fromstring(xml)
        column_names = []   # column names for data
        row_list = []
        row_data = []
        save_message_rows = []

        for row in root:
            
            # assemble data from xml into row list
            if row.tag == "r":
                row_data = []
                save_message_rows.append([row[0].text,""])

                for col in row[1:]:
                    row_data.append(col.text)
                row_list.append(row_data)

            # parse out column headers
            elif row.tag == "c":
                column_names.append(row.attrib['Column'])
        
        df_data = pd.DataFrame(row_list, columns=column_names[1:])
        df_save = pd.DataFrame(save_message_rows, columns=["Row","MessageToUser"])
        
        return [df_data, df_save]

    def dataframe_to_dict(self, dataframe, package_index=0):
        """ a custom method to parse the interject xml returned from a save into a dict object
            which can be upserted back into mongodb

            Argument:
                xml {string} -- xml string to parse
                package_index {int} -- mapping index for which map to pull mongo_paths from

            Returns:
            TODO: FIX COMMENTS
                [dict]['query'] -- the query, object id to update
                [dict]['data']  -- the update, information to replace/add existing with 
        """

        return_dict = OrderedDict()  # output object with new json objects to update mongo with

        column_names = dataframe.columns.tolist()   # column names for data

        updatable_keys = self.get_mongo_update_keys()   # valid columns to update mongo with
         
        sql_cols_obj = self.config['mapping'][package_index]['sql_cols'] 
        
        for row in dataframe.values.tolist():
        
            # assemble data from xml into row list
            update_data = {"$set" : {}}
            update_query = {}
            update_id = ""
            traceback_mongo_paths = {}

            # attempt to find object_id for index info later
            for col_idx in range(len(row)):
                
                # use objectid for query
                if column_names[col_idx] == "_id":
                    
                    # Make sure that the id to update is a valid id to update
                    if row[col_idx] == '' or row[col_idx] == None:
                        update_id = ''
                        logging.warn("found empty id")
                    else:
                        try:
                            update_id, traceback_mongo_paths, update_options = self.reassemble_paths(row[col_idx], package_index)
                        except Exception as e:
                            print("{}  --  {}".format(update_id, e))
                        update_query = {"_id" : ObjectId(update_id)}

            if update_id != '' or update_id != None:
                # setup object for options
                if update_id not in return_dict: 
                    return_dict[update_id] = {}

                    # remove arrayfilter options
                    return_dict[update_id]['options'] = {}
                    return_dict[update_id]['options']['arrayFilters'] = []
                    return_dict[update_id]['query'] = {}
                    return_dict[update_id]['data'] = {}

                # convert list into dict
                for col_idx in range(len(row)):
                    # replace keys with the locations for data and the data values
                    if column_names[col_idx] in updatable_keys[package_index]:
                        if column_names[col_idx] in traceback_mongo_paths:
                            mongo_path = traceback_mongo_paths[column_names[col_idx]]
                        else:
                            mongo_path = sql_cols_obj[column_names[col_idx]]['mongo_path']
                        
                        # determine what type the data should be cast to (defaults to string if nothing is specified)
                        path_data = None
                        if 'mongoUpdateType' in sql_cols_obj[column_names[col_idx]]:

                            # get builtin python type from string
                            var_type = __builtins__[sql_cols_obj[column_names[col_idx]]['mongoUpdateType']]
                            try:
                                path_data = var_type( row[col_idx] )
                            except:
                                path_data = None
                        else:
                            path_data = row[col_idx]

                        if path_data is not None:
                            update_data["$set"][mongo_path] = path_data

                # set the query and data to use in a mongdb update call
                deepmerge_dicts(return_dict[update_id]['query'], update_query)
                deepmerge_dicts(return_dict[update_id]['data'], update_data)
                
                # add new filters to arrayFilters
                # DEPRECATE
                """
                for item in update_options:
                    add = True
                    for existing_item in return_dict[update_id]['options']['arrayFilters']: 
                        if existing_item.keys() == item.keys():
                            add = False
                            break
                    if add:
                        return_dict[update_id]['options']['arrayFilters'].append( item )
                """
        return return_dict

    def reassemble_paths(self, info, package_index=0):
        """ assembles any paths for data attempting to insert back into a nested list
            Arg
            TODO: finish comments and refactoring
        """
        # parse out information from object id string
        try:
            try:
                info_split = info.split("|")
            except Exception as e:
                print("1) " + str(e))

            length = len(info_split)
            filters_array = []

            # attempt to return only the id if the string passed in does not contain all
            if length == 1 or (length == 2 and info_split[1] == ''):
                return info_split[0], {}, filters_array

            # for any path including [all]
            elif length > 1:
                object_id = info_split[0]
                output_dict = {}
                for var in info_split[1:]:
                    try:
                        alias = var.split("::")
                    except Exception as e:
                        print("2) " + str(e))

                    indexes = alias[1].split("_")
                    alias = alias[0]

                    new_mongo_path = self.config['mapping'][package_index]['sql_cols'][alias]['mongo_path']
                    for i in indexes:
                        new_mongo_path = new_mongo_path.replace("[all]", ".{}".format(i), 1)

                    # add transformed path to dictionary
                    output_dict[alias] = new_mongo_path
                return object_id, output_dict, filters_array
            else:
                return "", {}, filters_array
        except Exception as e:
            logging.error("Reassemble_paths ERROR: {}".format(e))
            return "", {}, []


    def get_mongo_update_keys(self):
        """ returns a list of sql cols with 'allowMongoUpdate':true for each package """
        map_keys = []
        # iterate over maps
        for _map in self.config['mapping']:
            keys = []
            for key in _map['sql_cols']:
                if 'allowMongoUpdate' in _map['sql_cols'][key]:
                    keys.append(key)
            map_keys.append(keys)
        return map_keys

    def remove_from_mongo(self, doc_id_list):
        """ """

        # setup connection to mongodb and get collection
        if self.setup_connection() == False:
            logging.error("Invalid MonoClient login, returning")
            return []

        logging.info('Pulling data from Mongo')

        _db = self.config["connectionInfo"]["mongoDatabase"]
        db = self.client[_db]
        collection = db[self.config["connectionInfo"]["mongoCollection"]]
        result = None

        for _id in doc_id_list:
            try:
                collection.delete_one({'_id': ObjectId(_id)})
            except Exception as err:
                logging.error("could not delete doc ({})".format(err))
            
            logging.info("document ({}) successfully removed".format(_id))

        self.close_connection()

        

####################################
##### --- Static Functions --- #####
####################################

def deepmerge_dicts(dict_to_add_to, dict_to_add):
    """ takes two dictionaries and merges them at the deepest level where a difference occurs 

        Example:
        {key : {key2 : value}}  +  {key : {key3 : value}}  =  {key : {key2 : value, key3 : value}}
    """
    for key, val in dict_to_add.items():
        if key in dict_to_add_to and isinstance(val, dict):
            deepmerge_dicts(dict_to_add_to[key], dict_to_add[key])
        elif key not in dict_to_add_to:
            dict_to_add_to[key] = val

def cast_to_target_type(mongodata, target_type=""):
    """ takes any point of single element data and attempts
    to convert it to the proper type to be inserted into sql.
    """
    try:
        if target_type == "str":
            if isinstance(mongodata, str):
                return mongodata
            else:
                return str(mongodata)

        elif target_type == "int":
            if isinstance(mongodata, int) or isinstance(mongodata, float):
                return mongodata
            elif isinstance(mongodata, str):
                try:
                    return float(mongodata)
                except Exception as e:
                    logging.error("Could not convert string to int: {}".format(e))
                    
        elif target_type == "date":
            if isinstance(mongodata, datetime.datetime):
                return mongodata.isoformat()
            elif isinstance(mongodata, str):
                return mongodata
            elif isinstance(mongodata, int) or isinstance(mongodata, float):
                return str(mongodata)

        elif target_type == "":
            if isinstance(mongodata, datetime.datetime) or \
               type(mongodata).__name__ == "ObjectId":
                return str(mongodata)
            else:
                return str(mongodata)
    except:
        return None
        
        

