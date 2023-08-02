import os
import sys
import configparser
import os, uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from datetime import datetime, timedelta


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb, siteAuth

sys.path.append("../common-functions")
import initializeContentSite

import logging
logger = logging.getLogger(__name__)


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

    #Read the content site configs
    content_site_name = config.get('content-site','sitename')
    src_type = config.get('content-site','srctype')
    src_path = config.get('content-site','srcpath')
    src_path_for_results = config.get('content-site','displaypath')
    logger.debug('Site Name is '+ content_site_name)
    logger.debug('Site Source Type is '+ src_type)
    logger.debug('Site Source Path is '+ src_path)
    logger.debug('Site Source Display Path is '+ src_path_for_results)

    #Read the vector database configs
    vectordb_hostname = config.get('vectordb', 'api-address')
    vectordb_portnumber = config.get('vectordb', 'api-port')
    vectordb_key = config.get('vectordb', 'api-key')
    #db-type can be typesense,qdrant 
    vectordb_type = config.get('vectordb','db-type')
    logger.debug('VectorDB Server Host is ' + vectordb_hostname)
    logger.debug('VectorDB Server Port is '+ vectordb_portnumber)
    logger.debug('VectorDB Server Key is ' + vectordb_key)
    logger.debug('VectorDB Type is '+ vectordb_type)
    vector_db = vectorDb(vectordb_type=vectordb_type, vectordb_hostname = vectordb_hostname, vectordb_portnumber = vectordb_portnumber, vectordb_key = vectordb_key)


    #Read config for local working 
    working_directory = config.get('local','working-dir')
    index_log_directory = config.get('local','index-dir')
    logger.debug('Local working directory  is '+working_directory)
    logger.debug('Local index directory is '+index_log_directory)
 
    #Read configs for the site-autthentication
    match src_type:
        case 'filepath':
            logger.debug('src_type is filepath so will be direct access. Read Access Permissions should be set')
        case 'azureblob':
            auth_type= config.get('content-site-auth','authtype')
            logger.debug('Site Authentication Type is '+ auth_type)
            match auth_type:
                case 'sas':
                    sas_token = config.get('content-site-auth','sastoken')
                    logger.debug('Azure sastoken is %s', sas_token)
                    if len(sas_token) == 0:
                        logger.error('Could not read sastoken for azureblob')
                    else:
                        site_auth= siteAuth(auth_type=auth_type,sas_token=sas_token)
                case 'az-storage-key':
                    az_key = config.get('content-site-auth','key')
                    logger.debug('Azure Storage Key read from config is %s',az_key)
                    if len(az_key) == 0: 
                        logger.error('Could not read Azure key to access azureblob')
                    else:
                        site_auth= siteAuth(auth_type=auth_type,az_key=az_key)
                case other:
                    logger.error('Dont know how to handle for azureblob,auth type %s', auth_type)
    

    #Initialize the content site handler. The returned oject is content site specific (azure, aws,filepath) handler
    contentSite = initializeContentSite.initialize(src_type=src_type,content_site_name=content_site_name,src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db)
    contentSite.connect()
    contentSite.index()
