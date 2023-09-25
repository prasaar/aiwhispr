import streamlit as st
import os
from PIL import Image


from unittest import result
import os
import sys
import json
import math
import string
import re
import logging
import getopt
import configparser
from importlib import import_module
import urllib.parse

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

class searchHandler:
   model:baseLlmService
   vector_db:vectorDb
   limit_hits=25
   content_site_name:str
   src_path:str
   src_path_for_results:str
   logger=logging.getLogger(__name__)

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

   def search(self,input_query:str, result_format:str, textsearch_flag:str): 

      output_format = result_format      
      self.logger.debug("result format: %s", result_format)
      if output_format not in ['html','json']:
         self.logger.error("cannot handle this result format type")
      if textsearch_flag not in ['Y', 'N']:
         self.logger.error("text search flag should be a Y or N")

      self.logger.debug("get vector embedding for text:{%s}",input_query)
      query_embedding_vector =  self.model.encode(input_query)
      query_embedding_vector_as_list = query_embedding_vector
      vector_as_string = ' '. join(str(e) for e in query_embedding_vector_as_list)
      self.logger.debug("vector embedding:{%s}",vector_as_string)

      if textsearch_flag == 'Y':
         search_results = self.vector_db.search(self.content_site_name,query_embedding_vector_as_list, self.limit_hits ,input_query)
      else:
         search_results = self.vector_db.search(self.content_site_name,query_embedding_vector_as_list, self.limit_hits)
      
      
      display_html = '<div class="aiwhisprSemanticSearchResults">'
      display_json = []

      

      """""
        We should receive a JSON Object in the format 
        {"results": [ semantic_results{} ,text_results{}  ]}
       
         semantic_results / text_results will be a format 
         {
         "found" : int
         "type"  : semantic / text / image 
         "hits"  : []
         }
             
             hits[]  will be a list Example : hits[ {"result":{},   {"result":{} }]
            "result": {
               id: UUID,
               content_site_name: str,
               content_path:str,
               src_path:str,
               src_path_for_results,
               tags:str,
               text_chunk:str,
               text_chunk_no:int,
               title:int,
               last_edit_date:float,
               vector_embedding_date:float,
               match_score: float,
            }
      """""
      
      self.logger.debug('SearchService received search results from vectordb:')
      self.logger.debug(json.dumps(search_results))

      no_of_semantic_hits = search_results['results'][0]['found']
     

      i = 0
      while i < no_of_semantic_hits:
         chunk_map_record = search_results['results'][0]['hits'][i]
         content_site_name = chunk_map_record['content_site_name']
         record_id = chunk_map_record['id']
         content_path = chunk_map_record['content_path']
         src_path = chunk_map_record['src_path']
         #src_path_for_results = chunk_map_record['src_path_for_results']
         src_path_for_results = self.src_path_for_results
         text_chunk = chunk_map_record['text_chunk']
         title = chunk_map_record['title']
         score = str(chunk_map_record['match_score'])

         if output_format == 'html':
            
            if src_path_for_results[0:4] == 'http': 
               display_url = urllib.parse.quote_plus(src_path_for_results,safe='/:')  + '/' + urllib.parse.quote(content_path)
            else:
               display_url = src_path_for_results + '/' + content_path
            
       

            if len(text_chunk) <= aiwhisprConstants.HTMLSRCHDSPLYCHARS:
               display_text_chunk = text_chunk
            else:
               display_text_chunk = text_chunk[:(aiwhisprConstants.HTMLSRCHDSPLYCHARS -3)] + '...'
            
            if len(title) > 0: #Display title with link to content
                display_html = display_html + '<a href="' + display_url + '">' + title + '</a><br>'
            else:  #display the content path
               display_html = display_html + '<a href="' + display_url + '">' + content_path + '</a><br>'
            
            display_html = display_html + '<br><p> Semantic distance : ' + score +  '</pr><br>' + '<div><p>' + display_text_chunk + '</p></div><br>'
            
         if output_format == 'json':
            json_record = {} #Dict
            json_record['content_path'] = content_path
            json_record['id'] = record_id
            json_record['content_site_name'] = content_site_name
            json_record['src_path'] = src_path
            json_record['src_path_for_results'] = src_path_for_results
            json_record['text_chunk'] = text_chunk
            json_record['search_type'] = 'semantic'
            json_record['title'] = title
            ##Add this dict record in the list
            display_json.append(json_record)
      
         i = i + 1 
      
      display_html = display_html + '</div>'

      if textsearch_flag == "Y": ## Process second batch of results which are from the text search
         display_html = display_html + '<div class="aiwhisprTextSearchResults">'
         
         j = 0
         if len(search_results['results']) > 1: #Check that  text results are there.
                no_of_text_hits = len(search_results['results'][1]['hits'])
         else:
            self.logger.info('No Text Results returned')

         while j < no_of_text_hits:
            chunk_map_record = search_results['results'][1]['hits'][j]
            content_site_name = chunk_map_record['content_site_name']
            record_id = chunk_map_record['id']
            content_path = chunk_map_record['content_path']
            src_path = chunk_map_record['src_path']
            #src_path_for_results = chunk_map_record['src_path_for_results']
            src_path_for_results = self.src_path_for_results
            text_chunk = chunk_map_record['text_chunk']
            title = chunk_map_record['title']
               
            if output_format == 'html':

               if src_path_for_results[0:4] == 'http':
                  display_url = urllib.parse.quote_plus(src_path_for_results,safe='/:')  + '/' + urllib.parse.quote(content_path)
               else:
                  display_url = src_path_for_results + '/' + content_path

               if len(text_chunk) <= aiwhisprConstants.HTMLSRCHDSPLYCHARS:
                  display_text_chunk = text_chunk
               else:
                  display_text_chunk = text_chunk[:(aiwhisprConstants.HTMLSRCHDSPLYCHARS -3)] + '...'

               if len(title) > 0: #Display title with link to content
                  display_html = display_html + '<a href="' + display_url + '">' + title + '</a><br>'
               else:  #display the content path
                  display_html = display_html + '<a href="' + display_url + '">' + content_path + '</a><br>'

               display_html = display_html + '<div><p>' + display_text_chunk + '</p></div><br>'
               
            if output_format == 'json':
               json_record = {} #Dict
               json_record['content_path'] = content_path
               json_record['id'] = record_id
               json_record['content_site_name'] = content_site_name
               json_record['src_path'] = src_path
               json_record['src_path_for_results'] = src_path_for_results
               json_record['text_chunk'] = text_chunk
               json_record['search_type'] = 'text'
               json_record['title'] = title
               ##Add this dict record in the list
               display_json.append(json_record)
         
            j = j + 1 
         
         display_html = display_html + '</div>'

      #Return based on result_format
      if output_format == 'json':
         return { 'results': display_json} #Return as dict
      else:
         return display_html
           

