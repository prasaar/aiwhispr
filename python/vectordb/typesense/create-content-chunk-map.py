import json
import os
import sys
import typesense
import time
import datetime
import re
import logging
import getopt

def main(argv):
   typesense_hostname = ''
   typesense_portnumber = ''
   typesense_key = ''
   full_path_to_backup_directory = ''
   opts, args = getopt.getopt(argv,"hK:H:P:B:",["key=","hostname=","portnumber=","backupdirpath="])
   for opt, arg in opts:
      if opt == '-h':
         print ('create-content-map-typesense-server.py -K <typesense_admin_key> -H <hostname_or_ip_of_server> -P <server_port>')
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

   client = typesense.Client({
    'api_key': typesense_key,
    'nodes': [{
        'host': typesense_hostname,
        'port': typesense_portnumber,
        'protocol': 'http'
    }],
    'connection_timeout_seconds': 600
   })

   # Create a collection
   #We are not creating an 'id' (unique id)  field. It will be provided in insert statements by the client
   #We expect id to be in the format <site-name>/<extracted-file_directory-name>/<chunk-files-directory>/<chunk-id>
   create_response = client.collections.create({
       "name": "content_chunk_map",
       "fields": [
   #SITE_NAME IS USED TO DEFINE THE SITE e.g. mas.gov.sg. THIS IS USED AS  FILTERING CRITERIA WHEN YOU WANT TO SEPRATE SEARCH BASED ON DIFFERENT SITES
           {"name": "content_site_name", "type": "string", "index": True  },
           #SRC_PATH IS USED TO DEFINE THE TOP SOURCE PATH FROM WHICH THE CONTENT RETRIEVER WILL START INDEXING CONTENT.
           # Example: For an Azure Blob/container it will be https://<storage_account>.blob.core.windows.net/<container>
           {"name": "src_path", "type": "string" , "optional": True, "index": False},
           #SRC_PATH_FOR_RESULTS is used as the prefix instead of SRC_PATH when displaying the link to content in the search results
           # Example: SRC_PATH for Azure Blob/container https://<storage_account>.blob.core.windows.net/<container>
           # The results can have fileshare prefix SRC_PATH_FOR_RESULTS for Azure Blob/container https://<storage_account>.file.core.windows.net/<container>
           {"name": "src_path_for_results", "type": "string", "optional": True, "index": False},
           # CONTENT_PATH is the path to the original content including file name under the SRC_PATH
           {"name": "content_path", "type": "string", "index": True},
           # LAST_EDIT_DATE is the last edit date read from source for the content
           {"name": "last_edit_date", "type": "float" , "optional": True, "index": False},
           # TAGS is an optional field that is used to store any tags associated with the content , seprated by "|" character
           {"name": "tags", "type": "string", "optional": True , "index": False},
           # TITLE is an optional field that is used to store any title for the content
           {"name": "title", "type": "string","optional": True, "index": True },
           # CHUNK_TEXT  is the text that will be used by the LLM
           {"name": "text_chunk", "type": "string", "optional": True , "index": False},
           # CHUNK_NO is a mandatory field, it is a running sequence of numbers for the sections of the text in the document. This is useful when the content is broken into sections.
           {"name": "text_chunk_no", "type": "int32", "optional": True, "index": False },
           #BELOW VECTOR FIELD : We are chossing a 768 dimension vector based on all_mpnet
           {"name": "vector_embedding", "type": "float[]", 'num_dim': 768, "optional": True , "index": True},
           # VECTOR_EMBEDDING_DATE is the last date  on which this content LLM Vector was created
           {"name": "vector_embedding_date", "type": "float" , "optional": True, "index": False},
       ],
       'default_sorting_field': 'content_path'
   })

   print('\n======CREATED content_map COLLECTION=======\n')
   print(create_response)


if __name__ == "__main__":
   main(sys.argv[1:])

