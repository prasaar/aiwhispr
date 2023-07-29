import json
import os
import sys
import typesense
import time
import datetime
import re
import logging
import getopt
import configparser
import io

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

   opts, args = getopt.getopt(argv,"hC:",["configfile="])
   for opt, arg in opts:
      if opt == '-h':
         print('index_site.py -C <site_config_file>' )
         sys.exit()
      elif opt in ("-C", "--configfile"):
         configfile = arg
         config = configparser.ConfigParser(interpolation=None)
         config.read(configfile)
         typesense_hostname = config.get('vectordb', 'api-address') 
         typesense_portnumber = config.get('vectordb', 'api-port') 
         typesense_key = config.get('vectordb', 'api-key') 
         site_name = config.get('site','sitename')
         src_type = config.get('site','srctype')
         src_path = config.get('site','srcpath')
         src_path_for_results = config.get('site','displaypath')
         if(src_type != 'filepath'):
             auth_type= config.get('auth','authtype')
             if( ( (src_type == 'azureblob') or (src_type == 's3') )  and ( auth_type == 'sas' ) ):
                 sas_token = config.get('auth','sastoken')
             else:
                 site_userid = config.get('auth','userid')
                 site_password = config.get('auth','password')

   print ('VectorDB Server Host is ', typesense_hostname)
   print ('VectorDB Server Port is ', typesense_portnumber)
   print ('VectorDB Server Key is ', typesense_key)
   print ('Site Name is ', site_name)
   print ('Site Source Type is ', src_type)
   print ('Site Source Path is ', src_path)
   print ('Site Source Display Path is ', src_path_for_results)
   print ('Site Authentication Type is ', auth_type)
   print ('Site Authentication SAS Token is ', sas_token)
   print ('Site User Id is ', site_userid)
   print ('Site Password is ',site_password)


if __name__ == "__main__":
   main(sys.argv[1:])

