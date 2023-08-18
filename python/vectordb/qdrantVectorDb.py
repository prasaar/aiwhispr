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

    def __init__(self,vectordb_hostname,vectordb_portnumber, vectordb_key, content_site_name:str,src_path:str,src_path_for_results:str):
        vectorDb.__init__(self,
                          vectordb_hostname = vectordb_hostname,
                          vectordb_portnumber = vectordb_portnumber, 
                          vectordb_key = vectordb_key, 
                          content_site_name = content_site_name,
                          src_path = src_path,
                          src_path_for_results = src_path_for_results)
        self.vectorDbClient:QdrantClient
        self.logger = logging.getLogger(__name__)

    def connect(self):

        #First create the connection
        try:
            self.logger.debug("Creating a Qdrant Connection")
            if self.vectordb_hostname == ':memory:' :
                self.logger.debug('Creating Qdrant in memory')
                self.vectorDbClient = QdrantClient(":memory:") # Create in-memory Qdrant instance

            elif self.vectordb_hostname[0:5] == 'path:'  :
                self.logger.debug("Creating Qdrant in specified local path: %s", self.vectordb_hostname[5:] )

                self.vectorDbClient = QdrantClient(path=(self.vectordb_hostname)[5:]) #Create local-db Qdrant instance

            elif self.vectordb_hostname[0:6] == 'https:'  or self.vectordb_hostname[0:5] == 'http:' :
                self.logger.debug("Create Qdrant http(s) connection to hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
                if (len(self.vectordb_key) > 0 ): 
                    self.vectorDbClient = QdrantClient(url=self.vectordb_hostname + ':' + self.vectordb_portnumber,api_key=self.vectordb_key) #Create connection to http/https host with key
                else:
                    self.vectorDbClient = QdrantClient(url=self.vectordb_hostname + ':' + self.vectordb_portnumber) #Create connection to http/http host without key

            else: #Assuming IP/hostname with PortNumber
                self.logger.debug("Create Qdrant http connection to hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)
                if (len(self.vectordb_key) > 0 ): 
                    self.vectorDbClient = QdrantClient(url='http:' + self.vectordb_hostname + ':' + self.vectordb_portnumber,api_key=self.vectordb_key) #Create connection with key
                else:
                    self.vectorDbClient = QdrantClient(url='http:' + self.vectordb_hostname + ':' + self.vectordb_portnumber) #Create connection without key
        except:
            self.logger.error("Could not create Qdrant connection to Qdrant Server hostname: %s , portnumber: %s with key: %s", self.vectordb_hostname, self.vectordb_portnumber, self.vectordb_key)

        #Now check if the collection already eixts, if not then recreate it
        collectionExistsFlag =  False
        try:
            collections_list = self.vectorDbClient.get_collections()
            for collection in collections_list.collections :
                if collection.name == 'content_chunk_map' :
                    collectionExistsFlag = True
                    break
        except:
            self.logger.error("Could not get collections list from Qdrant")

        if collectionExistsFlag == True:
            self.logger.info('collection content_chunk_map exists')
        else:
            self.logger.info("Qdrant collection content_chunk_map does not exist , so we will create it")
            #create the collection in Qdrant
            #We are not creating an 'id' (unique id)  field. It will be provided in insert statements by the client
            #We expect id to be in the format <site-name>/<extracted-file_directory-name>/<chunk-files-directory>/<chunk-id>
            create_response = self.vectorDbClient.create_collection(
                collection_name =  "content_chunk_map",
                vectors_config= models.VectorParams(size=768, distance=models.Distance.COSINE,on_disk = True), 
                on_disk_payload = True )
                 
            if(create_response == True):
                self.logger.info("Created collection, now creating payload index")
                try: 
                    self.vectorDbClient.create_payload_index(collection_name="content_chunk_map", 
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
                collection_name="content_chunk_map",
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
                collection_name="content_chunk_map",
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
            self.logger.debug("Deleted rows from content_chunk_map")   
        except: 
            self.logger.error("Could not deleteAll for content_chunk_map")


    def search(self,content_site_name,vector_embedding, limit_hits, input_text_query = ''):
        #vector_as_string = ','. join(str(e) for e in vector_embedding)
        search_results = client.search(
            collection_name="content_chunk_map",
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
        )
        return search_results
