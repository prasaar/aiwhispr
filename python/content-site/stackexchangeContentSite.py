import os
import sys
import io
import uuid
import sqlite3
import boto3
from datetime import datetime, timedelta
import time
import pathlib
import datetime
import re
import xml.etree.ElementTree as ET

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../common-objects")
sys.path.append("../common-functions")
sys.path.append("../base-classes")

import initializeDocumentProcessor
import aiwhisprTextDocProcessor

from aiwhisprLocalIndex import aiwhisprLocalIndex
from aiwhisprBaseClasses import siteAuth,vectorDb,srcContentSite, baseLlmService
from textDownloader import textDownloader


import aiwhisprConstants 

import logging

import extract_int_attribute_xml_element
import extract_str_attribute_xml_element
import extract_ts_attribute_xml_element
import extract_cleantext_from_html
import extract_codeblocks_from_html
import replace_codeblocks_from_html

# as per recommendation, compile once only
CLEANR = re.compile('p&gt;|/p&gt;|&#xA;|<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext
# as per recommendation, compile only once


class createContentSite(srcContentSite):
            
    downloader:textDownloader

    def __init__(self,content_site_name:str,src_path:str,src_path_for_results:str,working_directory:str,index_log_directory:str,site_auth:siteAuth,vector_db:vectorDb, llm_service:baseLlmService, do_not_read_dir_list:list = [], do_not_read_file_list:list = []):
       
       srcContentSite.__init__(self,content_site_name=content_site_name,src_type="s3",src_path=src_path,src_path_for_results=src_path_for_results,working_directory=working_directory,index_log_directory=index_log_directory,site_auth=site_auth,vector_db=vector_db,llm_service=llm_service,do_not_read_dir_list=do_not_read_dir_list, do_not_read_file_list=do_not_read_file_list)
       self.downloader = textDownloader()
       self.logger = logging.getLogger(__name__)
       #Since all content is text, we will initiate the text document processor at start. 
       # This will save time by avoiding multiple module import
       self.docProcessor =  aiwhisprTextDocProcessor.getDocProcessor()
     
    def connect(self):
       
       #Check if the top level directory exists
       if os.path.isdir(self.src_path) == False:
           self.logger.error("Src Type: %s Source Path: %s does not exist", self.src_type, self.src_path)
       #get handle to the local index map object
       self.local_index = aiwhisprLocalIndex(self.index_log_directory, self.content_site_name)
       #Request the vector db to connect to the server
       self.vector_db.connect()
       #Connect the LLM Service for encoding text -> vector
       self.llm_service.connect()
       
    def index(self):

         #Indexing is a multi-step operation
        # 1\ Cleanup : Purge the local index, vector db , move the old work dub-directorry to a backup
        # 2\ Read content site, for each file  get the file suffix and decide if we extract text for vector embeddings
        #      If we decide to process the file then download it, extract text and break the text into chunks
        #      For each text chunk get the vector embedding
        #      Insert the text chunk, associated meta data and vector embedding into the vector database

        #1\ Cleanup : Purge old records in local index, vectorDb for this site
        self.local_index.deleteAll()
        self.vector_db.deleteAll()
        self.backupDownloadDirectories()

    
        ###2\ Now start reading the site and list all the files
        self.logger.info('Reading From Top Level Directory:' + self.src_path)
        self.logger.info("Purging the current local ContentIndex Map")
        
        ###This dictionary will contain all the processed posts.
        ###The key is the Question Post ID
        parent_posts = {} #Dictionary of parent posts

    
        #### PARSE THE XML FILE ####
        xmlfilename = self.src_path
        try:
            tree = ET.parse(xmlfilename)
            root = tree.getroot()
            self.logger.debug("Reading the XML File:%s", xmlfilename)
        except:
            self.logger.error("Could not read XML File:%s, hence exiting", xmlfilename)
            sys.exit()

        #iterate over the subelements and populate parent_posts
        for child in root:
            #First process int
            post_id = int(child.attrib['Id'])
            accepted_answer_id = extract_int_attribute_xml_element.get(child,'AcceptedAnswerId') 
            answer_count  = extract_int_attribute_xml_element.get(child,'AnswerCount') 
            parent_post_id  = extract_int_attribute_xml_element.get(child,'ParentId')
            post_type_id  = extract_int_attribute_xml_element.get(child,'PostTypeId')
            score  = extract_int_attribute_xml_element.get(child,'Score')
            view_count  = extract_int_attribute_xml_element.get(child,'ViewCount')
            favorite_count  = extract_int_attribute_xml_element.get(child,'FavoriteCount')
            #Next timestamp fields
            closed_date = extract_ts_attribute_xml_element.get(child,'ClosedDate')
            community_owned_date = extract_ts_attribute_xml_element.get(child,'CommunityOwnedDate')
            last_edit_date = extract_ts_attribute_xml_element.get(child,'LastEditDate')
            creation_date = extract_ts_attribute_xml_element.get(child,'CreationDate')
            last_activity_date = extract_ts_attribute_xml_element.get(child,'LastActivityDate')
            #Next 
            owner_user_id = extract_str_attribute_xml_element.get(child,'OwnerUserId')
            owner_user_name = extract_str_attribute_xml_element.get(child,'OwnerDisplayName')
            last_editor_user_id = extract_str_attribute_xml_element.get(child,'LastEditorUserId')
            last_editor_user_name = extract_str_attribute_xml_element.get(child,'LastEditorDisplayName')
            content_license = extract_str_attribute_xml_element.get(child,'ContentLicense')
            tags = extract_str_attribute_xml_element.get(child,'Tags')
            title = extract_str_attribute_xml_element.get(child,'Title')
            post_body = extract_cleantext_from_html.get(child.attrib['Body'])
            #Extract any code blocks from the body
            post_code_blocks =  extract_codeblocks_from_html.get(child.attrib['Body'])
            #After finding code blocks , replace the code blocks with headers and then extract post body
            post_body = extract_cleantext_from_html.get(child.attrib['Body'])
            post_body_for_llm = extract_cleantext_from_html.get(replace_codeblocks_from_html.replace(child.attrib['Body'], len(post_code_blocks)))
            #Store Raw HTML Post
            post_raw = child.attrib['Body']


            if post_type_id == 1: #this is a parent
                self.logger.debug("Parent Post ID:%d", post_id)
                
                post = {}
                post['post_id'] = post_id
                post['content_path'] = str(post_id)
                post['tags'] = tags
                post['title'] = title
                post['post_body_for_llm'] = '[QUESTION]' + post_body_for_llm
                if last_edit_date != None:
                    post['last_edit_date'] = last_edit_date
                elif creation_date != None:
                    post['last_edit_date'] = creation_date
                else:
                    post['last_edit_date'] = time.time()

                ##Add this parent post in the dict
                parent_posts[str(post_id)] = post
                
                self.logger.debug("post_id:%d",post_id)
                self.logger.debug("content_path:%s", post['content_path'])
                self.logger.debug("tags:%s", post['tags'])
                self.logger.debug("title:%s",post['title'])
                self.logger.debug("post_body_for_llm:%s",post['post_body_for_llm'])
                self.logger.debug("last_edit_date:%f", post['last_edit_date'])
            else:  #this is a answer,comment
                if post_type_id == 2: #We only look at answers
                    #Find parent post and append this answer text to the parent post 
                    try:
                        parent_posts[str(parent_post_id)]['post_body_for_llm'] = parent_posts[str(parent_post_id)]['post_body_for_llm'] + '[ANSWER]' + post_body_for_llm
                        self.logger.debug("Appending post id %d text to parent post id %d  [TEXT]: %s", post_id, parent_post_id, post_body_for_llm) 
                    except:
                        self.logger.error("Could not append post id %d text to parent post id %d  [TEXT]: %s", post_id, parent_post_id, post_body_for_llm)

        #parent_posts now contains the QA under each parent_post_id (Key)    
        for parent_post_id in parent_posts.keys():
            qa_post = parent_posts[parent_post_id]
            download_file_path = self.getDownloadPath(qa_post['content_path'])
            self.logger.debug('Downloaded File Name: ' + download_file_path)
            self.downloader.write_content(text_content = qa_post['post_body_for_llm'], download_file_path = download_file_path)
                            
            if (self.docProcessor != None ):
                self.docProcessor.setDownloadFilePath(download_file_path)
                #Extract text
                self.docProcessor.extractText()
                #Create text chunks
                chunk_dict = self.docProcessor.createChunks()
                self.logger.debug("%d chunks created for %s", len(chunk_dict), download_file_path)
                #For each chunk, read text, create vector embedding and insert in vectordb
                ##the chunk_dict dictionary will have key=/filepath_to_the_file_containing_text_chunk, value=integer value of the chunk number.
                for chunk_file_path in chunk_dict.keys():
                    text_chunk_no = chunk_dict[chunk_file_path]
                    self.logger.debug("chunk_file_path:{%s} text_chunk_no:{%d}", chunk_file_path, text_chunk_no)
                    #Now encode the text chunk. chunk_file_path is the file path to the text chunk
                    text_f = open(chunk_file_path)
                    text_chunk_read = text_f.read()
                    vec_emb = self.llm_service.encode(text_chunk_read)
                    self.logger.debug("Vector encoding dimension is {%d}", len(vec_emb))
                    text_f.close()

                    id = self.generate_uuid()
                    #Insert the meta data, text chunk, vector emebdding for text chunk in vectordb
                    self.logger.debug("Inserting the record in vector database for id{%s}", id)
                    self.vector_db.insert(id = id,
                                        content_path =  qa_post['content_path'], 
                                        last_edit_date = qa_post['last_edit_date'] , 
                                        tags = qa_post['tags'] , 
                                        title = qa_post['title'] , 
                                        text_chunk = text_chunk_read, 
                                        text_chunk_no = text_chunk_no, 
                                        vector_embedding = vec_emb)
            else:
                self.logger.error('We did not get a valid document processor')

        self.logger.debug("Completed indexing for stackexchange posts")                    
