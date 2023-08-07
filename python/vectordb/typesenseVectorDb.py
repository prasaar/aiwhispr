import os
import sys
import io
import uuid
from datetime import datetime, timedelta
import pathlib

import json
import typesense


curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")
from aiwhisprBaseClasses import vectorDb

import aiwhisprConstants 

import logging

class createVectorDb(vectorDb):

    def __init__(self,vectordb_hostname,vectordb_portnumber, vectordb_key, content_site_name:str,src_path:str,src_path_for_results:str):
        vectordbClient = typesense.Client({
            'api_key': vectordb_key,
            'nodes': [
                {
                'host': vectordb_hostname,
                'port': vectordb_portnumber,
                'protocol': 'http'
                },
        ],
        'connection_timeout_seconds': 10
        })

