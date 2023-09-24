from operator import truediv
import os
import sys
import io
import uuid
import sqlite3
import boto3
from botocore import UNSIGNED as botoUNSIGNED
from botocore.client import Config as botoConfig

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




##This function is used by both single process and multiprocess
def index_from_list(pickle_file_path,process_list = 0):
    logger = logging.getLogger(__name__)
    mypid = os.getpid()
    
    try:
        f = open(pickle_file_path, 'rb')   # 'rb' for reading binary file
        self_description = pickle.load(f)     
        f.close()
    except:
        logger.error("PID:{%d} could not read the pickle file at %s", mypid, pickle_file_path )
        sys.exit()

    file_with_content_path_list = self_description['download_these_files_list'][process_list]
    logger.debug("PID:{%d} Indexing S3 Content Site in parallel by indexing files in the list in %s",mypid, file_with_content_path_list)          
    
    site_auth=siteAuth(auth_type= self_description['site_auth']['auth_type'],
                       aws_access_key_id=self_description['site_auth']['aws_access_key_id'],
                       aws_secret_access_key=self_description['site_auth']['aws_secret_access_key'])

    #Instantiate the vector db object. This will return a vectorDb derived class based on the module name
    vector_db = initializeVectorDb.initialize(vectordb_module=self_description['vector_db']['module_name'],
                                             vectordb_config = self_description['vector_db']['vectordb_config'], 
                                             content_site_name = self_description['content_site']['content_site_name'],
                                             src_path = self_description['content_site']['src_type'], 
                                             src_path_for_results = self_description['content_site']['src_path_for_results'] 
                                             )
    
    llm_service = initializeLlmService.initialize(llm_service_module = self_description['llm_service']['module_name'], 
                                                  llm_service_config = self_description['llm_service']['llm_service_config'])
                            
    contentSite = initializeContentSite.initialize(content_site_module='awsS3ContentSite',
                                                   src_type=self_description['content_site']['src_type'],
                                                   content_site_name=self_description['content_site']['content_site_name'],
                                                   src_path=self_description['content_site']['src_path'],
                                                   src_path_for_results=self_description['content_site']['src_path_for_results'],
                                                   working_directory=self_description['local']['working_directory'],
                                                   index_log_directory=self_description['local']['index_log_directory'],
                                                   site_auth=site_auth,
                                                   vector_db = vector_db,
                                                   llm_service = llm_service,
                                                   do_not_read_dir_list =  self_description['content_site']['do_not_read_dir_list'] ,
                                                   do_not_read_file_list = self_description['content_site']['do_not_read_file_list'] )
    
    contentSite.connect()
    

    # Read list of paths to download from the path_to_download_file_list, 
    #      for each file  get the file suffix and decide if we extract text for vector embeddings
    #          If we decide to process the file then download it, extract text and break the text into chunks
    #              For each text chunk get the vector embedding
    #              Insert the text chunk, associated meta data and vector embedding into the vector database
    
    #Now start reading the site and list all the files
    file_download_list = open(file_with_content_path_list, 'r', encoding="utf-8")
    continue_reading_file_list = True
    content_path = ''
    while continue_reading_file_list:  # Get next line from file
        row = file_download_list.readline()
        if not row:
            continue_reading_file_list = False
        else:
            # if line is empty then end of file is reached
            row_all_fields = row.split('|')
            content_path = row_all_fields[3]
            content_size = int(row_all_fields[9])
            content_creation_date = float(row_all_fields[5])
            content_last_modified_date = float(row_all_fields[6])
            
            if len(content_path) > 0: 
                
                #Get metadata
                logger.debug("PID:{%d} Object Name: %s LastModified: %s", mypid, content_path,str(content_last_modified_date))
                content_file_suffix = pathlib.PurePath(content_path).suffix          
                content_index_flag = 'N' #default
                content_type = 'NONE' #AWS S3 Does not give you content type
                content_uniq_id_src = content_path
                content_tags_from_src = ''
                
                content_processed_status = "N"

                #Download the file
                download_file_path = contentSite.getDownloadPath(content_path = content_path, pid_suffix = str(mypid) )
                logger.debug("PID:{%d} Downloaded File Name: %s", mypid, download_file_path)
                contentSite.downloader.download_s3object_to_file(contentSite.s3_client, contentSite.s3_bucket_name, content_path, download_file_path)                     
                docProcessor =  initializeDocumentProcessor.initialize(content_file_suffix,download_file_path)

                if (docProcessor != None ):
                    #Extract text
                    docProcessor.extractText()
                    #Create text chunks
                    chunk_dict = docProcessor.createChunks()
                    logger.debug("PID:{%d} %d chunks created for %s", mypid, len(chunk_dict), download_file_path)
                    #For each chunk, read text, create vector embedding and insert in vectordb
                    ##the chunk_dict dictionary will have key=/filepath_to_the_file_containing_text_chunk, value=integer value of the chunk number.
                    for chunk_file_path in chunk_dict.keys():
                        text_chunk_no = chunk_dict[chunk_file_path]
                        logger.debug("PID:{%d} chunk_file_path:{%s} text_chunk_no:{%d}", mypid, chunk_file_path, text_chunk_no)
                        #Now encode the text chunk. chunk_file_path is the file path to the text chunk
                        text_f = open(chunk_file_path)
                        text_chunk_read = text_f.read()
                        vec_emb =  contentSite.llm_service.encode(text_chunk_read)
                        logger.debug("PID:{%d} Vector encoding dimension is {%d}",mypid, len(vec_emb))
                        text_f.close()

                        id = contentSite.generate_uuid()
                        #Insert the meta data, text chunk, vector emebdding for text chunk in vectordb
                        logger.debug("PID:{%d} Inserting the record in vector database for id{%s}",mypid, id)
                        contentSite.vector_db.insert(id = id,
                                            content_path = content_path, 
                                            last_edit_date = content_last_modified_date , 
                                            tags = content_tags_from_src, 
                                            title = "", 
                                            text_chunk = text_chunk_read, 
                                            text_chunk_no = text_chunk_no, 
                                            vector_embedding = vec_emb)
                else:
                    logger.error("Did not find a document processor for document{%s}, with file suffix:{%s}",download_file_path,content_file_suffix)
           
    logger.info("PID:{%d} finished indexing the files is the list from %s ", mypid, file_with_content_path_list )
    file_download_list.close()
