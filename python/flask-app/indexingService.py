from flask import Flask,redirect, url_for, request
import os
import sys
import json
import math
import string
import re
import logging
import getopt
import configparser
from importlib import import_module
import urllib.parse

curr_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(curr_dir)
os.getcwd()

sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../base-classes")
from aiwhisprBaseClasses import baseLlmService, vectorDb, siteAuth

sys.path.append("../llm-service")
sys.path.append("../vectordb")
sys.path.append("../common-functions")
import initializeContentSite
import initializeVectorDb
import initializeLlmService

sys.path.append("../common-objects")
import aiwhisprConstants


aiwhispr_home =os.environ['AIWHISPR_HOME']
aiwhispr_logging_level = os.environ['AIWHISPR_LOG_LEVEL']
print("AIWHISPR_HOME=%s", aiwhispr_home)
print("LOGGING_LEVEL", aiwhispr_logging_level)

contentSiteHandlers=[]

import logging

if (aiwhispr_logging_level == "Debug" or aiwhispr_logging_level == "DEBUG"):
   logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
elif (aiwhispr_logging_level == "Info" or aiwhispr_logging_level == "INFO"):
   logging.basicConfig(level = logging.INFO,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
elif (aiwhispr_logging_level == "Warning" or aiwhispr_logging_level == "WARNING"):
   logging.basicConfig(level = logging.WARNING,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
elif (aiwhispr_logging_level == "Error" or aiwhispr_logging_level == "ERROR"):
   logging.basicConfig(level = logging.ERROR,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
else:   #DEFAULT logging level is DEBUG
   logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')


def index(configfile:str,operation:str):
    global contentSiteHandlers

    if len(configfile) == 0:
        logging.error("No config file provided. Exiting...")
        sys.exit()
    if len(operation) == 0:
        logging.error("No  operation argument provided. Exiting...")
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
        logging.error("Operation %s not supported. Exiting...", operation)
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

    logging.info("Started indexing using config file")
    #Read the content site configs
    content_site_name = config.get('content-site','sitename')
    src_type = config.get('content-site','srctype')
    src_path = config.get('content-site','srcpath')
    src_path_for_results = config.get('content-site','displaypath')
    content_site_module = config.get('content-site','contentSiteModule')
    

    do_not_read_dir_list=[]
    do_not_read_file_list = []

    
    logging.info('Site Name is '+ content_site_name)
    logging.info('Site Source Type is '+ src_type)
    logging.info('Site Source Path is '+ src_path)
    logging.info('Site Source Display Path is '+ src_path_for_results)
    logging.info('Content Site Module is: %s', content_site_module)
    
    #Read the vector database configs
    vectordb_config = dict(config.items('vectordb'))
    vectordb_module = config.get('vectordb','vectorDbModule')
    logging.info('VectorDB Module is '+ vectordb_module)
    logging.info('Vectordb Config is : %s', str(vectordb_config))
    
    #Read config for local section 
    working_directory = config.get('local','working-dir')
    index_log_directory = config.get('local','index-dir')
    logging.info('Local working directory  is '+working_directory)
    logging.info('Local index directory is '+index_log_directory)
    try:
        indexing_processes = config.get('local','indexing-processes')
        if indexing_processes == '' or indexing_processes == None:
           no_of_processes = 1
        else:
           no_of_processes = int(indexing_processes)
    except configparser.NoOptionError as exc:
        logging.info("indexing-process option is not defined, so assuming a single process")
        no_of_processes = 1
    except:
        logging.error("Problem when reading no_of_indexing_process")
        no_of_processes = 1
    logging.info('Local number of indexing process to run '  + str(no_of_processes) )

    #Read config for the LLM Service
    llm_service_config = dict(config.items('llm-service'))
    llm_service_module = config.get('llm-service', 'llmServiceModule')
    logging.info("LLM Service Module Name is %s", llm_service_module)
    logging.info('LLM Service Config is : %s', str(llm_service_config))
    
    #Read configs for the site-authentication
    match src_type:
        case 'index-service':
            auth_type= config.get('content-site-auth','authtype')
            match auth_type:
                case 'index-service-key':     
                    index_service_access_key_id = config.get('content-site-auth','access-key-id')
                
    site_auth=siteAuth(auth_type=auth_type,index_service_access_key_id=index_service_access_key_id)

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
    
    contentSiteHandlers.append(contentSite)

    if operation == 'index':
        contentSiteHandlers[0].index(no_of_processes = no_of_processes)
    elif operation == 'testconnection': ## This is a connection test , so dont call index process, only connect
        logging.info("This is a connection test so not indexing")
        contentSiteHandlers[0].testConnect()


##### Flask #####
app = Flask(__name__)
@app.route('/')
def say_hello():
   return '<center>Welcome. Your local AIWhispr  service is up</center>'

#This is the search function that takes the message and inserts int
@app.route('/index',methods = ['POST'])
def semantic_index():
    content=request.json
    print(content)
    input_msg=json.dumps(content)
    return contentSiteHandlers[0].process(input_msg)


#Main
if __name__ == '__main__':
   
   configfile=''
   serviceportnumber=0

   opts, args = getopt.getopt(sys.argv[1:],"hC:H:P:",["configfile=","servicehostip==","serviceportnumber="])
   for opt, arg in opts:
      if opt == '-h':
         print('This uses flask so provide full path to python3 for the python script and the config file in command line argument')
         print('<full_directory_path>/searchService.py -C <config file of the content site> -H<hostip> -P<flask port number on which this service should listen> ' )
         sys.exit()
      elif opt in ("-C", "--configfile"):
         configfile = arg
      elif opt in ("-H", "--servicehostip"):
         servicehostip = arg
      elif opt in ("-P", "--serviceportnumber"):
         serviceportnumber = int(arg)

   index(configfile,operation="index")
   app.run(debug=True,host=servicehostip, port=serviceportnumber)

