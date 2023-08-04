import os
import sys
import configparser
import os, uuid

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")

import aiwhisprConstants

import logging

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../common-objects")
from aiwhisprTextDocProcessor import aiwhisprTextDocProcessor
from aiwhisprPdfDocProcessor import aiwhisprPdfDocProcessor
from aiwhisprMSdocxDocProcessor import aiwhisprMSdocxDocProcessor
from aiwhisprMSxlsxDocProcessor import aiwhisprMSxlsxDocProcessor
from aiwhisprMSpptxDocProcessor import aiwhisprMSpptxDocProcessor

def initialize(content_file_suffix:str,downloaded_file_path:str):
    logger = logging.getLogger(__name__)
    logger.debug('initializing with content_file_suffix: ' + content_file_suffix)
    #Return the prcessor for the file type  
    if content_file_suffix in aiwhisprConstants.TXTFILEXTN:
            logger.debug('in initialize : returning a text document processor for %s', downloaded_file_path)
            docProcessor = aiwhisprTextDocProcessor(downloaded_file_path)
            return docProcessor
    elif content_file_suffix == '.pdf':
            logger.debug('in initialize : returning a pdf document processor for %s', downloaded_file_path)
            docProcessor = aiwhisprPdfDocProcessor(downloaded_file_path)
            return docProcessor
    elif (content_file_suffix == '.xlsx'):
            logger.debug('in initialize : returning a xlsx document processor for %s', downloaded_file_path)
            docProcessor = aiwhisprMSxlsxDocProcessor(downloaded_file_path)
            return docProcessor
    #elif (content_file_suffix == '.xls'):
    #        return aiwhisprMSxlsDocProcessor(downloaded_file_path)
    elif (content_file_suffix == '.docx'):
            logger.debug('in initialize : returning a docx document processor for %s', downloaded_file_path)
            docProcessor = aiwhisprMSdocxDocProcessor(downloaded_file_path)
            return docProcessor
    #elif (content_file_suffix == '.doc'):
    #        return aiwhisprMSdocDocProcessor(downloaded_file_path)
    elif (content_file_suffix == '.pptx'):
            logger.debug('in initialize : returning a pptx document processor for %s', downloaded_file_path)
            docProcessor = aiwhisprMSpptxDocProcessor(downloaded_file_path)
            return docProcessor
    #elif (content_file_suffix == '.ppt'):
    #        return aiwhisprMSpptDocProcessor(downloaded_file_path)
    #elif (content_file_suffix == '.wiki'):
            #return aiwhisprWikiDocProcessor(downloaded_file_path)
    #elif (content_file_suffix == '.xml'):
            #return aiwhisprXmlDocProcessor(downloaded_file_path)
    #elif (content_file_suffix == '.md'):
            #return aiwhisprMdDocProcessor(downloaded_file_path)
    else:
        logger.critical('Document Processing Class does not exist. Cannot handle the file with suffix: ' + content_file_suffix + ' for file ' + downloaded_file_path)
        return None
