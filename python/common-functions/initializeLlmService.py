import os
import sys
from importlib import import_module

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../base-classes")

sys.path.append("../common-objects")
sys.path.append("../llm-service")


import logging

def initialize(llm_service_module:str, llm_service_config:dict):
        #Dynamically import module and instantiate
        llmServiceMgr = import_module(llm_service_module)
        return   llmServiceMgr.createLlmService(llm_service_config = llm_service_config)