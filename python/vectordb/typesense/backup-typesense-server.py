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
   opts, args = getopt.getopt(argv,"hK:H:P:B:C:",["key=","hostname=","portnumber=","backupdirpath=","configfile="])
   for opt, arg in opts:
      if opt == '-h':
         print('backup_typesense_server.py -K <key> -H <hostname> -P <portnumber> -B <backupdirpath>')
         print(' OR ')
         print('backup_typesense_server.py -C <typesense-server.ini file full path> -B <backupdirpath>')
         sys.exit()
      elif opt in ("-K", "--key"):
         typesense_key = arg
      elif opt in ("-H", "--hostname"):
         typesense_hostname = arg
      elif opt in ("-P", "--portnumber"):
         typesense_portnumber = arg
      elif opt in ("-B", "--backupdirpath"):
         full_path_to_backup_directory = arg
      elif opt in ("-C", "--configfile"):
         configfile = arg
         config = configparser.ConfigParser()
         config.read(configfile)
         typesense_hostname = config.get('server', 'api-address') 
         typesense_portnumber = config.get('server', 'api-port') 
         typesense_key = config.get('server', 'api-key') 
         

   print ('Typsense Server Host is ', typesense_hostname)
   print ('Typsense Server Port is ', typesense_portnumber)
   print ('Typsense Server Key is ', typesense_key)
   print ('Typsense Backup Directory Path is ', full_path_to_backup_directory)

   client = typesense.Client({
    'api_key': typesense_key,
    'nodes': [{
        'host': typesense_hostname,
        'port': typesense_portnumber,
        'protocol': 'http'
    }],
    'connection_timeout_seconds': 600
   })
   response = client.operations.perform('snapshot', {'snapshot_path': full_path_to_backup_directory})
   print(response)


if __name__ == "__main__":
   main(sys.argv[1:])

