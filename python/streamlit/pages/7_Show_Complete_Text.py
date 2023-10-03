import streamlit as st
import os
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import sin, cos, pi
import umap

from unittest import result
import os
import sys
import json
import math
import logging
import configparser
from importlib import import_module
import urllib.parse

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer

import plotly.express as px
import plotly.graph_objects as go

aiwhispr_home =os.environ['AIWHISPR_HOME']
aiwhispr_logging_level = os.environ['AIWHISPR_LOG_LEVEL']

if (aiwhispr_logging_level == "Debug" or aiwhispr_logging_level == "DEBUG"):
   logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
elif (aiwhispr_logging_level == "Info" or aiwhispr_logging_level == "INFO"):
   logging.basicConfig(level = logging.INFO,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
elif (aiwhispr_logging_level == "Warning" or aiwhispr_logging_level == "WARNING"):
   logging.basicConfig(level = logging.WARNING,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
elif (aiwhispr_logging_level == "Error" or aiwhispr_logging_level == "ERROR"):
   logging.basicConfig(level = logging.ERROR,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')
else:   #DEFAULT logging level is DEBUG
   logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(process)d] %(message)s')


curr_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(curr_dir)
os.getcwd()

sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../../base-classes")
sys.path.append("../../llm-service")
sys.path.append("../../vectordb")
sys.path.append("../../common-functions")
sys.path.append("../../common-objects")
from aiwhisprBaseClasses import baseLlmService, vectorDb 
import aiwhisprConstants

def deg2rad(deg):
    return deg * pi / 180

class urlLinkHandlerStreamlit:
   model:baseLlmService
   vector_db:vectorDb
   limit_hits=25
   content_site_name:str
   src_path:str
   src_path_for_results:str
   logger=logging.getLogger(__name__)
   vector_angle_radians = [] 
   doc_vectors=[]
   doc_ids=[]
   query_vector = []

   def setup(self,llm_service_module:str, vectordb_module:str, llm_service_config:dict, vectordb_config:dict, content_site_name:str,src_path:str,src_path_for_results:str):
      llmServiceMgr = import_module(llm_service_module)
      vectorDbMgr = import_module(vectordb_module)

      self.vector_db = vectorDbMgr.createVectorDb(vectordb_config=vectordb_config,
                                          content_site_name = content_site_name,
                                          src_path = src_path,
                                          src_path_for_results = src_path_for_results)

      self.vector_db.connect()
      self.content_site_name = content_site_name
      self.src_path = src_path
      self.src_path_for_results = src_path_for_results

      self.model= llmServiceMgr.createLlmService(llm_service_config)
      self.model.connect()

   def getExtractedText(self,content_path:str):
      return self.vector_db.getExtractedText(self.content_site_name, content_path)

      

myUrlLinkHandler = []


def setup(configfile):
    
    #interpolation is set to None to allow reading special symbols like %
    config =  configparser.ConfigParser(interpolation=None)
    config.read(configfile)

    #Read the content site configs
    content_site_name = config.get('content-site','sitename')
    src_path = config.get('content-site','srcpath')
    src_path_for_results = config.get('content-site','displaypath')
    ##VectorDB Service
    vectordb_config = dict(config.items('vectordb'))
    vectordb_module = config.get('vectordb','vectorDbModule')
    ##LLM Service
    llm_service_config = dict(config.items('llm-service'))
    llm_service_module = config.get('llm-service', 'llmServiceModule')
    myUrlLinkHandler[0].setup(llm_service_module, vectordb_module, llm_service_config, vectordb_config, content_site_name,src_path,src_path_for_results)



st.session_state.canDisplayExtractedText=True
# get the value of the PATH environment variable
try:
    aiwhispr_home = os.environ['AIWHISPR_HOME']
except:
    print("Could not read environment variable AIWHISPR_HOME, exiting....")
    st.session_state.canDisplayExtractedText=False

try:
    query_params = st.experimental_get_query_params()
    if len(query_params) == 0:
        st.write("### Did not receive any query parameters in the URL link ###")
        st.write("This page is meant to be reached through search result URLs")
        st.session_state.canDisplayExtractedText=False
except:
    st.write("### An exception occured when trying to get query parameters in the URL ###")
    st.session_state.canDisplayExtractedText=False
else:
    try:
        configfile=query_params['configfile'][0]
        contentpath=query_params['contentpath'][0]
    except Exception as err:
        st.write(err)
        st.session_state.canDisplayExtractedText=False

    st.session_state.config_filepath=configfile

    if st.session_state.canDisplayExtractedText == True:

        image = Image.open(os.path.join(aiwhispr_home, 'python','streamlit', 'static', 'aiwhispr_logo_results.png'))
        st.image(image)
        st.header('AIWhispr - This page will display the full text of the result you have selected')
        
        myUrlLinkHandler.append(urlLinkHandlerStreamlit())
        setup(configfile)
        extracted_text = myUrlLinkHandler[0].getExtractedText(content_path=contentpath)
        st.write("### EXTRACTED TEXT ###")
        st.write(extracted_text)

        #Get all the unique words and get their encoding
        my_text_data = {'Text': [extracted_text]}
        extracted_text_dataframe = pd.DataFrame(my_text_data)

        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform(extracted_text_dataframe['Text'])
        unique_words = vectorizer.get_feature_names_out()

        unique_words_vectors = []
        for word in unique_words:
            word_vector = myUrlLinkHandler[0].model.encode(word)
            unique_words_vectors.append(word_vector)

        #PCA for all the unique words
        pca = PCA()
        pipe = Pipeline([('scaler', StandardScaler()), ('pca', pca)])
        embedding_array = np.array(unique_words_vectors)
        Xt = pca.fit_transform(embedding_array)
        st.write("### PCA MAP FOR UNIQUE WORDS IN THIS DOCUMENT ###")
        #PCA using Plotly
        pca_data = go.Scatter3d(x=Xt[:,0], y=Xt[:,1], z=Xt[:,2],hovertext=unique_words, mode='markers')
        pca_data_fig = go.Figure(pca_data)
        st.plotly_chart(pca_data_fig)
        