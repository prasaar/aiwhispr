import os
import sys
from importlib import import_module

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb

sys.path.append("../common-objects")
sys.path.append("../vectordb")



import logging

def initialize(vectordb_module:str,
    vectordb_hostname:str,
    vectordb_portnumber:str,
    vectordb_key:str,
    content_site_name:str,
    src_path:str,
    src_path_for_results:str):
        #Dynamically import module and instantiate
        vectorDbMgr = import_module(vectordb_module)
        return   vectorDbMgr.createVectorDb(vectordb_hostname = vectordb_hostname,
                                            vectordb_portnumber = vectordb_portnumber,
                                            vectordb_key = vectordb_key,
                                            content_site_name = content_site_name,
                                            src_path = src_path, 
                                            src_path_for_results = src_path_for_results)