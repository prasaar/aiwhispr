import os
import sys

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb, siteAuth

sys.path.append("../common-objects")
from azureContentSite import azureContentSite

import logging

def initialize(src_type:str,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb):
    logger = logging.getLogger(__name__)
    
    match src_type:
        case 'azureblob':
            logger.debug('azureContentSite instantiated')
            return azureContentSite(content_site_name=content_site_name,src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db)
