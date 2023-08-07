import os
import sys
import io
import uuid
import sqlite3
import boto3
from datetime import datetime, timedelta
import pathlib
import datetime


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")

import initializeDocumentProcessor
from aiwhisprLocalIndex import aiwhisprLocalIndex
from aiwhisprBaseClasses import siteAuth,vectorDb,srcContentSite
from filepathDownloader import filepathDownloader

import aiwhisprConstants 

import logging

class createContentSite(srcContentSite):
            
    downloader:filepathDownloader

    def __init__(self,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb):
       srcContentSite.__init__(self,content_site_name=content_site_name,src_type="s3",src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db)
       self.downloader = filepathDownloader()
       self.logger = logging.getLogger(__name__)
            
    def connect(self):
       
       #Check if the top level directory exists
       if os.path.isdir(self.src_path) == False:
           self.logger.error("Src Type: %s Source Path: %s does not exist", self.src_type, self.src_path)
       #get handle to the local index map object
       self.local_index = aiwhisprLocalIndex(self.index_log_directory, self.content_site_name)
       #Request the vector db to connect to the server
       self.vector_db.connect()
       
    def index(self):

         #Indexing is a multi-step operation
        # 1\ Cleanup : Purge the local index, vector db , move the old work dub-directorry to a backup
        # 2\ Read content site, for each file  get the file suffix and decide if we extract text for vector embeddings
        #      If we decide to process the file then download it, extract text and break the text into chunks
        #      For each text chunk get the vector embedding
        #      Insert the text chunk, associated meta data and vector embedding into the vector database

        #1\ Cleanup : Purge old records in local index, vectorDb for this site
        self.local_index.deleteAll()
        self.vector_db.deleteAll()
        self.backupDownloadDirectories()

        ###2\ Now start reading the site and list all the files
        self.logger.info('Reading From Top Level Directory:' + self.src_path)
        self.logger.info("Purging the current local ContentIndex Map")
        
        directory = self.src_path
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                content_path = os.path.join(dirpath, filename)
                if self.site_auth.check_file_permission == "Y":
                    if os.access(content_path, os.R_OK):
                        self.logger.debug("File permission for %s is R_OK", content_path)
                else:
                    self.logger.error("Cannot read the file : %s", content_path)

                with open(content_path) as f:
                    
                    
                    #Insert this list in the index database
                    #content_path = content_path

                    #Get metadata for each file
                    content_file_suffix = pathlib.PurePath(content_path).suffix          
                    content_index_flag = 'N' #default
                    content_type = 'NONE' #AWS S3 Does not give you content type
                    content_creation_date = os.path.getctime(content_path)
                    content_last_modified_date = os.path.getmtime(content_path)
                    content_uniq_id_src = content_path
                    content_tags_from_src = ''
                    content_size = os.path.getsize(content_path)
                    content_processed_status = "N"
                    self.logger.debug("File Path: %s CreateDate: %f LastModified: %f Size: %d", content_path,content_creation_date, content_last_modified_date, content_size)
                    
                    #Decide if the file should be read
                    if(content_file_suffix != None): 
                        if ( content_file_suffix in aiwhisprConstants.FILEXTNLIST ): 
                            content_index_flag = 'Y'

                    if content_file_suffix == None:
                        content_file_suffix = 'NONE'

                    if content_size == None:
                        #Dont index zero size files
                        content_size = 0
                        content_index_flag = 'N'

                    self.logger.debug("Insert Content Map Values:")
                    self.logger.debug(self.content_site_name)
                    self.logger.debug(self.src_path)
                    self.logger.debug(self.src_path_for_results)
                    self.logger.debug(content_path)
                    self.logger.debug(content_type)
                    self.logger.debug( "%f", content_creation_date)
                    self.logger.debug( "%f", content_last_modified_date) 
                    self.logger.debug(content_uniq_id_src)
                    self.logger.debug(content_tags_from_src)
                    self.logger.debug("%d",content_size)
                    self.logger.debug(content_file_suffix)
                    self.logger.debug(content_index_flag)
                    self.logger.debug(content_processed_status)


                    rsync_status = 'I'
                    self.logger.debug(rsync_status)

                    self.local_index.insert(
                    self.content_site_name, 
                    self.src_path, 
                    self.src_path_for_results, 
                    content_path, 
                    content_type, 
                    content_creation_date, 
                    content_last_modified_date, 
                    content_uniq_id_src, 
                    content_tags_from_src, 
                    content_size, 
                    content_file_suffix, 
                    content_index_flag, 
                    content_processed_status,
                    rsync_status
                    )

                    if content_index_flag == 'Y':
                        #Download the file
                        download_file_path = self.getDownloadPath(content_path)
                        self.logger.debug('Downloaded File Name: ' + download_file_path)
                        self.downloader.download_content_file(content_path, download_file_path)                     
                        docProcessor =  initializeDocumentProcessor.initialize(content_file_suffix,download_file_path)
                        if (docProcessor != None ):
                            #Extract text
                            docProcessor.extractText()
                            #Create text chunks
                            chunk_id_dict = docProcessor.createChunks()
                            self.logger.debug("%d chunks created for %s", len(chunk_id_dict), download_file_path)
                            for id in chunk_id_dict.keys():
                                self.logger.debug("id:{%s} text_chunk_no:{%d}", id, chunk_id_dict[id])
                        else:
                            self.logger.debug('Content Index Flag was "Y" but we did not get a valid document processor')

        contentrows = self.local_index.getContentProcessedStatus("N") 
        self.logger.debug("Total Number of rows in ContentIndex with ProcessedStatus = N:" + str( len(contentrows)) )
