import os
import sys
import io
from datetime import datetime, timedelta
import pathlib
import time
import textract

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-functions")
import aiwhisprConstants 
sys.path.append("../base-classes")
from aiwhisprBaseClasses import srcDocProcessor

import logging

class getDocProcessor(srcDocProcessor):
    logger = logging.getLogger(__name__)

    def __init__(self,downloaded_file_path):
        srcDocProcessor.__init__(self,downloaded_file_path)
        
    #public function
    def extractText(self):
        #This is a MS Office 2007 onwards .xlsx document text extractor

        self.logger.debug('This is a .xlsx file from which we will extract text')
        
        xlsx_filepath = self.downloaded_file_path
        txt_filepath = self.extracted_text_file_path

        text = textract.process(xlsx_filepath).decode('utf-8')
        self.logger.debug('Extracted text from xlsx file')
        try:
            f = open(txt_filepath, "w")
        except:
            self.logger.error('Could not not open a file to save the extracted text : %s', txt_filepath)
        else:
            f.write(text)
            f.close()