import os
import sys
import io
from datetime import datetime, timedelta
import pathlib
import time
import pypdf 

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-functions")
import aiwhisprConstants 
sys.path.append("../base-classes")
from aiwhisprBaseClasses import srcDocProcessor

import logging

class getDocProcessor(srcDocProcessor):
    logger = logging.getLogger(__name__)

    def __init__(self,downloaded_file_path=''):
        srcDocProcessor.__init__(self,downloaded_file_path)
        
    #public function
    def extractText(self):
        #This is a PDF Document text extractor

        self.logger.debug('This is a pdf file from which we will extract text')
        
        pdf_filepath = self.downloaded_file_path
        txt_filepath = self.extracted_text_file_path
        
        try:
            reader = pypdf.PdfReader(pdf_filepath)
            self.logger.debug("Instantiated reader for pdf file")
            text = ""
        except:
            self.logger.error("Could not instantiate a reader for pdf file: %s", pdf_filepath)
        else:
            try:
                f = open(txt_filepath, "w")
            except:
                self.logger.error('Could not not open a file to save the extracted text : %s', txt_filepath)
            else:
                try: 
                    for page in reader.pages:
                        try:
                            text = page.extract_text() + "\n"
                            self.logger.debug('Extracted Text from Pdf File : %s', pdf_filepath)
                            f.write(text)
                        except:
                            self.logger.error('Error while extracting a page from the pdf file : %s', pdf_filepath)

                except pypdf.errors.FileNotDecryptedError as error:
                    self.logger.error('File is encrypted, will not process : %s', pdf_filepath)
                except Exception as error:
                    self.logger.error('Error when processing this file : %s', pdf_filepath)
                finally:
                    self.logger.debug('Finished processing pdf file : %s', pdf_filepath)
    
                #Close text file after writing the extracted text
                f.close()

