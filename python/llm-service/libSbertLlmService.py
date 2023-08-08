from importlib import import_module
import os
from pyexpat import model
import sys
import json
import math
import string
import re
import logging
import getopt
import configparser

curr_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(curr_dir)
os.getcwd()
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../base-classes")
sys.path.append("../llm-service")

from aiwhisprBaseClasses import baseLlmService

import logging

class createLlmService(baseLlmService):

   model_service = import_module("sentence_transformers")
   model

   def __init__(self,model_family, model_name, llm_service_api_key):
      baseLlmService.__init__(self, model_family,model_name, llm_service_api_key)

   def connect(self):
      self.model = self.model_service.SentenceTransformer(self.model_name)

   def encode(self, in_text:str):
      vector_embedding =  self.model.encode(in_text)
      vector_embedding_as_list = vector_embedding.tolist()
      return vector_embedding_as_list