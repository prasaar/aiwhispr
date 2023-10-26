import os
import sys
import io
import uuid
import time
from datetime import datetime, timedelta
import pathlib
import json
from pymongo import MongoClient

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb

import aiwhisprConstants 

import logging

class createVectorDb(vectorDb):

    def __init__(self,vectordb_config:{}, content_site_name:str,src_path:str,src_path_for_results:str):
        
        vectorDb.__init__(self,
                        vectordb_config = vectordb_config,
                        content_site_name = content_site_name,
                        src_path = src_path,
                        src_path_for_results = src_path_for_results,
                        module_name = 'mongodbVectorDb')

        self.logger = logging.getLogger(__name__)
        
        try:
            self.vectordb_dbname = vectordb_config['dbname']
        except:
            self.logger.error("mongodb connection requires a valid dbname specified in config file")
            sys.exit()

        try:
            self.vectordb_connection_string = vectordb_config['connection-string']
        except:
            self.logger.error("mongodb connection requires a connection-string to be specified in config file")
            sys.exit()

        try:
            self.vectordb_vector_index = vectordb_config['vector-index']
        except:
            self.logger.error("mongodb Atlas Search vector-index is not specified in config file")
            sys.exit()


        try:
            self.vectordb_vector_dim = int(vectordb_config['vector-dim'])
        except:
            self.logger.error("mongodb requires vector dimensions to be provided. Have you set this as vector-dim=<int> ?")
            sys.exit()
        
        if 'collection-name' in vectordb_config:
            self.collection_name = vectordb_config['collection-name']
        else:
            self.setDefaultCollectionName()
        
        
        if 'text-index' in vectordb_config:
            self.vectordb_text_index = vectordb_config['text-index']
        else:
            self.logger.info("No text index provided for mongodb Atlas Search")
            self.vectordb_text_index = ""


    def testConnect(self):
        try:
            self.logger.debug("Creating a mongodb connection")
            self.connection_client = MongoClient(self.vectordb_connection_string)
            self.vectorDbClient = self.connection_client[self.vectordb_dbname]
        except:
            self.logger.error("Could not create mongodb connection")
        else:
            collectionExists = False
            self.logger.debug(self.vectorDbClient.list_collection_names())
            for coll_name in self.vectorDbClient.list_collection_names():
                if coll_name == self.collection_name:
                    self.logger.debug("Found collection name %s", coll_name)
                    collectionExists = True
            if collectionExists == True:
                self.logger.info("Collection %s already exists", self.collection_name)
            

    def connect(self):
        try:
            self.logger.debug("Creating a mongodb connection with connection_string: %s , dbname: %s", self.vectordb_connection_string, self.vectordb_dbname)
            self.connection_client = MongoClient(self.vectordb_connection_string)
            self.logger.debug("Created connection to mongodb, now accessing database")
            self.vectorDbClient = self.connection_client[self.vectordb_dbname]
            self.logger.debug("Connected to database %s", self.vectordb_dbname )
        except Exception as err:
            self.logger.error("Could not create mongodb connection with connection_string: %s , dbname: %s", self.vectordb_connection_string, self.vectordb_dbname)
            print(err)
            raise
        else:
            collectionExists = False
            try:
                self.logger.debug(self.vectorDbClient.list_collection_names())
                for coll_name in self.vectorDbClient.list_collection_names():
                    if coll_name == self.collection_name:
                        self.logger.debug("Found collection name %s", coll_name)
                        collectionExists = True
                    
                if collectionExists == True:        
                    self.logger.info("Collection %s already exists", self.collection_name)
                else:
                    self.logger.info("mongodb collection %s does not exist , so we will create it", self.collection_name)
                    #create the collection in mongodb
                    try:
                        collection = self.vectorDbClient[self.collection_name]    
                        #Create a test record 
                        id="TEST-TEST-TEST-TEST"
                        content_site_name="TEST-TEST-TEST-TEST"
                        src_path="TEST"
                        src_path_for_results="TEST"
                        content_path="TEST"
                        last_edit_date=0.0
                        tags=""
                        title=""
                        text_chunk="This_is_a_test_text_inserted_by_aiwhispr"
                        text_chunk_no=1
                        dim_counter = 0
                        vector_embedding = []
                        while dim_counter < self.vectordb_vector_dim:
                            vector_embedding.append(0.0)
                            dim_counter = dim_counter +1 
                        vector_embedding_date=0.0

                        content_chunk_map_record = {
                            'id' :  id,
                            'content_site_name' : self.content_site_name,
                            'src_path' : self.src_path,
                            'src_path_for_results' : self.src_path_for_results,
                            'content_path' : content_path,
                            'last_edit_date' : last_edit_date,
                            'tags' : tags,
                            'title' : title,
                            'text_chunk' : text_chunk,
                            'text_chunk_no' : text_chunk_no,
                            'vector_embedding' : vector_embedding,
                            'vector_embedding_date': vector_embedding_date
                        }
                        
                        collection.insert_one(content_chunk_map_record)
                        self.logger.info("Create Collection : %s", self.collection_name )
                        collection.create_index("id")
                        collection.create_index("content_site_name")  

                        filter_by_conditions = {"$and": [ {'content_site_name' :  self.content_site_name }, {'id' :  'TEST-TEST-TEST-TEST' } ] }
                        try:
                            delete_results = self.vectorDbClient[self.collection_name].delete_many(filter_by_conditions)
                            self.logger.debug("Deleted %d TEST rows from %s", delete_results.deleted_count, self.collection_name)   
                        except: 
                            self.logger.error("Could not TEST rows for %s",self.collection_name)   

                    except:
                        self.logger.error("Could not not create collection %s in mongodb", self.collection_name)
            
            except Exception as err:
                    self.logger.error("Could not check if collection exists")
                    print(err)
                    
        
    def deleteAll(self):
        #delete all rows for the content_site_name 
        filter_by_conditions = {'content_site_name' :  self.content_site_name }
        try:
            delete_results = self.vectorDbClient[self.collection_name].delete_many(filter_by_conditions)
            self.logger.debug("Deleted %d rows from %s", delete_results.deleted_count , self.collection_name)   
        except: 
            self.logger.error("Could not deleteAll for %s",self.collection_name)   

    def insert(self, 
               id:str,
               content_path:str, 
               last_edit_date:float, 
               tags:str, 
               title:str, 
               text_chunk:str, 
               text_chunk_no:int, 
               vector_embedding:[]
               ):
        #Lets read the chunk file first

        try:
            #get the current time since epoch in seconds
            vector_embedding_date = time.time()

             ##Insert record in typesense collection
            self.logger.debug("Inserting record in VectorDB")
            self.logger.debug("id:%s",id)
            self.logger.debug("content_site_name:%s", self.content_site_name )
            self.logger.debug("src_path:%s", self.src_path)
            self.logger.debug("src_path_for_results:%s", self.src_path_for_results)
            self.logger.debug("content_path:%s", content_path)
            self.logger.debug("last_edit_date:%f", last_edit_date)
            self.logger.debug("tags:%s", tags)
            self.logger.debug("title:%s", title)
            self.logger.debug("text_chunk.. first char:%s", text_chunk[0:1])
            self.logger.debug("text_chunk_no:%d", text_chunk_no)
            self.logger.debug("vector_embedding(size):%d", len(vector_embedding))
            self.logger.debug("vector_embedding_date:%f", vector_embedding_date)

            content_chunk_map_record = {
                'id' :  id,
                'content_site_name' : self.content_site_name,
                'src_path' : self.src_path,
                'src_path_for_results' : self.src_path_for_results,
                'content_path' : content_path,
                'last_edit_date' : last_edit_date,
                'tags' : tags,
                'title' : title,
                'text_chunk' : text_chunk,
                'text_chunk_no' : text_chunk_no,
                'vector_embedding' : vector_embedding,
                'vector_embedding_date': vector_embedding_date
            }
            self.vectorDbClient[self.collection_name].insert_one(content_chunk_map_record)
            self.logger.info("Completed inserting vector record")
        except:
            self.logger.error("Could not insert the record in mongodb")
            self.logger.error(json.dumps(content_chunk_map_record))

 
    def search(self,content_site_name,vector_embedding, limit_hits, input_text_query = ''):
        
        vector_as_string = ','. join(str(e) for e in vector_embedding)
        include_text_results = False
        score_details = True
        search_vector_query= [
            {
                "$vectorSearch": {
                "index": self.vectordb_vector_index,
                "queryVector": vector_embedding,
                "path": "vector_embedding",
                "numCandidates": 100,
                "limit": limit_hits
                }
            }
            ,
            {"$match": {"content_site_name": content_site_name}},
            {
                "$project": {
                    "_id": 0,
                    "content_site_name": 1,
                    "id":1,
                    "content_path":1,
                    "src_path":1,
                    "src_path_for_results":1,
                    "text_chunk":1,
                    "text_chunk_no":1,
                    "tags":1,
                    "title":1,
                    "last_edit_date":1,
                    "vector_embedding":1,
                    "vector_embedding_date":1,
                    "score": {"$meta": "vectorSearchScore"}
                    }
            }
        ];

        if len(input_text_query) > 0  and len(self.vectordb_text_index) > 0 :
            self.logger.debug('Will do multisearch, vector and text')
            include_text_results = True
            score_details = False
            search_text_query = [
                {
                    "$search": {
                    "index": self.vectordb_text_index,
                    "scoreDetails": score_details,
                    "compound": {
                            "filter": [{
                                "queryString": {
                                "defaultPath": "content_site_name",
                                "query": content_site_name
                                }
                            }],
                            "must": {
                                "text": {
                                    "query": input_text_query,
                                    "path": "text_chunk",
                                    "fuzzy": {
                                        "maxEdits":2
                                    }
                                }
                            }
                        }
                    },
                },
                {'$limit': limit_hits},
                {
                "$project": {
                    "_id": 0,
                    "content_site_name": 1,
                    "id":1,
                    "content_path":1,
                    "src_path":1,
                    "src_path_for_results":1,
                    "text_chunk":1,
                    "text_chunk_no":1,
                    "tags":1,
                    "title":1,
                    "last_edit_date":1,
                    "vector_embedding":1,
                    "vector_embedding_date":1,
                    "score": {"$meta": "searchScore"}
                    }
                }
            ]
        
        """""
        We will send  a JSON Object in the format 
        {"results": [ semantic_results{} ,text_results{}  ]}
       
         semantic_results / text_results will be a format 
         {
         "found" : int
         "type"  : semantic / text / image 
         "hits"  : []
         }
             
            hits[]  will be a list Example : hits[ {result},   {result}]
            Format of result dict 
            {
               id: UUID,
               content_site_name: str,
               content_path:str,
               src_path:str,
               src_path_for_results,
               tags:str,
               text_chunk:str,
               text_chunk_no:int,
               title:int,
               last_edit_date:float,
               vector_embedding_date:float,
               match_score: float,
            }
        """""
        search_vector_results=self.vectorDbClient[self.collection_name].aggregate(search_vector_query)

        json_results = {} #Dict
        json_results['results'] = []

        self.logger.debug('Received mongodb Search Results:')
        #self.logger.debug(json.dumps(search_vector_results))

        semantic_results = {} #Dict
        text_results = {} #Dict
        semantic_hits = []
        text_hits = []
        
        
        
        no_of_semantic_hits = 0
        for chunk_map_record in search_vector_results:
            result = {} #Dict to hold a single result
            
            no_of_semantic_hits = no_of_semantic_hits + 1
            
            result['match_score'] = 1.0 - chunk_map_record['score']
            result['content_site_name'] = chunk_map_record['content_site_name']
            result['id'] = chunk_map_record['id']
            result['content_path'] = chunk_map_record['content_path']
            result['src_path'] = chunk_map_record['src_path']
            #result['src_path_for_results'] = chunk_map_record['src_path_for_results']
            result['src_path_for_results'] = self.src_path_for_results
            result['text_chunk'] = chunk_map_record['text_chunk']
            result['text_chunk_no'] = chunk_map_record['text_chunk_no']
            result['tags'] = chunk_map_record['tags']
            result['title'] = chunk_map_record['title']
            result['last_edit_date'] = chunk_map_record['last_edit_date']
            result['vector_embedding_date'] = chunk_map_record['vector_embedding_date']
            result['vector_embedding'] = chunk_map_record['vector_embedding']
            
            semantic_hits.append(result)
            

        
        semantic_results['type'] = 'semantic'
        semantic_results['found'] = no_of_semantic_hits
        semantic_results['hits'] = semantic_hits
        json_results['results'].append(semantic_results)
        
        if include_text_results == True:
            search_text_results=self.vectorDbClient[self.collection_name].aggregate(search_text_query)

            no_of_text_hits = 0
            text_results['found'] = no_of_text_hits
            text_results['type'] = 'text'
            
            for chunk_map_record in  search_text_results:
                result = {} #Dict to hold a single result
                no_of_text_hits = no_of_text_hits + 1
                
                result['match_score'] =  chunk_map_record['score']
                result['content_site_name'] = chunk_map_record['content_site_name']
                result['id'] = chunk_map_record['id']
                result['content_path'] = chunk_map_record['content_path']
                result['src_path'] = chunk_map_record['src_path']
                #result['src_path_for_results'] = chunk_map_record['src_path_for_results']
                result['src_path_for_results'] = self.src_path_for_results
                result['text_chunk'] = chunk_map_record['text_chunk']
                result['text_chunk_no'] = chunk_map_record['text_chunk_no']
                result['tags'] = chunk_map_record['tags']
                result['title'] = chunk_map_record['title']
                result['last_edit_date'] = chunk_map_record['last_edit_date']
                result['vector_embedding_date'] = chunk_map_record['vector_embedding_date']
                result['vector_embedding'] = chunk_map_record['vector_embedding']
    
                text_hits.append(result)

            text_results['found'] = no_of_text_hits
            self.logger.debug("Number of text results: %d",no_of_text_hits )
            text_results['hits'] = text_hits
            json_results['results'].append(text_results)

        self.logger.debug(json.dumps(json_results))
        return json_results

    def getExtractedText(self,content_site_name:str,content_path:str):
        
        search_query= { "$and": [ {"content_path":content_path}, {"content_site_name":content_site_name}] }
        projection = {"text_chunk":1, "text_chunk_no": 1}
        
        try:
            search_results = self.vectorDbClient[self.collection_name].find(search_query, projection)
            self.logger.debug('Received mongodb search results:')
            self.logger.debug("getExtractedText for content-site{%s} content-path{%s}", content_site_name, content_path)
        except Exception as err: 
            self.logger.exception("Could not get extractedText for content-site{%s} content-path{%s}", content_site_name, content_path)   
            
        text_chunk_numbers=[]
        text_chunks={}
        extracted_text = ""

        for document in search_results:   
            text_chunks[str(document['text_chunk_no'])] = document['text_chunk']
            text_chunk_numbers.append(document['text_chunk_no'])
            self.logger.debug("getExtractedText text_chunk_no:%d",document['text_chunk_no'] )
            
        for j in sorted(text_chunk_numbers):
           self.logger.debug("getExtractedText text chunk append number:%d", j)
           extracted_text = extracted_text + text_chunks[str(j)]

        return extracted_text
