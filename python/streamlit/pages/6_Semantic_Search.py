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

class searchHandlerStreamlit:
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

   def search(self,input_query:str, result_format:str, textsearch_flag:str, configfile:str): 

      output_format = result_format      
      self.logger.debug("result format: %s", result_format)
      if output_format not in ['html','json']:
         self.logger.error("cannot handle this result format type")
      if textsearch_flag not in ['Y', 'N']:
         self.logger.error("text search flag should be a Y or N")

      self.logger.debug("get vector embedding for text:{%s}",input_query)
      query_embedding_vector =  self.model.encode(input_query)
      self.doc_ids.append(input_query)
      self.doc_vectors.append(query_embedding_vector)

      query_embedding_vector_as_list = query_embedding_vector
      vector_as_string = ' '. join(str(e) for e in query_embedding_vector_as_list)
      self.logger.debug("vector embedding:{%s}",vector_as_string)

      if textsearch_flag == 'Y':
         search_results = self.vector_db.search(self.content_site_name,query_embedding_vector_as_list, self.limit_hits ,input_query)
      else:
         search_results = self.vector_db.search(self.content_site_name,query_embedding_vector_as_list, self.limit_hits)
      
      display_html = '<div class="aiwhisprSemanticSearchResults">'
      display_json = []

      self.logger.debug('SearchService received search results from vectordb:')

      no_of_semantic_hits = search_results['results'][0]['found']
     

      i = 0
      st.session_state.search_results = {} #Empty dictionary
      st.session_state.search_results['results'] = [] #Array of records
      while i < no_of_semantic_hits:
         result_record = {}
         chunk_map_record = search_results['results'][0]['hits'][i]
         content_site_name = chunk_map_record['content_site_name']
         record_id = chunk_map_record['id']
         content_path = chunk_map_record['content_path']
         src_path = chunk_map_record['src_path']
         #src_path_for_results = chunk_map_record['src_path_for_results']
         src_path_for_results = self.src_path_for_results
         text_chunk = chunk_map_record['text_chunk']
         title = chunk_map_record['title']
         vector_embedding = chunk_map_record['vector_embedding']
         
         #Capture the value for the graphs (semantic search plot, 3D UMAP plot)
         #Semantic Distance for semantic search plot
         if (self.vector_db.module_name == 'qdrantVectorDb') or (self.vector_db.module_name == 'milvusVectorDb'):
            semantic_distance_score = (1 - chunk_map_record['match_score']) #Convert score to cosine distance(near)
         else:
            semantic_distance_score = chunk_map_record['match_score'] #Cosine Distance
         semantic_distance_score_str = str(semantic_distance_score)
         angle_radians = math.acos(semantic_distance_score)
         self.vector_angle_radians.append(angle_radians)
         
         #Store these reults in the session state
         result_record['content_site_name'] = content_site_name
         result_record['id'] = record_id
         result_record['content_path'] = content_path
         result_record['src_path'] = src_path
         result_record['src_path_for_results'] = src_path_for_results
         result_record['title'] = title
         result_record['text_chunk'] = text_chunk
         st.session_state.search_results['results'].append(result_record)
         
         #Vector ID for 3D UMAP Plot
         self.doc_ids.append(record_id)
         #VectorEmbedding for 3D UMAP Plot
         self.doc_vectors.append(vector_embedding)

         if output_format == 'html':
            
            if src_path_for_results[0:17] == 'aiwhisprStreamlit':
               display_url =   'Show_Complete_Text?configfile=' + urllib.parse.quote(configfile)  + '&contentpath=' + urllib.parse.quote(content_path)
            elif src_path_for_results[0:4] == 'http':
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
            
            display_html = display_html + '<p> Cosine semantic distance : ' + semantic_distance_score_str +  '</pr>'
            display_html = display_html + '<p> Document Id: ' + record_id + '</pr><br>'
            display_html = display_html + '<div><p>' + display_text_chunk + '</p></div><br>'
            
            
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
               
               if src_path_for_results[0:17] == 'aiwhisprStreamlit':
                  display_url =   'Show_Complete_Text?configfile=' + urllib.parse.quote(configfile)  + '&contentpath=' + urllib.parse.quote(content_path)
               elif src_path_for_results[0:4] == 'http':
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
    if 'sitename' in st.session_state:
        st.write('### For Content Site ' + st.session_state.sitename + ' ###')
    else:
        st.write('######')
        
    if 'indexing_started_flag' not in st.session_state:
        st.write('Indexing was not started in this session. You can specify a config file created earlier')    
        st.session_state.canSearch=True
        if 'config_filepath' not in st.session_state:
           configfile=""
        else:
           configfile=st.session_state.config_filepath
    else:
        configfile=st.session_state.config_filepath

    if st.session_state.canSearch == True:
        configfile=st.text_input("Enter the configfile path", value=configfile)
        
        if (len(configfile) == 0 ) or  ( os.path.isfile(configfile) == False ):
            st.write("ERROR: Please check if configuration file was created.")
            st.session_state.canSearch=False
            st.text_input("Enter search query", max_chars=2056, disabled=True)
        else:
            if st.text_input("Enter search query", max_chars=2056, key="input_query_in"):
               input_query = st.session_state.input_query_in
               mySearchHandler.append(searchHandlerStreamlit())
               setup(configfile)
               st.write('#### Semantic Plot  ####')
               st.write("The green line represents the input query, {blue,orange,red} lines represent search results - the semantic distance is the cosine distance")
               html_result = mySearchHandler[0].search(input_query=input_query, result_format='html', textsearch_flag='N',configfile=configfile)
               no_of_results = len(mySearchHandler[0].vector_angle_radians)
               
               if no_of_results > 0: #If we have results
                  ###Plot Semantic Search using Matplotlib
                  #r = 1.0
                  #plt.plot(0,r, color = 'blue', marker = 'o')
                  #plt.plot([0,r * cos(deg2rad(90))], [0,r * sin( deg2rad(90))], color = 'green')
                  #if len(input_query) < 40:
                  #  inquery=input_query
                  #else:
                  #  inquery=input_query[0:37] + '...'
                  #plt.text(0.1,0.95,inquery)
                  #for angle_radians in mySearchHandler[0].vector_angle_radians:
                  #     plt.plot([0, r * cos(angle_radians)], [0, r * sin(angle_radians)], color = "black")
               
                  #st.pyplot(plt)
                  #plt.clf()

                  #Plot Semantic Search Cosine using Plotly
                  if len(input_query) < 40:
                     inquery=input_query
                  else:
                     inquery=input_query[0:37] + '...'

                  semantic_distance_points_x = []
                  semantic_distance_points_y = []
                  
                  r= 1.0
                  semantic_distance_fig = go.Figure()
                  semantic_distance_fig.update_xaxes(range=[0, r])
                  semantic_distance_fig.update_yaxes(range=[0, 1])
                  semantic_distance_fig.add_shape(type="line",
                     x0=0, y0=0, x1=0, y1=1,
                     line_color="Green",line_width=5,
                  )
                  semantic_distance_points_x.append(0)
                  semantic_distance_points_y.append(1)
                  
      
                  point_counter = 1
                  for angle_radians in mySearchHandler[0].vector_angle_radians:
                        if point_counter <= 5:
                           linecolor="Blue"
                           linewidth=3
                        elif point_counter >5 and point_counter <= 10:
                           linecolor="Orange"
                           linewidth=2
                        else:
                           linecolor="Red"
                           linewidth=1

                        semantic_distance_fig.add_shape(type="line",x0=0, y0=0, 
                                       x1=(r*cos(angle_radians)), y1=(r * sin(angle_radians)), 
                                       line=dict(color=linecolor,width=linewidth)
                                       )
                        semantic_distance_points_x.append(r * cos(angle_radians))
                        semantic_distance_points_y.append(r * sin(angle_radians))
                        point_counter=point_counter+1
                  
                  
                  semantic_distance_fig.add_trace(go.Scatter(x=semantic_distance_points_x, 
                                                             y=semantic_distance_points_y,
                                                             mode="markers",
                                                             marker_color="Black",
                                                             text=mySearchHandler[0].doc_ids, 
                                                             hovertemplate = 
                                                             '<i>Cos(sd)=</i>: %{x}' +
                                                             '<br><i>Sin(sd)=</i>: %{y}' +
                                                             '<br><i>docId=</i>: %{text}'
                                                             )
                  )
                  semantic_distance_fig.update_shapes(dict(xref='x', yref='y'))      
                  semantic_distance_fig.update_layout(hovermode='x unified')
                  st.plotly_chart(semantic_distance_fig)   
                  
                  ##Vectors which will be input for PCA
                  embedding_array = np.array(mySearchHandler[0].doc_vectors)
                  ##Colors for the PCA points
                  color_array = []
                  color_array.append("green")   #The first point is the input query
                  point_counter = 1 #Starting from first result
                  while point_counter <= no_of_results:
                     if point_counter <= 5:
                          color_array.append("blue")
                     elif point_counter > 5 and point_counter <=10:
                          color_array.append("orange")
                     else:
                          color_array.append("red")
                     point_counter = point_counter + 1
                  
                  #data_series = pd.DataFrame(embedding_array, index=mySearchHandler[0].doc_ids)
                  ##PCA 
                  pca = PCA()
                  pipe = Pipeline([('scaler', StandardScaler()), ('pca', pca)])
                  Xt = pca.fit_transform(embedding_array)

                  st.write("#### PCA MAP FOR DOCUMENTS ####")
         
                  ##PCA using Matplotlib
                  #fig = plt.figure()
                  #ax = fig.add_subplot(projection='3d')
                  #ax.scatter(Xt[:,0], Xt[:,1], Xt[:,2],c=color_array)
                  #st.pyplot(plt)

                  #PCA using Plotly
                  pca_data = go.Scatter3d(x=Xt[:,0], y=Xt[:,1], z=Xt[:,2],hovertext=mySearchHandler[0].doc_ids, mode='markers', marker_color=color_array)
                  pca_data_fig = go.Figure(pca_data)
                  st.plotly_chart(pca_data_fig)


                  #Print results from nearest to furthest by semantic distance (top 25)
                  st.write('#### Search Results  ####')
                  st.markdown(html_result,unsafe_allow_html=True)
                  try:
                     if (len(st.session_state.search_results['results']) == 0  ):
                        st.write("No search results yet exist")
                  except Exception as err:
                     st.write(err)
                 






