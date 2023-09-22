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
   #Import sentence_transformers which should have been installed
   model_service = import_module("sentence_transformers")
   model

   def __init__(self,llm_service_config):
      baseLlmService.__init__(self, llm_service_config=llm_service_config, module_name='libSbertLlmService')
      self.model_family = llm_service_config['model-family']
      self.model_name = llm_service_config['model-name']
   
   def testConnect(self):   
      mymodel = self.model_service.SentenceTransformer(self.model_name)
      myembedding= mymodel.encode("Test Connection for SBert")
   
   def connect(self):
      self.model = self.model_service.SentenceTransformer(self.model_name)

   def encode(self, in_text:str):
      vector_embedding =  self.model.encode(in_text)
      vector_embedding_as_list = vector_embedding.tolist()
      return vector_embedding_as_list