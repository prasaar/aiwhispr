import os
import sys
import io
import uuid
import time
from datetime import datetime, timedelta
import pathlib
import json
from qdrant_client import models, QdrantClient

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
                          module_name = 'qdrantVectorDb')

        self.vectordb_hostname = vectordb_config['api-address']
        self.vectordb_portnumber = vectordb_config['api-port']
        self.vectordb_key = vectordb_config['api-key']

        if 'collection-name' in vectordb_config:
            self.collection_name = vectordb_config['collection-name']
        else:
            self.setDefaultCollectionName()
        
        self.vectorDbClient:QdrantClient
        self.logger = logging.getLogger(__name__)

        
    def connect(self):

        #First create the connection
        try:
            self.logger.debug("Creating a Qdrant Connection")
            if self.vectordb_hostname[0:6] == 'https:'  or self.vectordb_hostname[0:5] == 'http:' :
                self.logger.debug("Create Qdrant http(s) connection to hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
                if (len(self.vectordb_key) > 0 ): 
                    self.vectorDbClient = QdrantClient(url=self.vectordb_hostname + ':' + self.vectordb_portnumber,api_key=self.vectordb_key) #Create connection to http/https host with key
                else:
                    self.vectorDbClient = QdrantClient(url=self.vectordb_hostname + ':' + self.vectordb_portnumber) #Create connection to http/http host without key
            else: #Assuming IP/hostname with PortNumber
                self.logger.debug("Create Qdrant http connection to hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
                if (len(self.vectordb_key) > 0 ): 
                    connect_url = 'http://' + self.vectordb_hostname + ':' + self.vectordb_portnumber
                    self.vectorDbClient = QdrantClient(url=connect_url,api_key=self.vectordb_key) #Create connection with key
                else:
                    connect_url = 'http://' + self.vectordb_hostname + ':' + self.vectordb_portnumber
                    self.vectorDbClient = QdrantClient(url=connect_url) #Create connection without key
        except:
            self.logger.error("Could not create Qdrant connection to Qdrant Server hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)

        #Now check if the collection already exists, if not then recreate it
        collectionExistsFlag =  False
        try:
            collections_list = self.vectorDbClient.get_collections()
            for collection in collections_list.collections :
                if collection.name == self.collection_name :
                    collectionExistsFlag = True
                    break
        except:
            self.logger.error("Could not get collections list from Qdrant")

        if collectionExistsFlag == True:
            self.logger.info('collection %s exists', self.collection_name)
        else:
            self.logger.info("Qdrant collection %s does not exist , so we will create it", self.collection_name)
            #create the collection in Qdrant
            #We are not creating an 'id' (unique id)  field. It will be provided in insert statements by the client
            #We expect id to be in the format <site-name>/<extracted-file_directory-name>/<chunk-files-directory>/<chunk-id>
            create_response = self.vectorDbClient.create_collection(
                collection_name =  self.collection_name,
                vectors_config= models.VectorParams(size=768, distance=models.Distance.COSINE,on_disk = True), 
                on_disk_payload = True )
                 
            if(create_response == True):
                self.logger.info("Created collection, now creating payload index")
                try: 
                    self.vectorDbClient.create_payload_index(collection_name=self.collection_name, 
                                field_name="text_chunk", 
                                field_schema=models.TextIndexParams(
                                type="text",
                                tokenizer=models.TokenizerType.WORD,
                                min_token_len=2,
                                max_token_len=15,
                                lowercase=True,
                            )
                    )
                except:
                    self.logger.error("Could not create payload index")

            else:
                self.logger.error("Could not create collection")


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
            content_chunk_map_record = {
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

            self.logger.debug("Inserting a record in Qdrant vectordb: %s with vector embedding of size: %d", json.dumps(content_chunk_map_record), len(vector_embedding) )

            self.vectorDbClient.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=id,
                        payload= content_chunk_map_record,
                        vector=vector_embedding,
                    ),
                ]
            )
        except:
            self.logger.error("Could not insert the record in Qdrant")

    def deleteAll(self):
        #delete all rows for the content_site_name 
        try:
            response_del = self.vectorDbClient.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="content_site_name",
                                match=models.MatchValue(value=self.content_site_name),
                            ),
                        ],
                    )
                ),
            )
            self.logger.debug("Deleted rows from %s", self.collection_name)   
        except: 
            self.logger.error("Could not deleteAll for %s", self.collection_name)


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

        #We will first do a semantic search
        
        search_results = self.vectorDbClient.search(
            collection_name=self.collection_name,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="content_site_name",
                        match=models.MatchValue(
                            value=content_site_name,
                        ),
                    )
                ]
            ),
            search_params=models.SearchParams(
                hnsw_ef=128,
                exact=False
            ),
            query_vector=vector_embedding,
            limit=limit_hits,
            with_payload=True
        )

       
        json_results = {} #Dict
        json_results['results'] = []

        semantic_results = {} #Dict
        text_results = {} #Dict
        semantic_hits = []
        text_hits = []

        no_of_semantic_hits = len(search_results)
        semantic_results['found'] = no_of_semantic_hits
        semantic_results['type'] = 'semantic'
        self.logger.debug("Qdrant: semantic search  found %d results", no_of_semantic_hits)
        i = 0
        while i < no_of_semantic_hits:
            result = {} #Dict to hold a single result
            
            chunk_map_record = search_results[i].payload
            
            result['id'] = search_results[i].id
            result['match_score'] =  search_results[i].score
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
            search_results = self.vectorDbClient.search(
            collection_name=self.collection_name,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="content_site_name",
                        match=models.MatchValue(
                            value=content_site_name,
                        )
                    ),
                    models.FieldCondition(
                        key="text_chunk",
                        match=models.MatchText(
                            text=input_text_query  ##Match on the input text query
                        )
                    )

                ]
            ),
            query_vector=vector_embedding,
            limit=limit_hits,
            with_payload=True
            )

            no_of_text_hits = len(search_results)
            text_results['found'] = no_of_text_hits
            text_results['type'] = 'text'
            self.logger.debug("Qdrant: text search  found %d results for input query: %s",no_of_text_hits, input_text_query)
            i = 0
            while i < no_of_text_hits:
                result = {} #Dict to hold a single result
                
                chunk_map_record = search_results[i].payload
                
                result['id'] = search_results[i].id
                result['match_score'] =  search_results[i].score
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
                
                text_hits.append(result)
                i = i + 1 

            text_results['hits'] = text_hits
            json_results['results'].append(text_results)


        return json_results
