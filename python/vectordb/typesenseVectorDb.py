import os
import sys
import io
import uuid
import time
from datetime import datetime, timedelta
import pathlib
import json
import typesense


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
                        module_name = 'typesenseVectorDb')
        
        self.vectorDbClient:typesense.Client
    
        self.logger = logging.getLogger(__name__)

        self.vectordb_hostname = vectordb_config['api-address']
        self.vectordb_portnumber = vectordb_config['api-port']
        self.vectordb_key = vectordb_config['api-key']    
        try:
            self.vectordb_vector_dim = int(vectordb_config['vector-dim'])
        except:
            self.logger.error("Typesense requires vector dimensions to be provided. Have you set this as vector-dim=<int> ?")
            sys.exit()
        
        if 'collection-name' in vectordb_config:
            self.collection_name = vectordb_config['collection-name']
        else:
            self.setDefaultCollectionName()
        
    def testConnect(self):
        try:
            self.logger.debug("Creating a Typesense Connection")

            self.vectorDbClient = typesense.Client({
                'api_key': self.vectordb_key,
                'nodes': [
                    {
                    'host': self.vectordb_hostname,
                    'port': self.vectordb_portnumber,
                    'protocol': 'http'
                    },
            ],
            'connection_timeout_seconds': 60
            })
        except:
            self.logger.error("Could not create typesense connection to Typesense Server hostname: %s , portnumber: %s", self.vectordb_hostname, self.vectordb_portnumber)
        else:
            all_collections = self.vectorDbClient.collections.retrieve()
            table_found = "N"
            for collection in all_collections:
                if collection['name'] == self.collection_name:
                    table_found = "Y"
            
            if table_found == "Y":
                self.logger.info("Collection %s already exists", self.collection_name)
            

    def connect(self):
        try:
            self.logger.debug("Creating a Typesense Connection")

            self.vectorDbClient = typesense.Client({
                'api_key': self.vectordb_key,
                'nodes': [
                    {
                    'host': self.vectordb_hostname,
                    'port': self.vectordb_portnumber,
                    'protocol': 'http'
                    },
            ],
            'connection_timeout_seconds': 60
            })
        except:
            self.logger.error("Could not create typesense connection to Typesense Server hostname: %s , portnumber: %s", self.vectordb_hostname, self.vectordb_portnumber)
        else:
            all_collections = self.vectorDbClient.collections.retrieve()
            table_found = "N"
            for collection in all_collections:
                if collection['name'] == self.collection_name:
                    table_found = "Y"
            
            if table_found == "Y":
                self.logger.info("Typesense collection %s already exists", self.collection_name)
            else:
                self.logger.info("Typesense collection %s does not exist , so we will create it", self.collection_name)
                #create the collection in typesense
                #We are not creating an 'id' (unique id)  field. It will be provided in insert statements by the client
                #We expect id to be in the format <site-name>/<extracted-file_directory-name>/<chunk-files-directory>/<chunk-id>
                self.vectordb_vector_dim
                create_response = self.vectorDbClient.collections.create({
                    "name": self.collection_name,
                    "fields": [
                #SITE_NAME IS USED TO DEFINE THE SITE e.g. mas.gov.sg. THIS IS USED AS  FILTERING CRITERIA WHEN YOU WANT TO SEPRATE SEARCH BASED ON DIFFERENT SITES
                        {"name": "content_site_name", "type": "string", "index": True  },
                        #SRC_PATH IS USED TO DEFINE THE TOP SOURCE PATH FROM WHICH THE CONTENT RETRIEVER WILL START INDEXING CONTENT.
                        # Example: For an Azure Blob/container it will be https://<storage_account>.blob.core.windows.net/<container>
                        {"name": "src_path", "type": "string" , "optional": True, "index": False},
                        #SRC_PATH_FOR_RESULTS is used as the prefix instead of SRC_PATH when displaying the link to content in the search results
                        # Example: SRC_PATH for Azure Blob/container https://<storage_account>.blob.core.windows.net/<container>
                        # The results can have fileshare prefix SRC_PATH_FOR_RESULTS for Azure Blob/container https://<storage_account>.file.core.windows.net/<container>
                        {"name": "src_path_for_results", "type": "string", "optional": True, "index": False},
                        # CONTENT_PATH is the path to the original content including file name under the SRC_PATH
                        {"name": "content_path", "type": "string", "index": True},
                        # LAST_EDIT_DATE is the last edit date read from source for the content
                        {"name": "last_edit_date", "type": "float" , "optional": True, "index": False},
                        # TAGS is an optional field that is used to store any tags associated with the content , seprated by "|" character
                        {"name": "tags", "type": "string", "optional": True , "index": False},
                        # TITLE is an optional field that is used to store any title for the content
                        {"name": "title", "type": "string","optional": True, "index": True },
                        # CHUNK_TEXT  is the text that will be used by the LLM
                        {"name": "text_chunk", "type": "string", "optional": True , "index": True},
                        # CHUNK_NO is a mandatory field, it is a running sequence of numbers for the sections of the text in the document. This is useful when the content is broken into sections.
                        {"name": "text_chunk_no", "type": "int32", "optional": True, "index": False },
                        #BELOW VECTOR FIELD : We are chossing a 768 dimension vector based on all_mpnet
                        {"name": "vector_embedding", "type": "float[]", 'num_dim': self.vectordb_vector_dim, "optional": True , "index": True},
                        # VECTOR_EMBEDDING_DATE is the last date  on which this content LLM Vector was created
                        {"name": "vector_embedding_date", "type": "float" , "optional": True, "index": False},
                    ]

                })

                self.logger.info("Create Collection : %s", json.dumps(create_response))

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
            self.vectorDbClient.collections[self.collection_name].documents.create(content_chunk_map_record)
            self.logger.info("Completed inserting vector record")
        except:
            self.logger.error("Could not insert the record in typesense")
            self.logger.error(json.dumps(content_chunk_map_record))

    def deleteAll(self):
        #delete all rows for the content_site_name 
        filter_by_conditions = 'content_site_name:=' + self.content_site_name
        search_parameters= {
            'q': self.content_site_name,
            'query_by': 'content_site_name',
            'include_fields': 'content_path',
            'filter_by':filter_by_conditions
        }
        try:
            response_del = self.vectorDbClient.collections[self.collection_name].documents.delete(search_parameters)
            self.logger.debug("Deleted rows from %s", self.collection_name)   
            self.logger.debug(json.dumps(response_del))
        except: 
            self.logger.error("Could not deleteAll for %s",self.collection_name)   
            self.logger.erro(json.dumps(search_parameters))

    def search(self,content_site_name,vector_embedding, limit_hits, input_text_query = ''):
        
        vector_as_string = ','. join(str(e) for e in vector_embedding)
        include_text_results = False
        if len(input_text_query) > 0 :
            self.logger.debug('Will do multisearch, vector and text')
            include_text_results = True
            search_requests = {
                    'searches': [
                    {
                        'collection': self.collection_name,
                        'q' : '*',
                        'vector_query': 'vector_embedding:([' + vector_as_string + '])',
                    },
                    {
                        'collection': self.collection_name,
                        'q': input_text_query,
                        'query_by': 'text_chunk,content_path,title',
                        'sort_by': '_text_match:desc'
                    }
                    ]
                }
        else:
            search_requests = {
                    'searches': [
                    {
                        'collection': self.collection_name,
                        'q' : '*',
                        'vector_query': 'vector_embedding:([' + vector_as_string + '])',
                    },
                    ]
                }

        common_search_params =  {
                'per_page': limit_hits,
                #'exclude_fields': 'vector_embedding',
                'filter_by': 'content_site_name:='  + content_site_name
        }

        search_results = self.vectorDbClient.multi_search.perform(search_requests, common_search_params)

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

        json_results = {} #Dict
        json_results['results'] = []

        self.logger.debug('Received Typesense Search Results:')
        self.logger.debug(json.dumps(search_results))

        semantic_results = {} #Dict
        text_results = {} #Dict
        semantic_hits = []
        text_hits = []

        no_of_semantic_hits = len(search_results['results'][0]['hits'])
        semantic_results['found'] = no_of_semantic_hits
        semantic_results['type'] = 'semantic'

        i = 0
        while i < no_of_semantic_hits:
            result = {} #Dict to hold a single result
            
            chunk_map_record = search_results['results'][0]['hits'][i]['document']
            
            result['match_score'] =  search_results['results'][0]['hits'][i]['vector_distance']
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
            i = i + 1 

        semantic_results['hits'] = semantic_hits
        json_results['results'].append(semantic_results)
        
        if include_text_results == True:
            
            no_of_text_hits = len(search_results['results'][1]['hits'])
            text_results['found'] = no_of_text_hits
            text_results['type'] = 'text'
            i = 0
            while i < no_of_text_hits:
                result = {} #Dict to hold a single result
                
                chunk_map_record = search_results['results'][1]['hits'][i]['document']
                
                result['match_score'] =  search_results['results'][1]['hits'][i]['text_match']
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
                i = i + 1 

            text_results['hits'] = text_hits
            json_results['results'].append(text_results)

        
        return json_results

    


