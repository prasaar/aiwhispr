from operator import truediv
import os
import sys
import io
import uuid
import sqlite3
import boto3
from datetime import datetime, timedelta
import pathlib
import datetime

from more_itertools import bucket

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")
import initializeDocumentProcessor
from aiwhisprLocalIndex import aiwhisprLocalIndex
from aiwhisprBaseClasses import siteAuth,vectorDb,srcContentSite
from awsS3Downloader import awsS3Downloader

import aiwhisprConstants 

import logging

class createContentSite(srcContentSite):
            
    downloader:awsS3Downloader

    def __init__(self,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb):
       srcContentSite.__init__(self,content_site_name=content_site_name,src_type="s3",src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db)
       self.s3_bucket_name = src_path.split('/')[2]
       self.downloader = awsS3Downloader()
       self.logger = logging.getLogger(__name__)

    def connect(self):
       # Connect to AWS S3, Connect to localDB  which stores the ContentIndex
       # Create the boto3 client object
       match self.site_auth.auth_type:
           case 'aws-key':
               self.logger.info('Connecting to AWS S3 using AWS KEY')
               self.s3_client = boto3.client('s3', aws_access_key_id=self.site_auth.aws_access_key_id, aws_secret_access_key=self.site_auth.aws_secret_access_key)
           case other:
               self.logger.error('No authentication provided for AWS S3 connection')
       #get handle to the local index map object
       self.local_index = aiwhisprLocalIndex(self.index_log_directory, self.content_site_name)
       
    def index(self):
        ###Now start reading the site and list all the files
        self.logger.info('Reading AWS S3 bucket:' + self.s3_bucket_name)
        self.logger.info("Purging the current local ContenIndex Map")
        self.local_index.purge()
        # List all the objects in the bucket 
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

            
            for bucket_object in bucket_objects_list['Contents']:
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

                if(content_file_suffix != None): 
                    if ( content_file_suffix in aiwhisprConstants.FILEXTNLIST ): 
                        content_index_flag = 'Y'

                if content_file_suffix == None:
                    content_file_suffix = 'NONE'

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
                content_processed_status
                )

                if content_index_flag == 'Y':
                    download_file_path = self.getDownloadPath(content_path)
                    self.logger.debug('Downloaded File Name: ' + download_file_path)
                    self.downloader.download_s3object_to_file(self.s3_client, self.s3_bucket_name, content_path, download_file_path)                     
                    docProcessor =  initializeDocumentProcessor.initialize(content_file_suffix,download_file_path)
                    if (docProcessor != None ):
                        docProcessor.extractText()
                        docProcessor.createChunks()
                    else:
                        self.logger.debug('Content Index Flag was "Y" but we did not get a valid document processor')

            contentrows = self.local_index.getContentProcessedStatus("N") 
            self.logger.debug("Total Number of rows in ContentIndex with ProcessedStatus = N:" + str( len(contentrows)) )
