import os
import sys
import io
from datetime import datetime, timedelta
import pathlib
import time

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-functions")
import aiwhisprConstants 
sys.path.append("../base-classes")
from aiwhisprBaseClasses import srcDocProcessor

import logging

class getDocProcessor(srcDocProcessor):
    logger = logging.getLogger(__name__)

    def __init__(self,downloaded_file_path = ''): #A textDocProcessor can be startted with no file path if we are processing strings from in-mem objects
        srcDocProcessor.__init__(self,downloaded_file_path)
        
    #public function
    def extractText(self):
        ##Since the downloaded file is a text file we dont have to extract anything.
        ##We will use the downloaded file as source to create chunks
        self.logger.debug('This is a text file so there is nothing to extract. Setting extracted_text_file_path to downloaded_file_path')
        self.extracted_text_file_path = self.downloaded_file_path
