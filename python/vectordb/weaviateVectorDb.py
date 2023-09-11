import os
import sys
import io
import uuid
import time
from datetime import datetime, timedelta
import pathlib
import json
import weaviate

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
                          module_name = 'weaviateVectorDb')

        self.vectordb_hostname = vectordb_config['api-address']
        self.vectordb_portnumber = vectordb_config['api-port']
        self.vectordb_key = vectordb_config['api-key']

        self.vectorDbClient:weaviate.Client
        self.logger = logging.getLogger(__name__)

    def connect(self):

        #First create the connection
        try:
            self.logger.debug("Creating a Weaviate Connection")    

            if self.vectordb_hostname[0:6] == 'https:'  or self.vectordb_hostname[0:5] == 'http:' :
                self.logger.debug("Create Weaviate http(s) connection to hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
                connect_url = self.vectordb_hostname + ':' + self.vectordb_portnumber
                if (len(self.vectordb_key) > 0 ): 
                    auth_config = weaviate.AuthApiKey(api_key=self.vectordb_key)
                    self.vectorDbClient = weaviate.Client(url=connect_url,
                                                        auth_client_secret=auth_config,
                                                        timeout_config=(5, 15),) #Create connection to http/https host with key
                else:
                    self.vectorDbClient = weaviate.Client(url=connect_url, timeout_config=(5, 15),) #Create connection to http/http host without key
            else: #Assuming IP/hostname with PortNumber
                self.logger.debug("Create Weaviate http connection to hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
                connect_url = 'http://' + self.vectordb_hostname + ':' + self.vectordb_portnumber
                if (len(self.vectordb_key) > 0 ): 
                    auth_config = weaviate.AuthApiKey(api_key=self.vectordb_key)      
                    self.vectorDbClient = weaviate.Client(url=connect_url,
                                                        auth_client_secret=auth_config,
                                                        timeout_config=(5, 15),) #Create connection with key
                else:
                    self.vectorDbClient = weaviate.Client(url=connect_url, timeout_config=(5, 15),) #Create connection without key
        except Exception:    
            self.logger.error("Could not create Weaviate connection to Qdrant Server hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
        

        #Define a class object ContentChunkMap
        class_obj = {
            'class': 'ContentChunkMap',
            'vectorizer': 'none',
            'properties': [
                  {"name": "content_site_name", "dataType": ['text']},
                  {"name": "src_path", "dataType": ['text'] }, 
                  {"name": "src_path_for_results", "dataType": ['text']},
                  {"name": "content_path", "dataType": ['text']},
                  {"name": "last_edit_date", "dataType": ['number'] },
                  {"name": "tags", "dataType": ['text'], "tokenization": "word"},
                  {"name": "title", "dataType": ['text'], "tokenization": "word" },
                  {"name": "text_chunk", "dataType": ['text'], "tokenization": "word"},
                  {"name": "text_chunk_no", "dataType": ['int']},
                  {"name": "vector_embedding_date", "dataType": ['number']},

                  ],
            }


        #Now check if the class ContentChunkMap already exists, if not then recreate it
        classExistsFlag =  self.vectorDbClient.schema.contains(class_obj)
        
        if classExistsFlag == True:
            self.logger.info('Weaviate: class ContentChunkMap exists')
        else:
            self.logger.info("Weaviate: class ContentChunkMap does not exist , so we will create it")
            #create the collection in Weaviate
            #We are not creating an 'uuid' (unique id)  field and vector field. It will be provided in insert statements by the client
            self.vectorDbClient.schema.create_class(class_obj)
            if(self.vectorDbClient.schema.contains(class_obj) == True):
                self.logger.info("Weaviate: Created class ContentChunkMap ")
            else:
                self.logger.error("Weaviate: Could not create class ContentChunkMap")

    def insert(self, 
               id:str,  #should be a uuid
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
            data_object = {
                'content_site_name' : self.content_site_name,
                'src_path' : self.src_path,
                'src_path_for_results' : self.src_path_for_results,
                'content_path' : content_path,
                'last_edit_date' : last_edit_date,
                'tags' : tags,
                'title' : title,
                'text_chunk' : text_chunk,
                'text_chunk_no' : text_chunk_no,
                'vector_embedding_date': vector_embedding_date
            }

            self.logger.debug("Inserting a record in Weaviate vectordb: %s with vector embedding of size: %d", json.dumps(data_object), len(vector_embedding) )

            self.vectorDbClient.data_object.create(
                class_name="ContentChunkMap",
                uuid=id,
                vector=vector_embedding,
                data_object = data_object
            )
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not insert the record in Weaviate")

    def deleteAll(self):
        #delete all rows for the content_site_name 
        continueDeleteFlag  = True
        try:
            #MaxLimit for delete in Weaviate is 10000, so we have to run this multiple times
            while continueDeleteFlag:

                response_dry_run = self.vectorDbClient.batch.delete_objects(
                    class_name="ContentChunkMap",
                    where = {
                        'path':['content_site_name'],
                        'operator': 'Equal',
                        'valueText': self.content_site_name
                    },
                    dry_run = True,
                    output='verbose'
                )

                if response_dry_run['results']['matches'] > 0:
                    continueDeleteFlag = True
                    self.vectorDbClient.batch.delete_objects(
                    class_name="ContentChunkMap",
                    where = {
                        'path':['content_site_name'],
                        'operator': 'Equal',
                        'valueText': self.content_site_name
                    },  
                    )
                else:
                    continueDeleteFlag = False            
            
            self.logger.debug("Weaviate:Deleted rows from ContentChunkMap")   
        except: 
            self.logger.error("Weaviate:Could not deleteAll for ContentChunkMap")


    def search(self,content_site_name,vector_embedding, limit_hits, input_text_query = ''):
      
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
        #vector_as_string = ','. join(str(e) for e in vector_embedding)

        include_text_results = False
        if len(input_text_query) > 0 :
            include_text_results = True
       
        search_response = ( self.vectorDbClient.query
            .get("ContentChunkMap",["content_site_name", "src_path", "src_path_for_results", "content_path", "last_edit_date", "tags", "title", "text_chunk", "text_chunk_no", "vector_embedding_date"])
            .with_where({
                "path": ["content_site_name"],
                "operator": "Equal",
                "valueText": self.content_site_name
            })
            .with_near_vector({ "vector": vector_embedding})
            .with_limit(limit_hits)
            .with_additional(["distance", "id"])
            .do()
        )
        search_results=search_response['data']['Get']['ContentChunkMap']
        
        self.logger.debug("Search Response: %s", str(search_response))

        json_results = {} #Dict
        json_results['results'] = []

        semantic_results = {} #Dict
        text_results = {} #Dict
        semantic_hits = []
        text_hits = []

        no_of_semantic_hits = len(search_results)
        semantic_results['found'] = no_of_semantic_hits
        semantic_results['type'] = 'semantic'
        self.logger.debug("Weaviate: semantic search  found %d results", no_of_semantic_hits)
        i = 0
        while i < no_of_semantic_hits:
            result = {} #Dict to hold a single result
            
            chunk_map_record = search_results[i]
            
            result['id'] = chunk_map_record['_additional']['id']
            result['match_score'] =  chunk_map_record['_additional']['distance']
            result['content_site_name'] = chunk_map_record['content_site_name']
            result['content_path'] = chunk_map_record['content_path']
            result['src_path'] = chunk_map_record['src_path']
            result['src_path_for_results'] = self.src_path_for_results
            result['text_chunk'] = chunk_map_record['text_chunk']
            result['text_chunk_no'] = chunk_map_record['text_chunk_no']
            result['tags'] = chunk_map_record['tags']
            result['title'] = chunk_map_record['title']
            result['last_edit_date'] = chunk_map_record['last_edit_date']
            result['vector_embedding_date'] = chunk_map_record['vector_embedding_date']
            
            semantic_hits.append(result)
            i = i + 1 

        semantic_results['hits'] = semantic_hits
        json_results['results'].append(semantic_results)

        if include_text_results == True:

            #We have to do a text match search , by changing the filter condition
            self.logger.debug("Will do a text search on collection")
           
            search_response = ( self.vectorDbClient.query
            .get("ContentChunkMap",["content_site_name", "src_path", "src_path_for_results", "content_path", "last_edit_date", "tags", "title", "text_chunk", "text_chunk_no", "vector_embedding_date"])
            .with_bm25(query=input_text_query, properties=["text_chunk", "title", "tags"])
            .with_where({
                "path": ["content_site_name"],
               "operator": "Equal",
               "valueText": self.content_site_name
            })
            .with_limit(limit_hits)
            .with_additional(["score","id"])
            .do()
            )
            search_results=search_response['data']['Get']['ContentChunkMap']

            self.logger.debug("SearchResponse %s", search_response)

            no_of_text_hits = len(search_results)
            text_results['found'] = no_of_text_hits
            text_results['type'] = 'text'
            self.logger.debug("Weaviate: text search  found %d results for input query: %s",no_of_text_hits, input_text_query)
            i = 0
            while i < no_of_text_hits:
                result = {} #Dict to hold a single result
                
                chunk_map_record = search_results[i]
                
                result['id'] = chunk_map_record['_additional']['id']
                result['match_score'] =  chunk_map_record['_additional']['score']
                result['content_site_name'] = chunk_map_record['content_site_name']
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
                
                text_hits.append(result)
                i = i + 1 

            text_results['hits'] = text_hits
            json_results['results'].append(text_results)


        return json_results
