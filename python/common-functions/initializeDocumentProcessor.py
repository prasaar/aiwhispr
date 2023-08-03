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

def initialize(content_file_suffix:str,downloaded_file_path:str):
    logger = logging.getLogger(__name__)
    logger.debug('initializing with content_file_suffix: ' + content_file_suffix)
    #Return the prcessor for the file type  
    match content_file_suffix:
        case '.txt' | '.csv' | '.text' | '.py' | '.js' | '.php' | '.sh' | '.c' | '.pl' | '.cpp' | '.cs' | '.h' | '.java' | '.swift':
            logger.debug('in initialize : returning a text document processor')
            docProcessor = aiwhisprTextDocProcessor(downloaded_file_path)
            return docProcessor
        #case .xls' | '.xlsx'
            #return aiwhisprMSXlsDocProcessor(downloaded_file_path)
        #case '.doc' | '.docx'
            #return aiwhisprMSWordDocProcessor(downloaded_file_path)
        #case '.ppt' | '.pptx'
            #return aiwhisprMSPptDocProcessor(downloaded_file_path)
        #case '.pdf'
            #return aiwhisprPdfDocProcessor(downloaded_file_path)
        #case '.wiki'
            #return aiwhisprWikiDocProcessor(downloaded_file_path)
        #case '.xml'
            #return aiwhisprXmlDocProcessor(downloaded_file_path)
        #case '.md'
            #return aiwhisprMdDocProcessor(downloaded_file_path)
        case other:
            logger.critical('Document Processing Class does not exist. Cannot handle the file with suffix: ' + content_file_suffix + ' for file ' + downloaded_file_path)
