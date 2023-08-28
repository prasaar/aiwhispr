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
sys.path.append("../document-processor")

import aiwhisprTextDocProcessor

from aiwhisprLocalIndex import aiwhisprLocalIndex
from aiwhisprBaseClasses import siteAuth,vectorDb,srcContentSite, baseLlmService
from textDownloader import textDownloader

import initializeContentSite
import initializeVectorDb
import initializeLlmService
import initializeDocumentProcessor

import aiwhisprConstants 
import logging

import multiprocessing as mp
import pickle

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

##This function is used by both single process and multiprocess
def index_from_list(pickle_file_path,process_list = 0):
    logger = logging.getLogger(__name__)
    mypid = os.getpid()
    
    try:
        f = open(pickle_file_path, 'rb')   # 'rb' for reading binary file
        self_description = pickle.load(f)     
        f.close()
    except:
        logger.error("PID:{%d} could not read the pickle file at %s", mypid, pickle_file_path )
        sys.exit()

    file_with_content_path_list = self_description['download_these_files_list'][process_list]
    logger.debug("PID:{%d} Indexing Filepath Content Site in parallel by indexing files in the list in %s",mypid, file_with_content_path_list)          
        
    site_auth = siteAuth(auth_type=self_description['site_auth']['auth_type'],
                                 check_file_permission=self_description['site_auth']['check_file_permission'] )

    #Instantiate the vector db object. This will return a vectorDb derived class based on the module name
    vector_db = initializeVectorDb.initialize(vectordb_module=self_description['vector_db']['module_name'],
                                             vectordb_hostname = self_description['vector_db']['vectordb_hostname'], 
                                             vectordb_portnumber = self_description['vector_db']['vectordb_portnumber'], 
                                             vectordb_key = self_description['vector_db']['vectordb_key'],
                                             content_site_name = self_description['content_site']['content_site_name'],
                                             src_path = self_description['content_site']['src_type'], 
                                             src_path_for_results = self_description['content_site']['src_path_for_results'] 
                                             )
    
    llm_service = initializeLlmService.initialize(llm_service_module = self_description['llm_service']['module_name'], 
                                                  model_family = self_description['llm_service']['model_family'], 
                                                  model_name = self_description['llm_service']['model_name'],
                                                  llm_service_api_key = self_description['llm_service']['llm_service_api_key'])
                            
    contentSite = initializeContentSite.initialize(content_site_module='stackexchangeContentSite',
                                                   src_type=self_description['content_site']['src_type'],
                                                   content_site_name=self_description['content_site']['content_site_name'],
                                                   src_path=self_description['content_site']['src_path'],
                                                   src_path_for_results=self_description['content_site']['src_path_for_results'],
                                                   working_directory=self_description['local']['working_directory'],
                                                   index_log_directory=self_description['local']['index_log_directory'],
                                                   site_auth=site_auth,
                                                   vector_db = vector_db,
                                                   llm_service = llm_service,
                                                   do_not_read_dir_list =  self_description['content_site']['do_not_read_dir_list'] ,
                                                   do_not_read_file_list = self_description['content_site']['do_not_read_file_list'] )
    
    contentSite.connect()
    # Read list of paths to posts pickled in the path_to_download_file_list, 
    #      for each pickled post, load it and then process it
    #              For each post_body_for_llm, get the vector embedding
    #              Insert the post_body_for_llm, associated meta data and vector embedding into the vector database

    #Now start reading list of all the posts
    file_download_list = open(file_with_content_path_list, 'r')
    continue_reading_file_list = True
    content_path = ''
    while continue_reading_file_list:  # Get next line from file
        row = file_download_list.readline()
        if not row:
            continue_reading_file_list = False
        else:
            # if line is empty then end of file is reached
            row = row.rstrip()
            f = open(row, 'rb')
            qa_post = pickle.load(f)
            f.close()
            content_path = qa_post['content_path']
            download_file_path = contentSite.getDownloadPath(content_path = content_path, pid_suffix = str(mypid))
            logger.debug('Downloaded File Name: ' + download_file_path)
            contentSite.downloader.write_content(text_content = qa_post['post_body_for_llm'], download_file_path = download_file_path)
                            
            if (contentSite.docProcessor != None ):  #Using the aiwhisprTextDocProcessor set in the contentSite
                contentSite.docProcessor.setDownloadFilePath(download_file_path)
                #Extract text
                contentSite.docProcessor.extractText()
                #Create text chunks
                chunk_dict = contentSite.docProcessor.createChunks()
                logger.debug("%d chunks created for %s", len(chunk_dict), download_file_path)
                #For each chunk, read text, create vector embedding and insert in vectordb
                ##the chunk_dict dictionary will have key=/filepath_to_the_file_containing_text_chunk, value=integer value of the chunk number.
                for chunk_file_path in chunk_dict.keys():
                    text_chunk_no = chunk_dict[chunk_file_path]
                    logger.debug("chunk_file_path:{%s} text_chunk_no:{%d}", chunk_file_path, text_chunk_no)
                    #Now encode the text chunk. chunk_file_path is the file path to the text chunk
                    text_f = open(chunk_file_path)
                    text_chunk_read = text_f.read()
                    vec_emb = contentSite.llm_service.encode(text_chunk_read)
                    logger.debug("Vector encoding dimension is {%d}", len(vec_emb))
                    text_f.close()

                    id = contentSite.generate_uuid()
                    #Insert the meta data, text chunk, vector emebdding for text chunk in vectordb
                    logger.debug("Inserting the record in vector database for id{%s}", id)
                    contentSite.vector_db.insert(id = id,
                                        content_path =  content_path, 
                                        last_edit_date = qa_post['last_edit_date'] , 
                                        tags = qa_post['tags'] , 
                                        title = qa_post['title'] , 
                                        text_chunk = text_chunk_read, 
                                        text_chunk_no = text_chunk_no, 
                                        vector_embedding = vec_emb)
            else:
                self.logger.error('We did not get a valid document processor')

    logger.info("PID:{%d} finished indexing the files is the list from %s ", mypid, file_with_content_path_list )


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
       
       #Request the vector db to connect to the server
       self.vector_db.connect()
       #Connect the LLM Service for encoding text -> vector
       self.llm_service.connect()
       
    def index(self, no_of_processes = 1):
        self.logger.debug("Custom Sie Handler : Stack Exchange Archive Posts.xml with %d processes", no_of_processes)
        self.no_of_processes = no_of_processes

        #connect to the vector database
        try:
            self.vector_db.connect() # Connect to vectorDb
        except:
            self.logger.error("Could not connect to vector database ... Exiting")
            sys.exit()
    
        if mp.cpu_count() < self.no_of_processes:
            self.logger.critical("Number of CPU %d, is less than number of parallel index process %d requested, Will reset no_of processes to 1 to be safe", mp.cpu_count(), self.no_of_processes)
            self.no_of_processes = 1
        
        no_of_content_path_list_files = self.no_of_processes

        #Path to a files with pickled content, 1 file for each process
        fctr = 0
        while fctr < no_of_content_path_list_files:
            fpath = os.path.join(self.index_log_directory,  self.content_site_name + '.contentpath.list.' + str(fctr))
            self.download_these_files_list.append(fpath)
            fctr = fctr + 1
        
        #Open these files
        file_writers = []
        fctr = 0
        while fctr < no_of_content_path_list_files:
            f = open(self.download_these_files_list[fctr], "w")
            file_writers.append(f)
            fctr = fctr + 1
        
        #Indexing is a multi-step operation
        # 1\ Cleanup : Purge the local index, vector db , move the old work dub-directorry to a backup
        # 2\ Read content site, for each file  get the file suffix and decide if we extract text for vector embeddings
        #      If we decide to process the file then download it, extract text and break the text into chunks
        #      For each text chunk get the vector embedding
        #      Insert the text chunk, associated meta data and vector embedding into the vector database

        #1\ Cleanup : Purge old records in local index, vectorDb for this site

        self.vector_db.deleteAll()
        self.backupDownloadDirectories()
        self.createDownloadDirectory() #Create before the multiple processeses start downloading.

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
        no_of_parent_posts = 0
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
                no_of_parent_posts = no_of_parent_posts + 1
                
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

        #Finished parsing  Posts.xml
        size_of_posts_dict = sys.getsizeof(parent_posts)
        self.logger.info("Total Parent Posts: %d , Memory Size: %d", no_of_parent_posts, size_of_posts_dict)
        
        #parent_posts now contains the QA under each parent_post_id (Key)
        fctr = 0
        site_working_directory_subdir = os.path.join( self.working_directory , self.content_site_name)    
        for parent_post_id in parent_posts.keys():
            qa_post = parent_posts[parent_post_id]
            #Pickle this post and write it under the working directory
            #Write the path to this pickled post in the content_path list
            post_pickle_file_path = os.path.join(site_working_directory_subdir, parent_post_id + '.post.pkl')
            fpickle = open(post_pickle_file_path,"wb") #'wb' instead 'w' for binary file
            pickle.dump(qa_post, fpickle, -1) #-1 specifies highest binary protocol
            fpickle.close()
            file_writers[fctr].write(post_pickle_file_path + '\n')  #Record path to this pickle file in contentpath.list.*
            fctr = fctr + 1
            if fctr == no_of_content_path_list_files:
                fctr = 0

        fctr = 0
        while fctr < no_of_content_path_list_files:
            file_writers[fctr].close()
            fctr = fctr +1

        pickle_file_path = self.pickle_me()  #Pickle the main parts of myself(ContentSite)

        self.logger.debug("Attempting to starting %d processes for indexing", self.no_of_processes)
        #Spawn  indexing processes
        mp.set_start_method('spawn')
        i = 0
        jobs = []
        while i < self.no_of_processes:
            self.logger.info("Spawning indexing job {%d}", i)
            job = mp.Process(target=index_from_list, args=(pickle_file_path, i,))
            job.start()
            jobs.append(job)
            i = i + 1 
