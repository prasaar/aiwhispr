import io
import os
import sys
import shutil

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../common-functions")
import aiwhisprConstants 
import logging

class filepathDownloader(object):

    def download_content_file(self, content_path:str,download_file_path:str):
        logger = logging.getLogger(__name__)
        try:
            fsrc = open(content_path, 'rb')
            dest = open(download_file_path, 'wb')
        except:
            logger.error("Could not open files %s  copied to %s", content_path, download_file_path)
        else:
            logger.debug("Cppying file %s to %s", content_path, download_file_path)
            shutil.copyfileobj(fsrc, dest, aiwhisprConstants.BUFFERSIZEFORCOPY)
            fsrc.close()
            dest.close()
