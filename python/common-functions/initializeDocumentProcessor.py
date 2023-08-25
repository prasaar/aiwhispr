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

import aiwhisprMSdocxDocProcessor
import aiwhisprMSpptxDocProcessor
import aiwhisprMSxlsxDocProcessor
import aiwhisprPdfDocProcessor
import aiwhisprTextDocProcessor

import aiwhisprConstants

import logging


# This is a dictionary that maps the file suffix to the module that can process the document
# Edit this when you add a module to handle a new document type (.suffix)
# The python module is loaded dynamically
DOC_PROCESSOR={
    '.txt': aiwhisprTextDocProcessor.getDocProcessor() ,
    '.csv': aiwhisprTextDocProcessor.getDocProcessor() ,
    '.py':  aiwhisprTextDocProcessor.getDocProcessor() ,
    '.js':  aiwhisprTextDocProcessor.getDocProcessor() ,
    '.php': aiwhisprTextDocProcessor.getDocProcessor() ,
    '.sh':  aiwhisprTextDocProcessor.getDocProcessor() ,
    '.c':   aiwhisprTextDocProcessor.getDocProcessor() ,
    '.pl':  aiwhisprTextDocProcessor.getDocProcessor() ,
    '.cpp': aiwhisprTextDocProcessor.getDocProcessor() ,
    '.cs':  aiwhisprTextDocProcessor.getDocProcessor() ,
    '.h':   aiwhisprTextDocProcessor.getDocProcessor() ,
    '.java': aiwhisprTextDocProcessor.getDocProcessor() ,
    '.swift': aiwhisprTextDocProcessor.getDocProcessor() ,
    '.pdf':  aiwhisprPdfDocProcessor.getDocProcessor() ,
    '.docx': aiwhisprMSdocxDocProcessor.getDocProcessor() ,
    '.xlsx': aiwhisprMSxlsxDocProcessor.getDocProcessor() ,
    '.pptx': aiwhisprMSpptxDocProcessor.getDocProcessor() 
}


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))


def initialize(content_file_suffix:str,downloaded_file_path:str):
    logger = logging.getLogger(__name__)
    logger.debug('initializing with content_file_suffix: ' + content_file_suffix)
    try:
        docProcessor = DOC_PROCESSOR[content_file_suffix]
        if docProcessor != None:
            docProcessor.setDownloadFilePath(downloaded_file_path)
    except:
        logger.error("No document processing  module name found for the file suffix: %s", content_file_suffix)
    
    return docProcessor

