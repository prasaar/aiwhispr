import os
import sys
from importlib import import_module

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb, siteAuth, baseLlmService

sys.path.append("../common-objects")
sys.path.append("../content-site")



import logging

def initialize(content_site_module:str,
               src_type:str,
               content_site_name:str,
               src_path:str,
               src_path_for_results:str,
               working_directory:str,
               index_log_directory:str,
               site_auth:siteAuth,
               vector_db:vectorDb,
               llm_service:baseLlmService,
               do_not_read_dir_list:list = [], 
               do_not_read_file_list:list = []):
        logger = logging.getLogger(__name__)
        #Dynamically import module and instantiate
        contentSiteMgr = import_module(content_site_module)
        return   contentSiteMgr.createContentSite(content_site_name=content_site_name,
                                                  src_path=src_path,
                                                  src_path_for_results=src_path_for_results,
                                                  working_directory=working_directory,
                                                  index_log_directory=index_log_directory,
                                                  site_auth=site_auth,
                                                  vector_db = vector_db,
                                                  llm_service = llm_service,
                                                  do_not_read_dir_list=do_not_read_dir_list,
                                                  do_not_read_file_list=do_not_read_file_list)