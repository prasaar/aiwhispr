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
import initializeVectorDb
import initializeLlmService

import logging
logger = logging.getLogger(__name__)


def index(configfile:str,operation:str):

    if len(configfile) == 0:
        logger.error("No config file provided. Exiting...")
        sys.exit()
    if len(operation) == 0:
        logger.error("No  operation argument provided. Exiting...")
        sys.exit()
    #List of operations under this function
    operation_list = ['index', 'testconnection'] 
    #Check if the operation argument matches anything in the operation_list
    opres=False
    c=0
    for op in operation_list:
        if(operation.find(op)!=-1):
            c=c+1
    
    if(c>=1):
        opres=True

    if opres==False:
        logger.error("Operation %s not supported. Exiting...", operation)
        sys.exit()

    vectordb_module = ''
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

    logger.info("Started indexing using config file")
    #Read the content site configs
    content_site_name = config.get('content-site','sitename')
    src_type = config.get('content-site','srctype')
    src_path = config.get('content-site','srcpath')
    src_path_for_results = config.get('content-site','displaypath')
    content_site_module = config.get('content-site','contentSiteModule')
    
    doNotReadDirList = ''
    doNotReadFileList = ''
    
    try:
        doNotReadDirList = config.get('content-site','doNotReadDirList')  #Make it easy to skip directories : a comma separated list of directories not to read
    except configparser.NoOptionError as exc:
        logger.debug("doNotReadDirList option not defined")
        doNotReadDirList = ''
    except:
        logger.error("Problem when reading doNotReadDirList option from config file")
        doNotReadDirList = ''

    try:
        doNotReadFileList = config.get('content-site','doNotReadFileList')#Make it easy to skip filename patters: a comma separated list of filename pattern not to read
    except configparser.NoOptionError as exc:
        logger.debug("doNotReadFileList option not defined")
        doNotReadFileList = ''
    except:
        logger.error("Problem when reading doNotReadFileList option from config file")
        doNotReadFileList = ''

    do_not_read_dir_list=[]
    do_not_read_file_list = []

    if len(doNotReadDirList) > 0:
        for d in doNotReadDirList.split(','):
            do_not_read_dir_list.append(d)
    if len(doNotReadFileList) > 0:
        for pattern_str in doNotReadFileList.split(','):
            do_not_read_file_list.append(pattern_str)

    logger.info('Site Name is '+ content_site_name)
    logger.info('Site Source Type is '+ src_type)
    logger.info('Site Source Path is '+ src_path)
    logger.info('Site Source Display Path is '+ src_path_for_results)
    logger.info('Content Site Module is: %s', content_site_module)
    logger.info('doNotReadDirList is %s', doNotReadDirList)
    logger.info('doNotReadFileList is %s', doNotReadFileList)

    #Read the vector database configs
    vectordb_config = dict(config.items('vectordb'))
    vectordb_module = config.get('vectordb','vectorDbModule')
    logger.info('VectorDB Module is '+ vectordb_module)
    logger.info('Vectordb Config is : %s', str(vectordb_config))
    
    #Read config for local section 
    working_directory = config.get('local','working-dir')
    index_log_directory = config.get('local','index-dir')
    logger.info('Local working directory  is '+working_directory)
    logger.info('Local index directory is '+index_log_directory)
    try:
        indexing_processes = config.get('local','indexing-processes')
        if indexing_processes == '' or indexing_processes == None:
           no_of_processes = 1
        else:
           no_of_processes = int(indexing_processes)
    except configparser.NoOptionError as exc:
        logger.info("indexing-process option is not defined, so assuming a single process")
        no_of_processes = 1
    except:
        logger.error("Problem when reading no_of_indexing_process")
        no_of_processes = 1
    logger.info('Local number of indexing process to run '  + str(no_of_processes) )

    #Read config for the LLM Service
    llm_service_config = dict(config.items('llm-service'))
    llm_service_module = config.get('llm-service', 'llmServiceModule')
    logger.info("LLM Service Module Name is %s", llm_service_module)
    logger.info('LLM Service Config is : %s', str(llm_service_config))
    
    #Read configs for the site-authentication
    #Source Type are the root directory hosting types from where we read the path/files
    #Source Tpe can be a filepath, azureblob, s3(aws)
    #We have associated authetication related keys for each Source Type.
    # For azureblob we support a sas token and storage account key. We prefer the storage account key since SAS token can expire.
    #You should create sas token , storage account with restricted privileges to list contents in Azure container and read the blobs
    #For s3 we support aws access key. AWS has features to assign sophisticated , granular S3 bucket policies to IAM users.
    #You can create an IAM user which is assigned the bucket specific list, read objects policy. The create AWS Key for this user.
    #We have tested aiwhispr with granular access policy implementations on AWS S3 and Azure Blobs.
    #ACL(access control list) support of content source is important so if you feel we should be adding new features then email to contact@aiwhispr.com
    #The config files that AIWhispr reads contains the access keys , so please ensure that these config files do not ahve a public read access.
    #Also ensure that these config files are not managed under a public source code repository
    match src_type:
        case 'filepath':
            auth_type= config.get('content-site-auth','authtype')
            logger.debug('src_type is filepath so will be direct access. We will check for permissions')
            logger.debug('Site Authentication Type is '+ auth_type)
            match auth_type:
                case 'filechecks':
                    check_file_permission = config.get('content-site-auth','check-file-permission')

                    if check_file_permission == None:
                       check_file_permission = "N"
                    elif check_file_permission == "n" or check_file_permission == "no" or check_file_permission =="No" or check_file_permission == "N":
                        check_file_permission = "N"
                    elif check_file_permission == "y" or check_file_permission == "yes" or check_file_permission =="Yes" or check_file_permission == "Y":
                        check_file_permission = "Y"  #Check that file can be read before it's read and indexed.
                    else: 
                        check_file_permission = "N"
                    
                    logger.debug("Src Type : %s , Check File Permission Flag : %s", src_type, check_file_permission)
                    site_auth = siteAuth(auth_type=auth_type,check_file_permission=check_file_permission)

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
        case 's3':
            auth_type = config.get('content-site-auth','authtype')
            logger.debug('Site Authentication Type is '+ auth_type)
            match auth_type:
                case 'aws-key':
                    aws_access_key_id = config.get('content-site-auth','aws-access-key-id')
                    aws_secret_access_key = config.get('content-site-auth','aws-secret-access-key')
                    logger.debug('aws_access_key_id : %s aws_secret_access_key: %s', aws_access_key_id, aws_secret_access_key)
                    if(len(aws_access_key_id) == 0 or len(aws_secret_access_key) == 0):
                        logger.error('Could not ready aws-access-key-id, aws-secret-access-key combination to access AWS S3')
                    else:
                        site_auth=siteAuth(auth_type=auth_type,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
                case other:
                    logger.error('Dont know how to handle for s3,auth type %s', auth_type)
        case 'google-cloud':
            auth_type = config.get('content-site-auth','authtype')
            logger.debug('Site Authentication Type is '+ auth_type)
            match auth_type:
                case 'google-cred-key':
                    google_cred_path = config.get('content-site-auth','google-cred-path')
                    google_project_id = config.get('content-site-auth','google-project-id')
                    google_storage_api_key = config.get('content-site-auth','google-storage-api-key')
                    logger.debug('google_cred_path : %s google_project_id : %s google_storage_api_key: %s', google_cred_path, google_project_id, google_storage_api_key)
                    if(len(google_cred_path) == 0 or len(google_project_id) == 0 or len(google_storage_api_key) == 0):
                        logger.error('Could not read google-cred-path, google-project-id, google-storage-api-key')
                    else:
                        site_auth=siteAuth(auth_type=auth_type, 
                                           google_cred_path=google_cred_path ,
                                           google_project_id=google_project_id,
                                           google_storage_api_key=google_storage_api_key
                                           )
                case other:
                    logger.error('Dont know how to handle authentication for google-cloud,auth type %s', auth_type)
        case other: ##Could be custom config-site. So read the site-auth configs as it is as pass them as a dictionary  
            logger.debug('Site Authentication Type is '+ auth_type)
            #eturn a list of name, value pairs for the options in the content-site-auth section
            auth_config = dict(config.items('content-site-auth'))
            site_auth=siteAuth(auth_type=auth_type,auth_config=auth_config)

    #Instantiate the vector db object. This will return a vectorDb derived class based on the module name
    vector_db = initializeVectorDb.initialize( vectordb_module = vectordb_module,
                                            vectordb_config = vectordb_config,
                                            content_site_name = content_site_name,
                                            src_path = src_path, 
                                            src_path_for_results = src_path_for_results
                                            )
    
    llm_service = initializeLlmService.initialize(llm_service_module = llm_service_module, 
                                                  llm_service_config = llm_service_config)
                            
    #Initialize the content site handler. The returned oject is content site specific (azure, aws,filepath) handler
    contentSite = initializeContentSite.initialize(content_site_module=content_site_module,
                                                   src_type=src_type,
                                                   content_site_name=content_site_name,
                                                   src_path=src_path,
                                                   src_path_for_results=src_path_for_results,
                                                   working_directory=working_directory,
                                                   index_log_directory=index_log_directory,
                                                   site_auth=site_auth,
                                                   vector_db = vector_db,
                                                   llm_service = llm_service,
                                                   do_not_read_dir_list = do_not_read_dir_list,
                                                   do_not_read_file_list = do_not_read_file_list)
    
    #contentSite.connect()
    if operation == 'index':
        contentSite.index(no_of_processes = no_of_processes)
    elif operation == 'testconnection': ## This is a connection test , so dont call index process, only connect
        logger.info("This is a connection test so not indexing")
        contentSite.testConnect()
