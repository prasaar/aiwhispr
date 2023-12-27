import os
import sys
import io
import uuid
import time
from datetime import datetime, timedelta
import pathlib
import json
import psycopg2
import string
import random



curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb

import aiwhisprConstants 

import logging

class createVectorDb(vectorDb):
    
    vectordb_user:str
    vectordb_password:str
    vectordb_dbname:str
    vectordb_shards_num:int
    vectordb_vector_dim:int
    
    

    def __init__(self,vectordb_config:{}, content_site_name:str,src_path:str,src_path_for_results:str):    
        self.logger = logging.getLogger(__name__)
        
        vectorDb.__init__(self,
                          vectordb_config = vectordb_config,
                          content_site_name = content_site_name,
                          src_path = src_path,
                          src_path_for_results = src_path_for_results,
                          module_name = 'postgresVectorDb')

        self.vectordb_hostname = vectordb_config['api-address']
        self.vectordb_portnumber = vectordb_config['api-port']
        self.vectordb_user = vectordb_config['user']
        self.vectordb_password = vectordb_config['password']
        try:
            self.vectordb_dbname = vectordb_config['db-name']
        except:
            self.logger.error("db-name not provided for Postgres PGVector")  
            sys.exit()
         
        try:
            self.vectordb_vector_dim = int(vectordb_config['vector-dim'])
        except:
            self.logger.error("Postgres PGVector requires vector dimensions to be provided. Have you set this as vector-dim=<int> ?")
            sys.exit()        
        
        if 'collection-name' in vectordb_config:
            self.collection_name = vectordb_config['collection-name']
        else:
            self.setDefaultCollectionName()
        
        self.efValue = 64 #PGVector specific parameter
        self.Mvalue = 16 #PGVector specific parameter
    
    def get_random_string(self,length):
        # With combination of lower and upper case
        result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
        # print random string
        return result_str

    def list_to_string(self,my_list):
        if len(my_list) == 0:
            return '[]'
        else:
            return_str = "["
            count = 0
            while count < len(my_list):
                return_str = return_str + str(my_list[count])
                count = count  + 1
                if count < len(my_list):
                    return_str = return_str + ","
                else: #last float in array processed
                    return_str = return_str + "]"
        return return_str
    
    def str_to_float_list(self,my_str):
        if len(my_str) == 0:
            return []
        else:   
            float_list_str = (my_str.replace("[","").replace("]","")).split(",")
            return_float_list =[]
            count = 0
            while count < len(float_list_str):
                return_float_list.append( float(float_list_str[count]) )
                count = count + 1
            return return_float_list


    def remove_punctuations(self,word):
        qword = word
        qword = qword.replace(";", "")
        qword = qword.replace(",", "")
        qword = qword.replace("'", "")
        qword = qword.replace("-", "")
        qword = qword.replace(":", "")
        qword = qword.replace('"', "")
        qword = qword.replace("'", "")
        qword = qword.replace("#", "")
        qword = qword.replace("!", "")
        qword = qword.replace("@", "")
        qword = qword.replace("%", "")
        qword = qword.replace("&", "")
        qword = qword.replace("*", "")
        qword = qword.replace("(", "")
        qword = qword.replace(")", "")
        qword = qword.replace("[", "")
        qword = qword.replace("]", "")
        qword = qword.replace("{", "")
        qword = qword.replace("}", "")
        qword = qword.replace("?", "")
        qword = qword.replace("+", "")
        qword = qword.replace("-", "")
        qword = qword.replace("~", " ")
        qword = qword.replace("`", "")
        qword = qword.replace("|", "")
        qword = qword.replace("^", "")
        return qword
        
        
            
    def testConnect(self):
        #First create the connection
        try:
            self.logger.debug("Creating a Postgres Connection")
            
            self.vectordDbClient = psycopg2.connect(
                user= self.vectordb_user,
                password= self.vectordb_password ,
                database = self.vectordb_dbname,
                host= self.vectordb_hostname,
                port= self.vectordb_portnumber,
            )
        

            self.logger.info("Connected to Postgres  at host: %s , port: %s , user: %s , db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user, self.vectordb_dbname )
            self.logger.debug("Connected to Postgres at host: %s , port: %s , user: %s , password: %s, db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user,self.vectordb_password,self.vectordb_dbname )               
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not connect to Postgres at host: %s , port: %s , user: %s , db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user, self.vectordb_dbname )
            raise
        #Now check if the collection already exists, if not then recreate it
        collectionExistsFlag=False
        try:
            sqltableexists = "SELECT EXISTS ( SELECT 1 FROM pg_tables WHERE tablename = '"
            sqltableexists = sqltableexists + self.collection_name.lower() + "' ) AS table_existence"
            with self.vectordDbClient as conn:
                with conn.cursor() as cur:
                    cur.execute(sqltableexists)
                    row = cur.fetchone()
                    if row[0] == True:
                        collectionExistsFlag = True
        except Exception as err:
            self.logger.error("Error when checking if collection %s exists", self.collection_name)

        if collectionExistsFlag == True:
            self.logger.info("Collection %s already exists", self.collection_name)
        

    def connect(self):

        #First create the connection
        try:
            self.logger.debug("Creating a Postgres Connection")
            
            self.vectordDbClient = psycopg2.connect(
                user= self.vectordb_user,
                password= self.vectordb_password ,
                database = self.vectordb_dbname,
                host= self.vectordb_hostname,
                port= self.vectordb_portnumber,
            )
            
            self.logger.info("Connected to Postgres at host: %s , port: %s , user: %s , db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user, self.vectordb_dbname )
            self.logger.debug("Connected to Postgres at host: %s , port: %s , user: %s , password: %s, db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user,self.vectordb_password,self.vectordb_dbname )               
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not connect to Postgres at host: %s , port: %s , user: %s , db: %s",self.vectordb_hostname,self.vectordb_portnumber,self.vectordb_user, self.vectordb_dbname )
            raise
        #Now check if the collection already exists, if not then recreate it
        collectionExistsFlag=False
        try:
            sqltableexists = "SELECT EXISTS ( SELECT 1 FROM pg_tables WHERE tablename = '"
            sqltableexists = sqltableexists + self.collection_name.lower() + "' ) AS table_existence"
            with self.vectordDbClient as conn:
                with conn.cursor() as cur:
                    cur.execute(sqltableexists)
                    row = cur.fetchone()
                    if row[0] == True:
                        collectionExistsFlag = True
        except Exception as err:
            self.logger.error("Error when checking if collection %s exists", self.collection_name)
            sys.exit()

        if collectionExistsFlag == True:
            self.logger.info("collection %s exists", self.collection_name)
        else:
            try:
                self.logger.info("Postgres collection %s does not exist , so we will create it", self.collection_name)
                #1. Create the table
                sqlcommand = "CREATE TABLE " + self.collection_name
                sqlcommand = sqlcommand + "( id VARCHAR(50) PRIMARY KEY,"
                sqlcommand = sqlcommand + "content_site_name VARCHAR(2048) NOT NULL,"
                sqlcommand = sqlcommand + "src_path VARCHAR(2048) NOT NULL,"
                sqlcommand = sqlcommand + "src_path_for_results VARCHAR(2048) NULL,"
                sqlcommand = sqlcommand + "content_path VARCHAR(2048) NULL,"
                sqlcommand = sqlcommand + "last_edit_date BIGINT NULL,"
                sqlcommand = sqlcommand + "tags VARCHAR(2048) NULL,"
                sqlcommand = sqlcommand + "title VARCHAR(2048) NULL,"
                sqlcommand = sqlcommand + "text_chunk TEXT NULL,"
                sqlcommand = sqlcommand + "text_chunk_no int NOT NULL,"
                sqlcommand = sqlcommand + "vector_embedding_date BIGINT NOT NULL,"
                sqlcommand = sqlcommand + "vector_embedding vector(" + str(self.vectordb_vector_dim) +") NOT NULL"
                sqlcommand = sqlcommand + ")"
                
                self.logger.debug("Creating Postgres table for vector embeddings with command {%s}", sqlcommand)
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                self.logger.error("Error when creating query to create tab;e")
                raise
            
            #2. Create Collection(Table)
            try:
                with self.vectordDbClient as conn:
                    with conn.cursor() as cur:
                        cur.execute(sqlcommand)
                    self.logger.info("Created collection %s",  self.collection_name )
            except Exception as err:
                self.logger.error("Could not create collection %s in Postgres",  self.collection_name )
                print(f"Unexpected {err=}, {type(err)=}")
                raise

            #3 Now Alter the table to add a textsearch vector column. This is new in Postgres 12
            altersql = "ALTER TABLE " + self.collection_name + " ADD COLUMN text_chunk_tsvector tsvector GENERATED ALWAYS AS (to_tsvector('english', text_chunk)) STORED " 
            self.logger.debug("Altering the Postgres table to add a tsvector column  ts_text_chunk{%s}", altersql)
            try:
                with self.vectordDbClient as conn:
                    with conn.cursor() as cur:
                        cur.execute(altersql)
                    self.logger.info("Altered collection %s",  self.collection_name )
            except Exception as err:
                self.logger.error("Could not alter collection %s in Postgres",  self.collection_name )
                print(f"Unexpected {err=}, {type(err)=}")
                raise

            #4. Create index
            try:
                idx1_name = self.collection_name + "_idx1_" + self.get_random_string(4)
                idx2_name = self.collection_name + "_idx2_" + self.get_random_string(4)
                idxg_name = self.collection_name + "_idxg_" + self.get_random_string(4)

                idx1_sql = "CREATE INDEX " + idx1_name + " ON " + self.collection_name + "(content_site_name)"
                idx2_sql = "CREATE INDEX " + idx2_name + " ON " + self.collection_name + "(content_path)"
                idxg_sql = "CREATE INDEX " + idxg_name + " ON " + self.collection_name + " USING GIN (text_chunk_tsvector);"
                idxv_sql = "CREATE INDEX ON " + self.collection_name + " USING hnsw (vector_embedding vector_l2_ops)"
                
                try:
                    self.logger.debug(idx1_sql)
                    cur1 = self.vectordDbClient.cursor()
                    cur1.execute(idx1_sql)
                    self.logger.info("Created index %s on column content_site_name", idx1_name )
                except Exception as err:
                    self.logger.error("Could not create index %s on column content_site_name",  idx1_name )
                    print(f"Unexpected {err=}, {type(err)=}")
                    self.vectordDbClient.rollback()
                    raise
                else:
                    self.vectordDbClient.commit()

                try:
                    self.logger.debug(idx2_sql)
                    cur2 = self.vectordDbClient.cursor()
                    cur2.execute(idx2_sql)
                    self.logger.info("Created index %s on column src_path", idx2_name )
                except Exception as err:
                    self.logger.error("Could not create index %s on column src_path",  idx2_name )
                    print(f"Unexpected {err=}, {type(err)=}")
                    self.vectordDbClient.rollback()
                    raise
                else:
                    self.vectordDbClient.commit()
 
                try:
                    self.logger.debug(idxv_sql)
                    cur3 = self.vectordDbClient.cursor()
                    cur3.execute(idxv_sql)
                    self.logger.info("Created hnsw index on column vector_embedding")
                except Exception as err:
                    self.logger.error("Could not create hnsw index on column vector_embedding" )
                    print(f"Unexpected {err=}, {type(err)=}")
                    self.vectordDbClient.rollback()
                    raise
                else:
                    self.vectordDbClient.commit()

                try:
                    self.logger.debug(idxg_sql)
                    cur4 = self.vectordDbClient.cursor()
                    cur4.execute(idxg_sql)
                    self.logger.info("Created index %s on column text_chunk_tsvector", idxg_name )
                except Exception as err:
                    self.logger.error("Could not create index %s on column text_chunk_tsvector",  idxg_name )
                    print(f"Unexpected {err=}, {type(err)=}")
                    self.vectordDbClient.rollback()
                    raise
                else:
                    self.vectordDbClient.commit()

            except Exception as err:
                self.logger.error("Could not create index in Postgres")
                print(f"Unexpected {err=}, {type(err)=}")
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

            #converted into str fields         
            f_last_edit_date= str(last_edit_date)
            f_text_chunk_no= str(text_chunk_no)
            f_vector_embedding_date= str(vector_embedding_date)
            f_vector_embedding= self.list_to_string(vector_embedding)

            text_words = text_chunk.split()
            count = 0
            f_text_chunk = ""
            while count < len(text_words):
                word = self.remove_punctuations(text_words[count])
                count = count + 1
                if count < len(text_words):
                    f_text_chunk = f_text_chunk + word + ' '
                else: #last word processed
                    f_text_chunk = f_text_chunk + word

            #Create the insert command
            sqlcommand = "INSERT INTO " + self.collection_name
            sqlcommand = sqlcommand + " (id,"
            sqlcommand = sqlcommand + "content_site_name,"
            sqlcommand = sqlcommand + "src_path,"
            sqlcommand = sqlcommand + "src_path_for_results,"
            sqlcommand = sqlcommand + "content_path,"
            sqlcommand = sqlcommand + "last_edit_date,"
            sqlcommand = sqlcommand + "tags,"
            sqlcommand = sqlcommand + "title,"
            sqlcommand = sqlcommand + "text_chunk,"
            sqlcommand = sqlcommand + "text_chunk_no,"
            sqlcommand = sqlcommand + "vector_embedding_date,"
            sqlcommand = sqlcommand + "vector_embedding"
            sqlcommand = sqlcommand + ")"
            sqlcommand = sqlcommand + " values("
            sqlcommand = sqlcommand + "'" + id + "',"
            sqlcommand = sqlcommand + "'" + self.content_site_name + "',"
            sqlcommand = sqlcommand + "'" + self.src_path + "',"
            sqlcommand = sqlcommand + "'" + self.src_path_for_results + "',"
            sqlcommand = sqlcommand + "'" + content_path + "',"
            sqlcommand = sqlcommand +  f_last_edit_date + ","
            sqlcommand = sqlcommand + "'" + tags + "',"
            sqlcommand = sqlcommand + "'" + title + "',"
            sqlcommand = sqlcommand + "'" + f_text_chunk + "',"
            sqlcommand = sqlcommand +  f_text_chunk_no + ","
            sqlcommand = sqlcommand + f_vector_embedding_date + ","
            sqlcommand = sqlcommand + "'" + f_vector_embedding + "'"
            sqlcommand = sqlcommand + ")"
            
            self.logger.debug(sqlcommand)
            with self.vectordDbClient as conn:
                with conn.cursor() as cur:
                    cur.execute(sqlcommand)
                self.logger.debug("Inserting a record in Postgres vectordb{%s} with vector embedding of size{%d}", sqlcommand, len(vector_embedding))       
                self.logger.info("Completed inserting vector record")
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Could not insert the record in Postgres")
            raise

    def deleteAll(self):
        #delete all rows for the content_site_name
        sqlcommand_where = " WHERE content_site_name = '" + self.content_site_name + "'"

        try:
            delete_sql = "DELETE FROM " + self.collection_name + sqlcommand_where
            self.logger.debug(delete_sql)
            with self.vectordDbClient as conn:
                with conn.cursor() as cur:
                    cur.execute(delete_sql)
                self.logger.info("Deleted rows from table{%s} for content_site_name{%s}", self.collection_name,self.content_site_name)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Error when deleting rows from collection %s", self.collection_name)
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

        include_text_results = False
        if len(input_text_query) > 0 :
            self.logger.debug('Will do multisearch, vector and text')
            include_text_results = True
        
        text_words = input_text_query.split()
        tsquery_str = ""
        count = 0
        while count < len(text_words):
            word = self.remove_punctuations(text_words[count])
            count = count + 1
            if count < len(text_words):
                tsquery_str = tsquery_str + word + ' '
            else: #last word processed
                tsquery_str = tsquery_str + word  


        vector_embedding_str_for_pgvector  = "'" + self.list_to_string(vector_embedding) + "'"
        
        sqlcommand_common = "SELECT id, content_site_name, content_path, src_path, src_path_for_results,tags, title, text_chunk, text_chunk_no, last_edit_date, vector_embedding_date, vector_embedding,"
        sqlcommand_vector_score = " cosine_distance(" + vector_embedding_str_for_pgvector + ", vector_embedding) as rank"
        sqlcommand_text_score = " ts_rank(text_chunk_tsvector,websearch_to_tsquery('" + tsquery_str +  "')) as rank" #Text match scores are not available explicitly
        
        sqlcommand_from =  " FROM " + self.collection_name
        sqlcommand_where = " WHERE content_site_name = '" +  content_site_name + "'"
        
        sql_order_by_vector_rank = " ORDER BY vector_embedding <=> " + vector_embedding_str_for_pgvector + " "
        
        sqlcommand_where_text_search = " AND  ( text_chunk_tsvector @@ websearch_to_tsquery('" + tsquery_str +  "') = True ) "
        sql_order_by_text_rank = " ORDER BY rank DESC"
        
        sql_limit_hits =  " LIMIT " + str(limit_hits)
        
        
        
        


        json_results = {} #Dict
        json_results['results'] = []
        semantic_results = {} #Dict
        text_results = {} #Dict
        
        text_hits = []


        #First always run the semantic search
        try:
            semanticsearchsql = sqlcommand_common + sqlcommand_vector_score + sqlcommand_from + sqlcommand_where + sql_order_by_vector_rank + sql_limit_hits
            self.logger.debug(semanticsearchsql)
            cur1 = self.vectordDbClient.cursor()
            cur1.execute(semanticsearchsql)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Error when running semantic search query")
            raise
        else:
            semantic_hits = []
            no_of_semantic_hits = 0
            row = cur1.fetchone()
            while row is not None:
                no_of_semantic_hits = no_of_semantic_hits + 1
                result = {}
                result['id'] = row[0]
                result['content_site_name'] = row[1]
                result['content_path'] = row[2]
                result['src_path'] = row[3]
                result['src_path_for_results'] = row[4]
                result['tags'] = row[5]
                result['title'] = row[6]
                result['text_chunk'] = row[7]
                result['text_chunk_no'] = row[8]
                result['last_edit_date'] = row[9]
                result['vector_embedding_date'] = row[10]
                result['vector_embedding'] = self.str_to_float_list(row[11])
                result['match_score'] =  row[12]
                semantic_hits.append(result)
                row = cur1.fetchone()
                
            semantic_results['found'] = no_of_semantic_hits
            self.logger.debug("Postgres PGVector: semantic search  found %d results", no_of_semantic_hits)
            semantic_results['type'] = 'semantic'
            semantic_results['hits'] = semantic_hits
            json_results['results'].append(semantic_results)
            print("SEMANTIC-RESULTS:", semantic_results)


        if include_text_results == True:
            try:
                textsearchsql = sqlcommand_common + sqlcommand_text_score + sqlcommand_from + sqlcommand_where + sqlcommand_where_text_search + sql_order_by_text_rank + sql_limit_hits
                self.logger.debug(textsearchsql)
                cur2 = self.vectordDbClient.cursor()
                cur2.execute(textsearchsql)
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                self.logger.error("Error when running text search query")
                raise
            else:
                text_hits = []
                no_of_text_hits = 0
                row = cur2.fetchone()
                while row is not None:
                    no_of_text_hits = no_of_text_hits + 1
                    result = {}
                    result['id'] = row[0]
                    result['content_site_name'] = row[1]
                    result['content_path'] = row[2]
                    result['src_path'] = row[3]
                    result['src_path_for_results'] = row[4]
                    result['tags'] = row[5]
                    result['title'] = row[6]
                    result['text_chunk'] = row[7]
                    result['text_chunk_no'] = row[8]
                    result['last_edit_date'] = row[9]
                    result['vector_embedding_date'] = row[10]
                    result['vector_embedding'] = self.str_to_float_list(row[11])
                    result['match_score'] =  row[12]
                    text_hits.append(result)
                    row = cur2.fetchone()
                    
                text_results['found'] = no_of_text_hits
                self.logger.debug("Postgres PGVector: text full search  found %d results", no_of_text_hits)
                text_results['type'] = 'text'
                text_results['hits'] = text_hits
                json_results['results'].append(text_results)

        return json_results

    def getExtractedText(self,content_site_name:str,content_path:str):
        sqlcommand_select = "SELECT content_site_name, content_path, text_chunk_no, text_chunk"
        sqlcommand_from =  " FROM " + self.collection_name
        sqlcommand_where = " WHERE content_site_name = '" + content_site_name + "' AND content_path = '" + content_path +"'"
        sqlcommand_order_by = " ORDER BY content_site_name, content_path, text_chunk_no"
        extracted_text=""
        try:
            sqlcommand = sqlcommand_select + sqlcommand_from + sqlcommand_where + sqlcommand_order_by
            self.logger.debug(sqlcommand)
            cur = self.vectordDbClient.cursor()
            cur.execute(sqlcommand)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.logger.error("Error when running  search query to extract text")
            raise
        else:
            row = cur.fetchone()
            while row is not None:
                extracted_text = extracted_text + row[3]
                row = cur.fetchone()
    
        return extracted_text
    
 
        

