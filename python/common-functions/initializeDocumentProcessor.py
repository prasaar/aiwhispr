import os
import sys
import configparser
import os, uuid
from importlib  import import_module

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../document-processor")

import aiwhisprConstants

import logging

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))


def initialize(content_file_suffix:str,downloaded_file_path:str):
    logger = logging.getLogger(__name__)
    logger.debug('initializing with content_file_suffix: ' + content_file_suffix)
    module_name = aiwhisprConstants.DOCPROCESSORMODULES[content_file_suffix] 
    if module_name == None:
        logger.error("No document processing  module name found for the file suffix: %s", content_file_suffix)
    else:
      logger.debug("Will load module: %s for the file suffix: %s", module_name, content_file_suffix)
      docProcessorModule = import_module(module_name)
      docProcessor =  docProcessorModule.getDocProcessor(downloaded_file_path) 
      return docProcessor

