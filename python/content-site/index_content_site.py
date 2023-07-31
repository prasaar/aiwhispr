import json
import os
import glob
import sys
import typesense
import time
import datetime
import re
import logging
import getopt
import configparser
import io
import uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from datetime import datetime, timedelta

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-functions")
import index_content_site_for_config

#logging.basicConfig(level=logging.WARNING)


def main(argv):
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
         index_content_site_for_config.index(configfile)
      elif opt in ("-A", "--all"):
         configfiledir = arg
         globsearchpath = configfiledir + '/*.cfg'
         myconfigfilelist = [f for f in glob.glob(globsearchpath)]
         for configfile in myconfigfilelist:
             print('##Config File : ',configfile)
             index_content_site_for_config.index(configfile)


if __name__ == "__main__":
   main(sys.argv[1:])

