import os
import sys
import io
import uuid
import sqlite3
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from datetime import datetime, timedelta
import logging
import pathlib
import datetime

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
#sys.path.append("../common-functions")
sys.path.append("../common-objects")
from aiwhisprLocalIndex import aiwhisprLocalIndex

def index(content_site_name,src_path,src_path_for_results,working_directory,index_log_directory,auth_type,sas_token,site_userid, site_password,vectordb_type,vectordb_hostname,vectordb_portnumber, vectordb_key):
   file_extension_list = ['.txt', '.csv', '.xls', '.xlsx', '.doc', '.docx', '.ppt', '.pptx']
   ###Now start reading the site and list all the files
   if(auth_type == 'sas'):
       azure_account_url = src_path.split('/')[2]
       container_name= src_path.split('/')[3]
       print('Reading an Azure Storage Account : ', azure_account_url, 'with Container: ', container_name)

       # Create the BlobServiceClient object
       blob_service_client = BlobServiceClient(account_url=azure_account_url, credential=sas_token)
       container_client = blob_service_client.get_container_client(container=container_name)
       # List the blobs in the container
       local_index = aiwhisprLocalIndex(index_log_directory, content_site_name)
       blob_list = container_client.list_blobs()
       for blob in blob_list:
           print("\t" + blob.name,'last_modified:',blob.last_modified, 'creation_time:',blob.creation_time,'content_type:',blob.content_settings.content_type)
           #print(blob)
           #Insert this list in the index database
           content_file_suffix = pathlib.Path(blob.name).suffix          
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
               if ( content_file_suffix in file_extension_list ): 
                   content_index_flag = 'Y'
           if ( (content_index_flag == 'N') and (blob.content_settings.content_type != None) and ( blob.content_settings.content_type[:4] == 'text' ) ):
               content_index_flag = 'Y'

           if content_file_suffix == None:
               content_file_suffix = 'NONE'
           if content_type == None:
               content_type = 'NONE'
           if content_uniq_id_src == None:
               content_uniq_id_src = 'NONE'
           if content_size == None:
               content_size = 0

           print("Insert Values")
           print("####")
           print(
           content_site_name,'\n',
           src_path,'\n',
           src_path_for_results,'\n',
           content_path,'\n',
           content_type,'\n',
           content_creation_date.timestamp(),'\n',
           content_last_modified_date.timestamp(),'\n', 
           content_uniq_id_src,'\n',
           content_tags_from_src,'\n',
           content_size,'\n',
           content_file_suffix,'\n' ,
           content_index_flag, '\n',
           content_processed_status
           )
           print("####")

           local_index.insert(
           content_site_name, 
           src_path, 
           src_path_for_results, 
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

