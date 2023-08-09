import json
import os
import sys
import typesense
import time
import datetime
import re
import logging
import getopt
import math



def main(argv):
   typesense_hostname = ''
   typesense_portnumber = ''
   typesense_key = ''
   full_path_to_backup_directory = ''
   opts, args = getopt.getopt(argv,"hK:H:P:S:B:",["key=","hostname=","portnumber=","sitename=","backupfile="])
   for opt, arg in opts:
      if opt == '-h':
         print ('dump-content-map-typesense-server.py -K <typesense_admin_key> -H <hostname_or_ip_of_server> -P <server_port> -S <content-site-name> -B <backup_file_full_path>')
         sys.exit()
      elif opt in ("-K", "--key"):
         typesense_key = arg
      elif opt in ("-H", "--hostname"):
         typesense_hostname = arg
      elif opt in ("-P", "--portnumber"):
         typesense_portnumber = arg
      elif opt in ("-S", "--sitename"):
         content_site_name = arg
      elif opt in ("-B", "--backupfile"):
         backup_filename = arg
         

   print ('Typsense Server Host is ', typesense_hostname)
   print ('Typsense Server Port is ', typesense_portnumber)
   print ('Typsense Server Key is ', typesense_key)

   client = typesense.Client({
    'api_key': typesense_key,
    'nodes': [{
        'host': typesense_hostname,
        'port': typesense_portnumber,
        'protocol': 'http'
    }],
    'connection_timeout_seconds': 600
   })

   #search for  content_site_name 
   filter_by_conditions = 'content_site_name:=' + content_site_name
   search_parameters= {
            'q': content_site_name,
            'query_by': 'content_site_name',
            'exclude_fields': 'vector_embedding',
            'filter_by':filter_by_conditions
        }
   search_res = client.collections['content_chunk_map'].documents.search(search_parameters)

   ### Parameter to return no of pages per search query from typesense. Max allowed by Typesense is 250
   per_page =  250
   ###Total no of posts
   no_of_rows = search_res['found']
   if no_of_rows > 0:
       no_of_pages = math.ceil(no_of_rows/per_page)
   else:
       no_of_pages = 0

   print(no_of_pages,' pages have to be processed to process ', no_of_rows, ' records')

   page_no = 1
   
   f = open(backup_filename,"w")
   f.write("[\n")

   filter_by_conditions = 'content_site_name:=' + content_site_name

   while page_no <=  no_of_pages:
      search_parameters= {
            'q': content_site_name,
            'query_by': 'content_site_name',
            'per_page': per_page,
            'page': page_no,
            'filter_by':filter_by_conditions
      }
      
      content_chunk_map_page = client.collections['content_chunk_map'].documents.search(search_parameters)
      no_of_doc = len(content_chunk_map_page['hits'])
      i = 0
      while i < no_of_doc:
         f.write(str(content_chunk_map_page['hits'][i]['document']))
         f.write(",\n")
         i=i+1
      
      page_no = page_no + 1

   f.write("]")
   f.close()
           
if __name__ == "__main__":
   main(sys.argv[1:])

