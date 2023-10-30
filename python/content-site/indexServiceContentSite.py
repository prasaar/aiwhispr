import os
import sys
import io
import uuid
import sqlite3
from datetime import datetime, timedelta
import pathlib
import time


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")

from aiwhisprLocalIndex import aiwhisprLocalIndex
from aiwhisprBaseClasses import siteAuth,vectorDb,srcContentSite, baseLlmService
from awsS3Downloader import awsS3Downloader

import initializeContentSite
import initializeVectorDb
import initializeLlmService
import initializeDocumentProcessor

import aiwhisprConstants 

import logging

import multiprocessing as mp
import pickle
import json

indexingServiceQueueHandler=[]
indexingServiceQueue = mp.Queue() 
indexingServiceQueueHandler.append(indexingServiceQueue)

##This function is used by both single process and multiprocess
def indexing_proc(pickle_file_path,process_list = 0,):

    mypid = os.getpid()
    
    try:
        logging.debug("Opening pickle file path %s", pickle_file_path)
        f = open(pickle_file_path, 'rb')   # 'rb' for reading binary file
        self_description = pickle.load(f)     
        f.close()
    except:
        logging.error("PID:{%d} could not read the pickle file at %s", mypid, pickle_file_path )
        sys.exit()

    
    site_auth=siteAuth(auth_type= self_description['site_auth']['auth_type'],
                       index_service_access_key_id=self_description['site_auth']['index_service_access_key_id'])
                       
    #Instantiate the vector db object. This will return a vectorDb derived class based on the module name
    vector_db = initializeVectorDb.initialize(vectordb_module=self_description['vector_db']['module_name'],
                                             vectordb_config = self_description['vector_db']['vectordb_config'], 
                                             content_site_name = self_description['content_site']['content_site_name'],
                                             src_path = self_description['content_site']['src_type'], 
                                             src_path_for_results = self_description['content_site']['src_path_for_results'] 
                                             )
    
    llm_service = initializeLlmService.initialize(llm_service_module = self_description['llm_service']['module_name'], 
                                                  llm_service_config = self_description['llm_service']['llm_service_config'])
                            
    contentSite = initializeContentSite.initialize(content_site_module='indexServiceContentSite',
                                                   src_type=self_description['content_site']['src_type'],
                                                   content_site_name=self_description['content_site']['content_site_name'],
                                                   src_path=self_description['content_site']['src_path'],
                                                   src_path_for_results=self_description['content_site']['src_path_for_results'],
                                                   working_directory=self_description['local']['working_directory'],
                                                   index_log_directory=self_description['local']['index_log_directory'],
                                                   site_auth=site_auth,
                                                   vector_db = vector_db,
                                                   llm_service = llm_service,
                                                   do_not_read_dir_list =  [],    #Empty list, ignored
                                                   do_not_read_file_list = [] )   #Empty list, ignored
    
    contentSite.connect()
    text_chunk_size=contentSite.llm_service.text_chunk_size
    
    # Read list of paths to download from the path_to_download_file_list, 
    #      for each file  get the file suffix and decide if we extract text for vector embeddings
    #          If we decide to process the file then download it, extract text and break the text into chunks
    #              For each text chunk get the vector embedding
    #              Insert the text chunk, associated meta data and vector embedding into the vector database
    
    #Now start reading the queue
    while True:
        logging.info( "PID:{%d} waiting for message", mypid)
        data_recvd = indexingServiceQueueHandler[0].get() 
        logging.info( "PID:{%d} received  message", mypid)
        try: 
            data = data_recvd
        except:
            logging.error("PID:{%d} data_recvd couldnt decode to utf-8", mypid)
        else:
            try:
                content_to_index = json.loads(data) # Load the JSON into Python Object
            except:
                logging.error("PID:{%d} couldnt load into json")
            else:   
                if content_to_index.get("access_key_id") is None:
                    logging.error("PID:{%d} Message %s has no access_key_id", mypid, data)
                else:
                    if content_to_index.get("access_key_id") != site_auth.index_service_access_key_id:
                        logging.error("PID:{%d} Message %s has incorrect access_key_id", mypid, data)
                    else:
                        if content_to_index.get("content_path") is None:
                            logging.error("PID:{%d} Message %s has no content_path", mypid, data)
                        else:
                            content_path_from_src =  content_to_index.get("content_path")

                        if content_to_index.get("text_chunk") is None:
                            logging.error("PID:{%d} Message %s has no text_chunk", mypid, data)
                        else:
                            text_chunk_from_src = content_to_index.get("text_chunk")
                        
                        if content_to_index.get("id") is None:
                            id = contentSite.generate_uuid()
                        else:
                            id = content_to_index.get("id")
                        
                        if content_to_index.get("text_chunk_no") is None:
                            text_chunk_no = 1
                        else:
                            text_chunk_no = content_to_index.get("text_chunk_no")
                        
                        if content_to_index.get("tags") is None:
                            content_tags_from_src = ""
                        else:
                            content_tags_from_src = content_to_index.get("tags")
                        
                        if content_to_index.get("title") is None:
                            content_title_from_src = ""
                        else:
                            content_title_from_src = content_to_index.get("title")
                        
                        dt = datetime.now()
                        content_last_modified_date = datetime.timestamp(dt)
                        vec_emb =  contentSite.llm_service.encode(text_chunk_from_src)
                        content_index_flag = 'N' #default
                        
                        content_processed_status = "N"
                        #Insert the meta data, text chunk, vector emebdding for text chunk in vectordb
                        logging.debug("PID:{%d} Inserting the record in vector database for id{%s}",mypid, id)
                        contentSite.vector_db.insert(id = id,
                                                    content_path = content_path_from_src, 
                                                    last_edit_date = content_last_modified_date , 
                                                    tags = content_tags_from_src, 
                                                    title = content_title_from_src, 
                                                    text_chunk = text_chunk_from_src, 
                                                    text_chunk_no = text_chunk_no, 
                                                    vector_embedding = vec_emb)
                        
    
