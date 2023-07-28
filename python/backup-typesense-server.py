import json
import os
import sys
import typesense
import time
import datetime
import re
import logging
import getopt

#logging.basicConfig(level=logging.WARNING)

def main(argv):
   typesense_hostname = ''
   typesense_portnumber = ''
   typesense_key = ''
   full_path_to_backup_directory = ''
   opts, args = getopt.getopt(argv,"hK:H:P:B:",["key=","hostname=","portnumber=","backupdirpath="])
   for opt, arg in opts:
      if opt == '-h':
         print ('backup_typesense_server.py -K <typesense_admin_key> -H <hostname_or_ip_of_server> -P <server_port> -B <full_path_to_backup_directory>')
         sys.exit()
      elif opt in ("-K", "--key"):
         typesense_key = arg
      elif opt in ("-H", "--hostname"):
         typesense_hostname = arg
      elif opt in ("-P", "--portnumber"):
         typesense_portnumber = arg
      elif opt in ("-B", "--backupdirpath"):
         full_path_to_backup_directory = arg
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

