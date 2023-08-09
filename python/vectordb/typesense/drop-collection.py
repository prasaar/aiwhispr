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

#logging.basicConfig(level=logging.WARNING)

def main(argv):
   typesense_hostname = ''
   typesense_portnumber = ''
   typesense_key = ''
   configfile = ''
   full_path_to_backup_directory = ''
   opts, args = getopt.getopt(argv,"hK:H:P:B:C:",["key=","hostname=","portnumber="])
   for opt, arg in opts:
      if opt == '-h':
         print('drop-collection.py -K <typesense-key> -H <typesense-hostname> -P <portnumber> ')
         print('THIS WILL REMOVE DATA AND SCHEMA RELATED TO ALL CONTENT SITES')
         sys.exit()
      elif opt in ("-K", "--key"):
         typesense_key = arg
      elif opt in ("-H", "--hostname"):
         typesense_hostname = arg
      elif opt in ("-P", "--portnumber"):
         typesense_portnumber = arg

   print ('Typsense Server Host is ', typesense_hostname)
   print ('Typsense Server Port is ', typesense_portnumber)
   print ('Typsense Server Key is ', typesense_key)

   txt = input("THIS WILL REMOVE DATA AND SCHEMA RELATED TO ALL CONTENT SITES.\nDo you really want to continue(Y/N): ")
   if txt == "Y" or txt == "y":

       client = typesense.Client({
        'api_key': typesense_key,
        'nodes': [{
            'host': typesense_hostname,
            'port': typesense_portnumber,
            'protocol': 'http'
        }],
        'connection_timeout_seconds': 600
       })
       response = client.collections['content_chunk_map'].delete()
       print(response)

if __name__ == "__main__":
   main(sys.argv[1:])

