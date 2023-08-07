import os
import sys
import io
import uuid
import sqlite3
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_account_sas, ResourceTypes, AccountSasPermissions
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
from aiwhisprBaseClasses import siteAuth,vectorDb,srcContentSite,srcDocProcessor
from azureBlobDownloader import azureBlobDownloader

import aiwhisprConstants 

import logging

class createContentSite(srcContentSite):
            
    downloader:azureBlobDownloader

    def __init__(self,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb):
       srcContentSite.__init__(self,content_site_name=content_site_name,src_type="azureblob",src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db)
       self.azure_account_url = src_path.split('/')[2]
       self.container_name= src_path.split('/')[3]
       self.downloader = azureBlobDownloader()
       self.logger = logging.getLogger(__name__)

    def connect(self):
       # Connect to Azure, Connect to localDB  which stores the ContentIndex
       # Create the BlobServiceClient object
       match self.site_auth.auth_type:
           case 'sas':
               self.logger.info('Connecting to Azure using sas')
               self.blob_service_client = BlobServiceClient(account_url=self.azure_account_url, credential=self.site_auth.sas_token)
               self.container_client = self.blob_service_client.get_container_client(container=self.container_name)
           case 'az-storage-key':
               self.logger.info('Connecting to Azure using storage account key')
               self.blob_service_client = BlobServiceClient(account_url=self.azure_account_url, credential=self.site_auth.az_key)
               self.container_client = self.blob_service_client.get_container_client(container=self.container_name)
           case other:
               self.logger.error('No authentication provided for Azure connection')
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

        #1\ CLeanup: Purge old records in local index, vectorDb for this site
        self.local_index.deleteAll()
        self.vector_db.deleteAll()
        self.backupDownloadDirectories()

        ###2\ Now start reading the site and list all the files
        self.logger.info('Reading an Azure Storage Account : ' + self.azure_account_url +  ' with Container: ' + self.container_name)
        self.logger.info("Purging the current local ContentIndex Map")
       
        # List the blobs in the container
        blob_list = self.container_client.list_blobs()
        for blob in blob_list:
            self.logger.debug("BlobName:" + blob.name+' last_modified:'+str(blob.last_modified)+ ' creation_time:'+str(blob.creation_time))
            #self.logger.debug(blob)
            #Insert this list in the index database

            #Get metadata for each file
            content_file_suffix = pathlib.PurePath(blob.name).suffix          
            content_index_flag = 'N' #default
            content_path = blob.name
            content_type = blob.content_settings.content_type
            content_creation_date = blob.creation_time
            content_last_modified_date = blob.last_modified
            content_uniq_id_src = blob.etag
            content_tags_from_src = ''
            content_size = blob.size
            content_processed_status = "N"

            if(content_file_suffix != None): 
                if ( content_file_suffix in aiwhisprConstants.FILEXTNLIST ): 
                    content_index_flag = 'Y'
            if ( (content_index_flag == 'N') and (blob.content_settings.content_type != None) and ( blob.content_settings.content_type[:4] == 'text' ) ):
                content_index_flag = 'Y'

            #Decide if the file should be read
            if content_file_suffix == None:
                content_file_suffix = 'NONE'
            if content_type == None:
                content_type = 'NONE'
            if content_uniq_id_src == None:
                content_uniq_id_src = 'NONE'
            if content_size == None:
                content_size = 0

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

            rsync_status = 'I'
            self.logger.debug(rsync_status)

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

            if content_index_flag == 'Y':
                #Download the file
                download_file_path = self.getDownloadPath(content_path)
                self.logger.debug('Downloaded File Name: ' + download_file_path)
                self.downloader.download_blob_to_file(self.blob_service_client, self.container_name, content_path, download_file_path) 
                docProcessor =  initializeDocumentProcessor.initialize(content_file_suffix,download_file_path)
                if ( docProcessor != None ):
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
