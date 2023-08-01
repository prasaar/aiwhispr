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
logger = logging.getLogger(__name__)


import os
import sys

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb, siteAuth

sys.path.append("../common-objects")
from azureContentSite import azureContentSite

def initialize(content_file_suffix:str,downloaded_file_path:str):
    #First check if the file suffix can be handled  
    if ( content_file_suffix in aiwhisprConstants.FILEXTNLIST ):
        match content_file_suffix:
            case '.txt' | '.csv':
                return aiwhisprTextDocProcessor(downloaded_file_path)
            case '.xls' | '.xlsx'
                return aiwhisprMSXlsDocProcessor(downloaded_file_path)
            case '.doc' | '.docx'
                return aiwhisprMSWordDocProcessor(downloaded_file_path)
            case '.ppt' | '.pptx'
                return aiwhisprMSPptDocProcessor(downloaded_file_path)
            case '.pdf'
                return aiwhisprPdfDocProcessor(downloaded_file_path)
            case '.wiki'
                return aiwhisprWikiDocProcessor(downloaded_file_path)
            case '.xml'
                return aiwhisprXmlDocProcessor(downloaded_file_path)
            case '.md'
                 return aiwhisprMdDocProcessor(downloaded_file_path)
    else:
        logger.critical('Document Processing Class does not exist. Cannot handle the file with suffix: ' + content_file_suffix + ' for file ' + downloaded_file_path)