##End of indexing_proc


class createContentSite(srcContentSite):
            
    def __init__(self,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb,llm_service:baseLlmService, do_not_read_dir_list:list = [], do_not_read_file_list:list = []):
       srcContentSite.__init__(self,content_site_name=content_site_name,src_type="indexingService",src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db, llm_service = llm_service, do_not_read_dir_list=do_not_read_dir_list,do_not_read_file_list=do_not_read_file_list)
       self.logger = logging.getLogger(__name__)

    def connect_to_content_site(self):
        # Only checks if the access_key_id is set
        match self.site_auth.auth_type:
            case 'service-key':
                if len(self.site_auth.access_key_id) == 0:
                    self.logger.info('Access Key Id has not been set')   
                

    def connect(self):
        # Connect to content_site
        try:
            self.connect_to_content_site()
        except Exception as err:
            self.logger.error("Could not connect to content site")
            print(err)
            raise

        #Connect to vector database
        try:
            self.vector_db.connect()
        except Exception as err:
            self.logger.error("Could not connect to vector database")
            print(err)
            raise

        #Connect the LLM Service for encoding text -> vector
        try:    
            self.llm_service.connect()
        except Exception as err:
            self.logger.error("Could not connect to LLM service")
            print(err)
            raise
        
    def testConnect(self):
        # test connection to content site
        self.logger.info("Now testing connection to S3")
        self.connect_to_content_site()
        #Test connect to vector database
        try:
            self.logger.info("Now testing connection to vector database")
            self.vector_db.testConnect()
        except Exception as err:
            self.logger.error("Could not connect to vector database")
            print(err)
            raise
        #Test connect the LLM Service for encoding text -> vector
        try:
            self.logger.info("Now testing connection to LLM Service")    
            self.llm_service.testConnect()
        except Exception as err:
            self.logger.error("Could not connect to LLM service")
            print(err)
            raise

    ##Start of index function
    def index(self, no_of_processes = 1):
        self.logger.debug("setup multiprocessing with %d indexing processes", no_of_processes)
        self.no_of_processes = no_of_processes

        try:
            self.connect_to_content_site() #Connect to content-site
        except:
            self.logger.error("Could not connect to content site ... Exiting")
            sys.exit()

        
        #connect to the vector database
        try:
            self.vector_db.connect() # Connect to vectorDb
        except:
            self.logger.error("Could not connect to vector database ... Exiting")
            sys.exit()

        #Cleanup : Purge old records in vectorDb for this site, take backup of old working directory
        self.vector_db.deleteAll()
        self.backupDownloadDirectories()
        self.createDownloadDirectory() #Create before the multiple processeses start downloading

             
        self.logger.debug("Attempting to starting %d processes for indexing", self.no_of_processes)
        if mp.cpu_count() < self.no_of_processes:
            self.logger.critical("Number of CPU %d, is less than number of parallel index process %d requested, Will reset no_of processes to 1 to be safe", mp.cpu_count(), self.no_of_processes)
            self.no_of_processes = 1

        pickle_file_path = self.pickle_me()
        
        #Spawn  indexing processes
        mp.set_start_method('fork', force=True)
        i = 0
        jobs = []
        while i < self.no_of_processes:
            self.logger.info("Spawning indexing job {%d}", i)
            job = mp.Process(target=indexing_proc, args=(pickle_file_path, i,))
            #job.daemon = True
            job.start()
            jobs.append(job)
            i = i + 1        
    ##End of Index function

    #Process the message by putting it in the global queue
    def process(self, msg:str):
        global indexingServiceQueueHandler
        indexingServiceQueueHandler[0].put(msg)
        return "processed"