mySearchHandler = []

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
    mySearchHandler[0].setup(llm_service_module, vectordb_module, llm_service_config, vectordb_config, content_site_name,src_path,src_path_for_results)



st.session_state.canSearch=True
# get the value of the PATH environment variable
try:
    aiwhispr_home = os.environ['AIWHISPR_HOME']
except:
    print("Could not read environment variable AIWHISPR_HOME, exiting....")
    st.session_state.canSearch=False
else:
    image = Image.open(os.path.join(aiwhispr_home, 'python','streamlit', 'static', 'aiwhispr_logo_results.png'))
    st.image(image)
    st.header('AIWhispr - Semantic Search')
    st.write('### For Content Site ' + st.session_state.sitename + ' ###')

    if 'indexing_started_flag' not in st.session_state:
        st.write('Indexing was not started in this session. You can specify a config file created earlier')    
        st.session_state.canSearch=True
        if 'config_filepath' not in st.session_state:
           configfile=""
        else:
           configfile=st.session_state.config_filepath

    if st.session_state.canSearch == True:
        configfile=st.text_input("Enter the configfile path", value=configfile)
        
        if (len(configfile) == 0 ) or  ( os.path.isfile(configfile) == False ):
            st.write("ERROR: Please check if configuration file was created.")
            st.session_state.canSearch=False
            st.text_input("Enter search query", max_chars=2056, disabled=True)
        else:
            if  st.text_input("Enter search query", max_chars=2056, key="input_query_in"):
                input_query = st.session_state.input_query_in
                mySearchHandler.append(searchHandler())
                setup(configfile)
                st.write('### Semantic Search Results ###')
                html_result = mySearchHandler[0].search(input_query=input_query, result_format='html', textsearch_flag='N')
                st.markdown(html_result,unsafe_allow_html=True)



