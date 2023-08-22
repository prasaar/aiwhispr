import io
import os
import sys


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))

sys.path.append("../common-functions")

import logging

class textDownloader(object):

    def write_content(self, text_content:str,download_file_path:str):
        logger = logging.getLogger(__name__)
        try:
            dest = open(download_file_path, 'w', encoding="utf-8")
        except:
            logger.error("Could not open files %s  copied to %s", content_path, download_file_path)
        else:
            logger.debug("Writing text %s to file %s", text_content, download_file_path)
            dest.write(text_content)
            dest.close()