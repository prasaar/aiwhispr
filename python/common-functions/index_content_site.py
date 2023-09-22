import json
import os
import glob
import sys
import typesense
import time
import datetime
import re
import getopt
import configparser
import io
import uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from datetime import datetime, timedelta

aiwhispr_home =os.environ['AIWHISPR_HOME']
aiwhispr_logging_level = os.environ['AIWHISPR_LOG_LEVEL']
print("AIWHISPR_HOME=%s", aiwhispr_home)
print("LOGGING_LEVEL", aiwhispr_logging_level)

import logging

if (aiwhispr_logging_level == "Debug" or aiwhispr_logging_level == "DEBUG"):
   logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
elif (aiwhispr_logging_level == "Info" or aiwhispr_logging_level == "INFO"):
   logging.basicConfig(level = logging.INFO,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
elif (aiwhispr_logging_level == "Warning" or aiwhispr_logging_level == "WARNING"):
   logging.basicConfig(level = logging.WARNING,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
elif (aiwhispr_logging_level == "Error" or aiwhispr_logging_level == "ERROR"):
   logging.basicConfig(level = logging.ERROR,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
else:   #DEFAULT logging level is DEBUG
   logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')

curr_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(curr_dir)
os.getcwd()
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-functions")
import index_content_site_for_config


def main(argv):
   logger = logging.getLogger(__name__)
   configfile = ''
   typesense_hostname = ''
   typesense_portnumber = ''
   typesense_key = ''
   site_name = ''
   src_type = ''
   src_path = ''
   src_path_for_results = ''
   auth_type = ''
   sas_token = ''
   site_userid = ''
   site_password = ''

   opts, args = getopt.getopt(argv,"hC:A:",["configfile=","all="])
   for opt, arg in opts:
      if opt == '-h':
         print('index_content_site.py -C <content_site_config_file>' )
         print(' Or ' )
         print('index_content_site.py -A <path_to_directory_with_all_content_site_config_files>')
         sys.exit()
      elif opt in ("-C", "--configfile"):
         configfile = arg
         logger.info(configfile)
         index_content_site_for_config.index(configfile=configfile,operation='index')
      elif opt in ("-A", "--all"):
         configfiledir = arg
         globsearchpath = configfiledir + '/*.cfg'
         myconfigfilelist = [f for f in glob.glob(globsearchpath)]
         for configfile in myconfigfilelist:
             print('##Config File : ',configfile)
             logger.info(configfile)
             index_content_site_for_config.index(configfile=configfile,operation='index')

if __name__ == "__main__":
   main(sys.argv[1:])