##End of index_in_parallel


class createContentSite(srcContentSite):
            
    downloader:awsS3Downloader

    def __init__(self,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb,llm_service:baseLlmService, do_not_read_dir_list:list = [], do_not_read_file_list:list = []):
       srcContentSite.__init__(self,content_site_name=content_site_name,src_type="s3",src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db, llm_service = llm_service, do_not_read_dir_list=do_not_read_dir_list,do_not_read_file_list=do_not_read_file_list)
       self.s3_bucket_name = src_path.split('/')[2]
       self.downloader = awsS3Downloader()
       self.logger = logging.getLogger(__name__)

    def connect_to_content_site(self):
        # Connect to AWS S3, Connect to localDB  which stores the ContentIndex
        # Create the boto3 client object
        match self.site_auth.auth_type:
            case 'aws-key':
                self.logger.info('Connecting to AWS S3 using AWS KEY')
                if self.site_auth.aws_access_key_id == 'UNSIGNED':
                    self.logger.info('Connecting to AWS S3 using UNSIGNED ACCESS')
                    self.s3_client = boto3.client('s3',config=botoConfig(signature_version=botoUNSIGNED))   
                else:
                    self.s3_client = boto3.client('s3', aws_access_key_id=self.site_auth.aws_access_key_id, aws_secret_access_key=self.site_auth.aws_secret_access_key)
        
                try:
                    #test the connection by retrieving the list of objects
                    response = self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
                except Exception as err:
                    self.logger.error("Could not connect to S3 bucket")
                    print(err)
                    raise
            case other:
                self.logger.error('No authentication provided for AWS S3 connection')


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
        self.logger.debug("Indexing S3 Content Site with %d processes", no_of_processes)
        self.no_of_processes = no_of_processes

        try:
            self.connect_to_content_site() #Connect to content-site
        except:
            self.logger.error("Could not connect to content site ... Exiting")
            sys.exit()

        #create the local index  object, it will be used to record the metdata of the src files in the content site
        try:
            self.local_index = aiwhisprLocalIndex(self.index_log_directory, self.content_site_name)
        except:
            self.logger.error("Could not connect to local index to store metadata ... Exiting")
            sys.exit()

        #connect to the vector database
        try:
            self.vector_db.connect() # Connect to vectorDb
        except:
            self.logger.error("Could not connect to vector database ... Exiting")
            sys.exit()

        #1\ Cleanup : Purge old records in local index, vectorDb for this site, take backup of old working directory
        self.local_index.deleteAll()
        self.vector_db.deleteAll()
        self.backupDownloadDirectories()
        self.createDownloadDirectory() #Create before the multiple processeses start downloading

        #2\ Now start reading the site and list all the files
        self.logger.debug('Reading AWS S3 bucket:' + self.s3_bucket_name)
        self.logger.debug("Purging the current local ContentIndex Map")
        
        # List all the objects in the bucket
        # For each file, decided if it should be indexed.
        #If yes then store the metadata in the local index
        continueReadingBucket = True
        bucketListIsTruncated = False
        NextContinuationToken = ''
        while continueReadingBucket:

            if bucketListIsTruncated:
                self.logger.debug('Another loop to read the next set of bucket objects')
                bucket_objects_list = self.s3_client.list_objects_v2(Bucket=self.s3_bucket_name,ContinuationToken=NextContinuationToken,MaxKeys=aiwhisprConstants.S3MAXKEYS)
            else:
                #This is the first and the last call to read bucket contents
                bucket_objects_list = self.s3_client.list_objects_v2(Bucket=self.s3_bucket_name,MaxKeys=aiwhisprConstants.S3MAXKEYS)

            bucketListIsTruncated = bucket_objects_list['IsTruncated']
            keyCount = bucket_objects_list['KeyCount']
            self.logger.debug('bucketListIsTruncated: %s keyCount: %d', str(bucketListIsTruncated), keyCount)

            if bucketListIsTruncated:
                #We will have to do another pass after processing these results
                NextContinuationToken = bucket_objects_list['NextContinuationToken']
                continueReadingBucket = True
            else:
                #this is the last result set
                continueReadingBucket = False
                NextContinuationToken = ''

            #Now for each file , identify it should be indexed.
            #If yes then insert the file metadata in the local index.
            for bucket_object in bucket_objects_list['Contents']:
                #Get metadata for each file
                self.logger.debug("Object Name: %s LastModified: %s", bucket_object['Key'],str(bucket_object['LastModified']))
                #Insert this list in the index database
                content_path = bucket_object['Key']
                content_file_suffix = pathlib.PurePath(content_path).suffix          
                content_index_flag = 'N' #default
                content_type = 'NONE' #AWS S3 Does not give you content type
                content_creation_date = bucket_object['LastModified']
                content_last_modified_date = bucket_object['LastModified']
                content_uniq_id_src = content_path
                content_tags_from_src = ''
                content_size = bucket_object['Size']
                content_processed_status = "N"

                #Check if the content_path should be read and does not trigger a do_not_read
                contentShouldBeRead = True #Default
                contentShouldBeRead = self.checkIfContentShouldBeRead(content_path)
                if contentShouldBeRead == True:
                    self.logger.debug("checkIfContentShouldBeRead=True for %s", content_path)
                else:
                    self.logger.debug("checkIfContentShouldBeRead=False for %s", content_path)

                if contentShouldBeRead == True:  
                    #Decide if the file should be read
                    if(content_file_suffix != None): 
                        if ( content_file_suffix in aiwhisprConstants.FILEXTNLIST ): 
                            content_index_flag = 'Y'

                    if content_file_suffix == None:
                        content_file_suffix = 'NONE'

                    if content_size == None:
                        content_size = 0

                    if content_index_flag == 'Y':  #Then insert this content_path in the local index.
                        rsync_status = 'I'
                        ####DEBUG####
                        self.logger.debug("Insert Content Map Values:")
                        self.logger.debug(self.content_site_name)
                        self.logger.debug(self.src_path)
                        self.logger.debug(self.src_path_for_results)
                        self.logger.debug(content_path)
                        self.logger.debug(content_type)
                        self.logger.debug( str( content_creation_date.timestamp() ))
                        self.logger.debug( str(content_last_modified_date.timestamp() ))
                        self.logger.debug(content_uniq_id_src)
                        self.logger.debug(content_tags_from_src)
                        self.logger.debug(str(content_size))
                        self.logger.debug(content_file_suffix)
                        self.logger.debug(content_index_flag)
                        self.logger.debug(content_processed_status)                
                        self.logger.debug(rsync_status)
                        ####DEBUG-END####

                        #Insert in local index 
                        self.local_index.insert(
                        self.content_site_name, 
                        self.src_path, 
                        self.src_path_for_results, 
                        content_path, 
                        content_type, 
                        content_creation_date.timestamp(), 
                        content_last_modified_date.timestamp(), 
                        content_uniq_id_src, 
                        content_tags_from_src, 
                        content_size, 
                        content_file_suffix, 
                        content_index_flag, 
                        content_processed_status,
                        rsync_status
                        )

        #Call function that will now create the files that have all the download content_path
        #If its a single process then a single file is created.If its multiple process (self.no_of_processes)
        #then the workload is distributed
        self.create_download_these_files_list()
     
        self.logger.debug("Attempting to starting %d processes for indexing", self.no_of_processes)
        if mp.cpu_count() < self.no_of_processes:
            self.logger.critical("Number of CPU %d, is less than number of parallel index process %d requested, Will reset no_of processes to 1 to be safe", mp.cpu_count(), self.no_of_processes)
            self.no_of_processes = 1

        pickle_file_path = self.pickle_me()
        
        #Spawn  indexing processes
        mp.set_start_method('spawn')
        i = 0
        jobs = []
        while i < self.no_of_processes:
            self.logger.info("Spawning indexing job {%d}", i)
            job = mp.Process(target=index_from_list, args=(pickle_file_path, i,))
            job.start()
            jobs.append(job)
            i = i + 1 
       
            
                
    ##End of Index function

    
