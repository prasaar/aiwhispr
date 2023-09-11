import os
import sys
import io
import uuid
import time
from datetime import datetime, timedelta
import pathlib
import json
import pymilvus


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb

import aiwhisprConstants 

import logging

class createVectorDb(vectorDb):
    
    vectordb_collection_name:str
    vectordb_user:str
    vectordb_password:str
    vectordb_dbname:str
    vectordb_shards_num:int
    vectordb_vector_dim:int

    def __init__(self,vectordb_config:{}, content_site_name:str,src_path:str,src_path_for_results:str):    
        self.logger = logging.getLogger(__name__)
        self.vectordb_collection_name = "content_chunk_map"
        
        vectorDb.__init__(self,
                          vectordb_config = vectordb_config,
                          content_site_name = content_site_name,
                          src_path = src_path,
                          src_path_for_results = src_path_for_results,
                          module_name = 'milvusVectorDb')

        self.vectordb_hostname = vectordb_config['api-address']
        self.vectordb_portnumber = vectordb_config['api-port']
        self.vectordb_user = vectordb_config['user']
        self.vectordb_password = vectordb_config['password']
        if 'db-name' in  vectordb_config:
            self.vectordb_dbname = vectordb_config['db-name']
        else:
            self.vectordb_dbname = "default"  
        
        if 'shards-num' in vectordb_config:
            self.vectordb_shards_num = int(vectordb_config['shards-num'])
        else:
            self.vectordb_shards_num = 1
 
        try:
            self.vectordb_vector_dim = int(vectordb_config['vector-dim'])
        except:
            self.logger.error("Milvus requires vector dimensions to be provided. Have you set this as vector-dim=<int> ?")
            sys.exit()        
        
        
        

    def connect(self):

        #First create the connection
        try:
            self.logger.debug("Creating a Milvus Connection")
            pymilvus.connections.connect(
                alias="default",         #Alias for the Milvus Server in our connections
                user= self.vectordb_user,
                password= self.vectordb_password ,
                host= self.vectordb_hostname,
                port= self.vectordb_portnumber,
                db_name= self.vectordb_dbname
            )
            self.logger.info("Connected to Milvus at host: %s , port: %s , user: %s , db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user, self.vectordb_dbname )
            self.logger.debug("Connected to Milvus at host: %s , port: %s , user: %s , password: %s, db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user,self.vectordb_password,self.vectordb_dbname )               
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not connect to Milvus at host: %s , port: %s , user: %s , db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user, self.vectordb_dbname )
            raise
        #Now check if the collection already exists, if not then recreate it
        
        try:
            collectionExistsFlag = pymilvus.utility.has_collection(self.vectordb_collection_name)
        except Exception as err:
            self.logger.error("Error when checking if collection %s exists", self.vectordb_collection_name)
            sys.exit()

        if collectionExistsFlag == True:
            self.logger.info("collection %s exists", self.vectordb_collection_name)
        else:
            self.logger.info("Milvus collection %s does not exist , so we will create it", self.vectordb_collection_name)
            #create the fields, then schema, then collection, then index
            #1. Create the fields
            id = pymilvus.FieldSchema(   ##UUID
                name="id",
                dtype=pymilvus.DataType.VARCHAR,
                is_primary=True,
                max_length=36  #32 character hex uuid with 4 "-" 
                )
            content_site_name=pymilvus.FieldSchema(
                name="content_site_name",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=256
                )
            src_path=pymilvus.FieldSchema(
                name="src_path",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=1024
                )
            src_path_for_results=pymilvus.FieldSchema(
                name="src_path_for_results",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=1024
                )
            content_path=pymilvus.FieldSchema(
                name="content_path",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=3072
                )
            last_edit_date=pymilvus.FieldSchema(
                name="last_edit_date",
                dtype=pymilvus.DataType.DOUBLE
                )
            tags=pymilvus.FieldSchema(
                name="tags",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=1024
                )
            title=pymilvus.FieldSchema(
                name="title",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=1024
                )
            text_chunk=pymilvus.FieldSchema(
                name="text_chunk",
                dtype=pymilvus.DataType.VARCHAR,
                max_length=32750
                )
            text_chunk_no=pymilvus.FieldSchema(
                name="text_chunk_no",
                dtype=pymilvus.DataType.INT64
                )
            vector_embedding_date=pymilvus.FieldSchema(
                name="vector_embedding_date",
                dtype=pymilvus.DataType.DOUBLE
                )
            vector_embedding=pymilvus.FieldSchema(
                name="vector_embedding",
                dtype=pymilvus.DataType.FLOAT_VECTOR,
                dim=self.vectordb_vector_dim
            )

            #2.Create the schema
            try:
                schema = pymilvus.CollectionSchema(
                    fields=[id,content_site_name,src_path,src_path_for_results,content_path,last_edit_date,tags,title,text_chunk,text_chunk_no,vector_embedding_date,vector_embedding],
                    description="AIWhispr Content Chunk Map",
                    enable_dynamic_field=False
                )
                self.logger.info("Created schema for Milvus")
            except:
                self.logger.error("Could not create schema for Milvus")
                sys.exit()
            
            #3. Create Collection
            try:
                collection = pymilvus.Collection(
                    name=self.vectordb_collection_name,
                    schema=schema,
                    using='default',
                    shards_num=self.vectordb_shards_num
                    )
                self.logger.info("Created collection %s",  self.vectordb_collection_name )
            except:
                self.logger.error("Could not create collection %s in Milvus",  self.vectordb_collection_name )
                sys.exit()
            
            #4. Create index
            try: 
                index_params = {
                    "metric_type":"IP",
                    "index_type":"DISKANN",
                    "params":{"search_list":1024}
                }
                vectordb_collection = pymilvus.Collection(name = self.vectordb_collection_name)
                vectordb_collection.create_index(
                    field_name="vector_embedding",
                    index_params=index_params
                )

                vectordb_collection.create_index(
                    field_name="text_chunk",
                    index_name="scalar_index_text_chunk",
                )

                vectordb_collection.create_index(
                    field_name="tags",
                    index_name="scalar_index_tags",
                )

                vectordb_collection.create_index(
                    field_name="title",
                    index_name="scalar_index_title",
                )            
            except Exception as err:
                self.logger.error("Could not create index in Milvus")
                raise

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

            #Milvus inserts the record as list of lists. The position determines which field.
            #fields=[id,content_site_name,src_path,src_path_for_results,content_path,last_edit_date,tags,title,text_chunk,text_chunk_no,vector_embedding_date,vector_embedding]
    
            #Inner list is fields
            f_id =[id]
            f_content_site_name=[self.content_site_name]
            f_src_path=[self.src_path]
            f_src_path_for_results=[self.src_path_for_results]
            f_content_path=[content_path]
            f_last_edit_date=[last_edit_date]
            f_tags=[tags]
            f_title=[title]
            f_text_chunk=[text_chunk]
            f_text_chunk_no=[text_chunk_no]
            f_vector_embedding_date=[vector_embedding_date]
            f_vector_embedding=[vector_embedding]

            content_chunk_map_record=[f_id,f_content_site_name,f_src_path,f_src_path_for_results,f_content_path,f_last_edit_date,f_tags,f_title,f_text_chunk,f_text_chunk_no,f_vector_embedding_date,f_vector_embedding]
            vectordb_collection = pymilvus.Collection(name = self.vectordb_collection_name)
            self.logger.debug("Inserting a record in Milvus vectordb %s with vector embedding of size: %d", str(content_chunk_map_record), len(vector_embedding))
            vectordb_collection.insert(content_chunk_map_record)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not insert the record in Milvus")
            raise


    def deleteAll(self):
        #delete all rows for the content_site_name
        # Milvus only supports deleting entities using the primary key
        #So we will first retrieve all the id's and then delete
        continueDeleteFlag  = True
        expr_query = "content_site_name == '" + self.content_site_name + "'"

        try:
            vectordb_collection = pymilvus.Collection(name = self.vectordb_collection_name)
            vectordb_collection.load()
            vectordb_collection.compact()  #We compact the data manually. Milvus has a soft delete, hence we should first compact.
        except:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not load the collection %s ", self.vectordb_collection_name)
            raise
        else:
            try:
                while continueDeleteFlag:
                    self.logger.debug("Querying rows from collection using expression %s", expr_query)
                    #Query any remaining rows
                    res_all_ids = vectordb_collection.query(
                        expr = expr_query,
                        offset = 0,
                        limit = 16384,  #The max limit
                        output_fields = ["id"],
                    )

                    if len(res_all_ids) == 0:
                        continueDeleteFlag = False
                        self.logger.debug("End of deleting rows from collection")
                    else:
                        self.logger.debug("Deleting %d rows from collection", len(res_all_ids))
                        for dict_id in res_all_ids:
                            expr = "id in ['" + dict_id['id'] + "']"
                            vectordb_collection.delete(expr)
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                self.logger.error("Error when deleting rows from collection %s", self.vectordb_collection_name)
                raise

    def search(self,content_site_name,vector_embedding, limit_hits, input_text_query = ''):
      
        """""
        We will not do test search in Milvus. It's not good for text search
        We will send  a JSON Object in the format 
        {"results": [ semantic_results{} ,text_results{}  ]}
       
         semantic_results will be in the  format 
         {
         "found" : int
         "type"  : "semantic"
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
               title:int,
               text_chunk:str,
               text_chunk_no:int,
               last_edit_date:float,
               vector_embedding_date:float,
               match_score: float,
            }
        """""
        #vector_as_string = ','. join(str(e) for e in vector_embedding)

        #load the collection
        try:
            vectordb_collection = pymilvus.Collection(name = self.vectordb_collection_name)
            vectordb_collection.load()
        except:
            self.logger.error("Could not load the collection %s ", self.vectordb_collection_name)
            raise

        expr_query = "content_site_name == '" + self.content_site_name + "'"
        #We will first do a semantic search
        search_params = {
            "metric_type": "IP",
            "offset": 1,
            "ignore_growing": False,
        }

        search_results = vectordb_collection.search(
            data=[vector_embedding],
            anns_field="vector_embedding",
            # the sum of `offset` in `param` and `limit` 
            # should be less than 16384.
            param=search_params,
            limit=limit_hits,
            expr=expr_query,
            # set the names of the fields you want to 
            # retrieve from the search result.
            output_fields=['id', "content_site_name", "content_path", "src_path", "src_path_for_results","tags", "title","text_chunk","text_chunk_no","last_edit_date","vector_embedding_date" ],
            consistency_level="Strong"
        )


        json_results = {} #Dict
        json_results['results'] = []

        semantic_results = {} #Dict
        text_results = {} #Dict
        semantic_hits = []
        text_hits = []

        no_of_semantic_hits = len(search_results[0])
        semantic_results['found'] = no_of_semantic_hits
        semantic_results['type'] = 'semantic'
        self.logger.debug("Milvus: semantic search  found %d results", no_of_semantic_hits)
        i = 0
        while i < no_of_semantic_hits:
            result = {} #Dict to hold a single result
            
            chunk_map_record = search_results[0][i]
            
            result['id'] = chunk_map_record.entity.get('id')
            result['match_score'] =  chunk_map_record.distance
            result['content_site_name'] = chunk_map_record.entity.get('content_site_name')
            result['content_path'] = chunk_map_record.entity.get('content_path')
            result['src_path'] = chunk_map_record.entity.get('src_path')
            result['src_path_for_results'] = self.src_path_for_results
            result['text_chunk'] = chunk_map_record.entity.get('text_chunk')
            result['text_chunk_no'] = chunk_map_record.entity.get('text_chunk_no')
            result['tags'] = chunk_map_record.entity.get('tags')
            result['title'] = chunk_map_record.entity.get('title')
            result['last_edit_date'] = chunk_map_record.entity.get('last_edit_date')
            result['vector_embedding_date'] = chunk_map_record.entity.get('vector_embedding_date')
            
            semantic_hits.append(result)
            i = i + 1 

        semantic_results['hits'] = semantic_hits
        json_results['results'].append(semantic_results)

        #No text results
        text_results['found'] = 0
        text_results['type'] = 'text'
        text_results['hits'] = text_hits
        json_results['results'].append(text_results)

        return json_results