import os
import sys
import configparser
import os, uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from datetime import datetime, timedelta


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../base-classes")
from azureContentSite import azureContentSite
from aiwhisprBaseClasses import vectorDb, siteAuth

def index(configfile):


    vectordb_type = ''
    vectordb_hostname = ''
    vectordb_portnumber = ''
    vectordb_key = ''
    content_site_name = ''
    src_type = ''
    src_path = ''
    src_path_for_results = ''
    auth_type = ''
    sas_token = ''
    site_userid = ''
    site_password = ''

    #interpolation is set to None to allow reading special symbols like %
    config =  configparser.ConfigParser(interpolation=None)
    config.read(configfile)

    vectordb_hostname = config.get('vectordb', 'api-address')
    vectordb_portnumber = config.get('vectordb', 'api-port')
    vectordb_key = config.get('vectordb', 'api-key')
    #sw-name can be typesense,qdrant 
    vectordb_type = config.get('vectordb','db-type')
    content_site_name = config.get('content-site','sitename')
    src_type = config.get('content-site','srctype')
    src_path = config.get('content-site','srcpath')
    src_path_for_results = config.get('content-site','displaypath')
    if(src_type != 'filepath'):
         auth_type= config.get('auth','authtype')
         if( ( (src_type == 'azureblob') or (src_type == 's3') )  and ( auth_type == 'sas' ) ):
             sas_token = config.get('auth','sastoken')
         else:
             site_userid = config.get('auth','userid')
             site_password = config.get('auth','password')

    working_directory = config.get('local','working-dir')
    index_log_directory = config.get('local','index-dir')


    print ('VectorDB Server Host is ', vectordb_hostname)
    print ('VectorDB Server Port is ', vectordb_portnumber)
    print ('VectorDB Server Key is ', vectordb_key)
    print ('VectorDB Type is ', vectordb_type)
    print ('Site Name is ', content_site_name)
    print ('Site Source Type is ', src_type)
    print ('Site Source Path is ', src_path)
    print ('Site Source Display Path is ', src_path_for_results)
    print ('Site Authentication Type is ', auth_type)
    print ('Site Authentication SAS Token is ', sas_token)
    print ('Site User Id is ', site_userid)
    print ('Site Password is ',site_password)
    print ('Local working directory  is ',working_directory)
    print ('Local index directory is ',index_log_directory)



    vector_db = vectorDb(vectordb_type=vectordb_type, vectordb_hostname = vectordb_hostname, vectordb_portnumber = vectordb_portnumber, vectordb_key = vectordb_key)

    if auth_type=='sas':
        site_auth= siteAuth(auth_type,sas_token)
    elif auth_type=='azlogin':
        site_auth= siteAuth(auth_type,site_userid,site_password)

    if src_type == 'azureblob':
        #instantiate azureContentSite 
        contentSite = azureContentSite(content_site_name=content_site_name,src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db)
        contentSite.connect()
        contentSite.index()
