##This file implements all the base classes in aiwhispr
##We dont use typical __ because there is no real private variable in python
import random
import string
import os
import sys
import pathlib
import logging
import time
from xmlrpc.client import Boolean

import spacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector
import logging

import shutil
import re

import uuid

import pickle


sys.path.append("../common-functions")
sys.path.append("../common-objects")
import aiwhisprConstants
from aiwhisprLocalIndex import aiwhisprLocalIndex

#BASE CLASS: baseLlmService
class baseLlmService:
    
    llm_service_config:dict
    module_name:str

    def __init__(self, llm_service_config:dict, module_name:str):
        self.llm_service_config = llm_service_config
        self.module_name = module_name
        
    #public function
    def connect(self):
        pass

    #public function
    def encode(self,in_text:str):
        pass


#BASE CLASS: siteAuth
#Support S3, Azureblob, filepath mounts
#If you want to include other types of authentication then inherit from this class and you can process the cofigurations from kwargs
class siteAuth:

    auth_type:str = ''
    site_userid:str = ''
    site_password:str = ''
    sas_token:str = ''
    az_key:str = ''
    aws_access_key_id:str = ''
    aws_secret_access_key:str = ''
    check_file_permission:str = ''
    google_cred_path:str=''
    google_project_id:str=''
    google_storage_api_key:str=''

    auth_config: dict = {}

    logger = logging.getLogger(__name__)
    
    def __init__(self,auth_type:str,**kwargs):
        self.auth_type = auth_type
        self.logger.debug("auth_type=%s",auth_type)
        match self.auth_type:
            case 'filechecks':
                self.logger.debug("filechecks:check_file_permission=%s",kwargs['check_file_permission'] )
                self.check_file_permission = kwargs['check_file_permission']
            case 'sas':
                self.logger.debug("sas:sas_token=%s",kwargs['sas_token'] )
                self.sas_token = kwargs['sas_token']
            case 'az-storage-key':
                self.logger.debug("az-storage-key:az_key=%s",kwargs['az_key'] )
                self.az_key = kwargs['az_key']
            case 'aws-key':
                self.logger.debug("aws-key:aws_access_key_id=%s,aws_secret_access_key=%s",kwargs['aws_access_key_id'], kwargs['aws_secret_access_key'] )
                self.aws_access_key_id = kwargs['aws_access_key_id']
                self.aws_secret_access_key = kwargs['aws_secret_access_key']
            case 'google-cred-key':
                self.logger.debug("google_cred_path=%s,google_project_id=%s,google_storage_api_key=%s",kwargs['google_cred_path'], kwargs['google_project_id'], kwargs['google_storage_api_key'] )
                self.google_cred_path = kwargs['google_cred_path']
                self.google_project_id = kwargs['google_project_id']
                self.google_storage_api_key = kwargs['google_storage_api_key']
            case other:
                self.logger.debug('Dont know how to handle the auth type %s', self.auth_type)
                self.auth_config = kwargs['auth_config']
                if self.auth_config != None:
                    self.logger.debug("The auth_config dictionary is %s", str(self.auth_config) )            

#BASE CLASS: vectorDb:
class vectorDb:
    
    vectordb_config:dict
    module_name:str
    content_site_name:str 
    src_path:str 
    src_path_for_results:str


    def __init__(self, vectordb_config:{}, content_site_name:str,src_path:str,src_path_for_results:str, module_name:str):
        self.vectordb_config = vectordb_config
        self.content_site_name = content_site_name
        self.src_path=src_path
        self.src_path_for_results=src_path_for_results
        self.module_name=module_name

        self.baseLogger = logging.getLogger(__name__)
        for key in vectordb_config.keys():
            self.baseLogger.debug("Key:Value Pair in VectorDB Config [%s][%s]", key, vectordb_config[key])
    

    #We are defining the signature in base class to show that we are folling a particular schema
    #A schema change has to be managed carefully across the application.
    #A customer vectorDB module can be written  and instantiated easily so lets keep schema changes to a minimu, only when necessary.
    #public function 
    def insert(self, id:str,
               text_chunk_file_path:str, 
               content_path:str, 
               last_edit_date:float, 
               tags:str, 
               title:str, 
               text_chunk:str, 
               text_chunk_no:int, 
               vector_embedding:[]
               ):
        pass

    #public function
    def connect(self):
        pass

    #public function
    def deleteAll(self):
        pass

    #public function
    def update(self):
        pass

    #public function
    def query(self):
        pass

#This is the template (base) class that implements the Content Sites
#There will be seperate classes for each source e.g. azure, s3, file etc.
#The base class is useful to design the basic operations that we will link to any Content Site

#BASE CLASS: srcContentSite
class srcContentSite:

    content_site_name:str
    src_type:str
    src_path_for_results:str
    working_directory:str
    index_log_directory:str
    site_auth:siteAuth
    vector_db:vectorDb
    llm_service:baseLlmService
    do_not_read_dir_list:[]
    do_not_read_file_list:[]
    no_of_processes:int
    download_these_files_list:[]  #a list of path to files that contain the content_paths that should be indexed
    local_index:aiwhisprLocalIndex  #local index, it will store the metadata


    baseLogger = logging.getLogger(__name__)
    #Init without siteAuth e.g. local file directory
    #def __init__(self, content_site_name:str, src_type:str, src_path:str, src_path_for_results:str, working_directory:str, index_log_directory:str, vector_db:vectorDb ):
    #    self.content_site_name = content_site_name
    #    self.src_type = src_type
    #   self.src_path = src_path
    #   self.src_path_for_results = src_path_for_results
    #   self.working_directory = working_directory
    #   self.index_log_directory = index_log_directory
    #   self.vector_db = vector_db
        
    #Common init signature
    #We have defined a common signature for bases and expect derived classes also to follow this signature.
    #the Derives classes are instantiated dynamically so it's important we have a common signature.
    def __init__(self, content_site_name:str, src_type:str, src_path:str, src_path_for_results:str, working_directory:str, index_log_directory:str, site_auth:siteAuth, vector_db:vectorDb, llm_service:baseLlmService, do_not_read_dir_list:list = [], do_not_read_file_list:list = []):
        self.content_site_name = content_site_name
        self.src_type = src_type
        self.src_path = src_path
        self.src_path_for_results = src_path_for_results
        self.working_directory = working_directory
        self.index_log_directory = index_log_directory
        self.site_auth = site_auth
        self.vector_db = vector_db
        self.llm_service = llm_service
        self.do_not_read_dir_list = do_not_read_dir_list
        self.do_not_read_file_list = do_not_read_file_list
        #Create an empty list
        self.download_these_files_list = []

        
        
    #These operations shold be implemented is the sub(child) classes
    #public function
    def connect(self):
        pass

    #public function
    def index(self, no_of_processes = 1):
        pass

    #public function
    def deleteAll(self):
        pass

    #public function
    def display(self):
        pass

    #public function
    def generate_uuid(self):
        return str(uuid.uuid1())
    
    #private function
    def get_random_string(self,length:int):
        # choose from all lowercase letter
        letters = string.ascii_letters
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str
    
    #This funtions checks if the content path should be read based on rules configured in config file
    #public function
    def checkIfContentShouldBeRead(self,content_path:str)->Boolean:
        contentCanBeReadFlag = True
        #Check if the do_not_read list has some rules, if yes then check
        if ( len(self.do_not_read_file_list) > 0 or len(self.do_not_read_dir_list) > 0 ):  ##If any rule is defined then check else return True
            self.baseLogger.debug("Do Not Read list exits")
            dirpath,filename = os.path.split(content_path)
    
            if (len(dirpath)> 0 and (dirpath in self.do_not_read_dir_list) ):  ##Check in directory lists
                self.baseLogger.info("Found directory %s in the do_not_read_dir_list", dirpath)
                contentCanBeReadFlag = False
            else:   ##Else check in file list
                if (len(filename) > 0):
                    ##The do_not_read_file_list can be patterns.
                    for pattern_str in self.do_not_read_file_list:
                        pattern = re.compile(pattern_str)
                        match_results= re.search(pattern, filename)
                        if (match_results != None):
                            self.baseLogger.info("Found filename %s matching a pattern in the do_not_read_file_list", filename)
                            contentCanBeReadFlag = False
                            break

        return contentCanBeReadFlag
                        
        
    #This funtion creates the download path. When called with a pid_suffix(by index_in_parallel) it adds the pid_suffix to the temp directory name 
    #private function
    def getDownloadPath(self,content_path:str, pid_suffix = '') -> str:  
        filename = pathlib.PurePath(content_path).name

        site_working_directory_subdir = os.path.join( self.working_directory , self.content_site_name)
        isDirExist = os.path.exists(site_working_directory_subdir)
        if not isDirExist:
               os.makedirs(site_working_directory_subdir)
               self.baseLogger.debug('Created working directory ' + site_working_directory_subdir)

        directory_path = os.path.join(site_working_directory_subdir , self.get_random_string(8) )
        if len(pid_suffix) > 0:
            directory_path = directory_path + '_' + pid_suffix

        isDirExist = os.path.exists(directory_path) 
        if not isDirExist:
            os.makedirs(directory_path)
            self.baseLogger.debug("Created a temporary directory path for downloaded file name: " + directory_path)

        download_file_path = os.path.join(directory_path , filename)

        self.baseLogger.debug('Download File Path: ' + download_file_path)
        return download_file_path
    
    def backupDownloadDirectories(self):
        #This function is called when a full index is done on the content-site
        #It will move the content-site-name dir to another name
        site_working_directory_subdir = os.path.join( self.working_directory , self.content_site_name)
        isDirExist = os.path.exists(site_working_directory_subdir)
        if isDirExist:
            site_working_directory_subdir_bkup = site_working_directory_subdir + '_' + self.get_random_string(6) + '_bkup'
            self.baseLogger.info("Backup existing directory to %s", site_working_directory_subdir_bkup)
            try:
                shutil.move(site_working_directory_subdir, site_working_directory_subdir_bkup )
            except:
                self.baseLogger.error("Could not move %s to %s", site_working_directory_subdir, site_working_directory_subdir_bkup )

    def createDownloadDirectory(self):
        #Create the download directory before the multiprocess starts
        site_working_directory_subdir = os.path.join( self.working_directory , self.content_site_name)
        isDirExist = os.path.exists(site_working_directory_subdir)
        if not isDirExist:
               os.makedirs(site_working_directory_subdir)
               self.baseLogger.debug('Created working directory ' + site_working_directory_subdir)


    def create_download_these_files_list(self):
        contentrows = self.local_index.getContentProcessedStatus("N") 
        no_of_rows = len(contentrows)
        self.baseLogger.debug("Total Number of rows in ContentIndex with ProcessedStatus = N: %d" , no_of_rows )
        if self.no_of_processes == None:
            self.baseLogger.error("The number of processes is not set, so setting it to 1")
            self.no_of_processes = 1
        
        no_of_files = self.no_of_processes
        i = 0
        while i < no_of_files:
            fpath = os.path.join(self.index_log_directory,  self.content_site_name + '.contentpath.list.' + str(i))
            self.download_these_files_list.append(fpath)
            i = i + 1
        
        #Open these files
        file_writers = []
        i = 0
        while i < no_of_files:
            f = open(self.download_these_files_list[i], "wb")
            file_writers.append(f)
            i = i + 1
        
        #Fetch each row[content_path] and put it in a file
        j = 0
        for row in contentrows:
            """
            SELECT 
                content_site_name,
                src_path,
                src_path_for_results,
                content_path,
                content_type,
                content_creation_date,
                content_last_modified_date,
                content_uniq_id_src,
                content_tags_from_src,
                content_size,
                content_file_suffix, 
                content_index_flag,
                content_processed_status 
            """
            file_writers[j].write(row[0].encode("utf-8") + '|'.encode("utf-8") )
            file_writers[j].write(row[1].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[2].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[3].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[4].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(str(row[5]).encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(str(row[6]).encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[7].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[8].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(str( row[9]).encode("utf-8")   + '|'.encode("utf-8") )
            file_writers[j].write(row[10].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[11].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write(row[12].encode("utf-8")  + '|'.encode("utf-8") )
            file_writers[j].write('\n'.encode("utf-8") )

            j = j + 1
            if j == no_of_files:
                j = 0
        
        #Now close the files
        for file_writer in file_writers:
            file_writer.close()
        
    def pickle_me(self):
        #This will contain the description of the setup
        self.self_description = {}
        self.self_description['content_site'] = {}
        self.self_description['content_site']['content_site_name'] = self.content_site_name
        self.self_description['content_site']['src_type'] = self.src_type
        self.self_description['content_site']['src_path'] = self.src_path
        self.self_description['content_site']['src_path_for_results'] = self.src_path_for_results
        self.self_description['content_site']['do_not_read_dir_list'] = self.do_not_read_dir_list
        self.self_description['content_site']['do_not_read_file_list'] = self.do_not_read_file_list
        
        self.self_description['local'] = {}
        self.self_description['local']['working_directory'] = self.working_directory
        self.self_description['local']['index_log_directory'] = self.index_log_directory 
        self.self_description['local']['no_of_processes'] = self.no_of_processes

        self.self_description['site_auth'] = {}
        self.self_description['site_auth']['auth_type'] = self.site_auth.auth_type
        self.self_description['site_auth']['site_userid'] = self.site_auth.site_userid
        self.self_description['site_auth']['site_password'] = self.site_auth.site_password
        self.self_description['site_auth']['sas_token'] = self.site_auth.sas_token
        self.self_description['site_auth']['az_key'] = self.site_auth.az_key
        self.self_description['site_auth']['aws_access_key_id'] = self.site_auth.aws_access_key_id
        self.self_description['site_auth']['aws_secret_access_key'] = self.site_auth.aws_secret_access_key
        self.self_description['site_auth']['check_file_permission'] = self.site_auth.check_file_permission
        self.self_description['site_auth']['google_cred_path'] = self.site_auth.google_cred_path
        self.self_description['site_auth']['google_project_id'] = self.site_auth.google_project_id
        self.self_description['site_auth']['google_storage_api_key'] = self.site_auth.google_storage_api_key    
        self.self_description['site_auth']['auth_config'] = self.site_auth.auth_config
    
        self.self_description['vector_db'] = {}
        self.self_description['vector_db']['vectordb_config'] = self.vector_db.vectordb_config 
        self.self_description['vector_db']['module_name'] =  self.vector_db.module_name 
        
        self.self_description['llm_service'] = {}
        self.self_description['llm_service']['llm_service_config'] = self.llm_service.llm_service_config 
        self.self_description['llm_service']['module_name'] = self.llm_service.module_name
        
        self.self_description['download_these_files_list'] = self.download_these_files_list

        #Pickle the self description and store it in a file in index_log_directory
        self.pickle_file_path = os.path.join(self.self_description['local']['index_log_directory'], self.content_site_name + '.pkl')
        self.baseLogger.debug("Pickle File Path:%s", self.pickle_file_path) 
        self.baseLogger.debug("Pickling :%s in binary", str(self.self_description) ) 
        fpickle = open(self.pickle_file_path,'wb') #'wb' instead 'w' for binary file
        pickle.dump(self.self_description, fpickle, -1) #-1 specifies highest binary protocol
        fpickle.close()
        return  self.pickle_file_path

        #End of self description. This will allow configs to be passed for multiprocessing
        

#BASE CLASS: srcDocProcessor for Document Processors which extract text, then chunk the text
class srcDocProcessor:
    downloaded_file_path:str
    downloaded_file_size:str
    downloaded_file_dir:str
    downloaded_filename:str

    extracted_text_file_dir:str
    extracted_text_file_path:str
    extracted_text_file_size:int
    
    no_of_chunks:int
    text_chunks_dir:str
    MAXCHUNKSIZE = aiwhisprConstants.TXTCHUNKSIZE
    
    baseLogger = logging.getLogger(__name__)

    # private function
    def get_lang_detector(self,nlp, name):
        return LanguageDetector(seed=42) 

    # Sentence level language detection
    #private function
    def detectLanguage(self,text_chunk:str)->str:
        doc = self.nlp_model(text_chunk)
        out_text_chunk = ''
        ctr = 0
        for i, sent in enumerate(doc.sents):
            ctr = ctr + 1
            if sent._.language['language'] == 'en':
                out_text_chunk = out_text_chunk + sent.text.encode('latin1').decode('utf-8')
                self.baseLogger.debug("sentence {%s}  [validated sentence as English])", sent.text.encode('latin1').decode('utf-8'))
            else:
                self.baseLogger.warning('Found sentence number %d in text chunk which is not English. Removing this sentence.Lang= %s', ctr, sent._.language['language'])
        return out_text_chunk

    #private function
    def get_random_string(self,length:int):
        # choose from all lowercase letter
        letters = string.ascii_letters
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    #private function
    def getFileSize(self,file_path:str) -> int:
        file_size = 0
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            return file_size
        else:
            self.baseLogger.critical('File does not exist : '  + file_path)
            return file_size
        
        
    def __init__(self, downloaded_file_path):
 
        spacy_on_gpu = spacy.prefer_gpu()
        if spacy_on_gpu:
            self.baseLogger.info("spacy module will use gpu")
        else:
            self.baseLogger.info("spacy module will use cpu")

        self.nlp_model = spacy.load("en_core_web_sm")
        Language.factory("language_detector", func=self.get_lang_detector)
        self.nlp_model.add_pipe('language_detector', last=True)

        if len(downloaded_file_path) > 0: ##A download path has been given as part of the constructor 
            self.downloaded_file_path = downloaded_file_path
            self.downloaded_file_size = self.getFileSize(self.downloaded_file_path)
            self.downloaded_file_dir = pathlib.PurePath(self.downloaded_file_path).parent
            self.downloaded_filename = pathlib.PurePath(self.downloaded_file_path).name
    
            #create directory for extracted text, text chunks
            ts = str( time.time() )
            
            self.extracted_text_file_dir = os.path.join(self.downloaded_file_dir, 'extract' + self.get_random_string(4) + ts)
            os.makedirs(self.extracted_text_file_dir)
            self.baseLogger.debug("Created a temporary directory path for extracted text file name: " +self. extracted_text_file_dir)
            ##the extracted text file name will replace any space " " in its name with "_" and will have .txt suffix 
            self.extracted_text_file_path = os.path.join(self.extracted_text_file_dir, self.downloaded_filename.replace(' ','_') ) + '.txt'      
            
            self.text_chunks_dir = os.path.join(self.downloaded_file_dir, 'chunks'+ self.get_random_string(4) + ts )
            os.makedirs(self.text_chunks_dir)
            self.baseLogger.debug("Created directory for text chunks: " + self.text_chunks_dir)
        else:
            self.baseLogger.info("The documentProcessor has been created without any downloaded_file_path")

    #public function    
    def setDownloadFilePath(self, downloaded_file_path):
 
        self.downloaded_file_path = downloaded_file_path
        self.downloaded_file_size = self.getFileSize(self.downloaded_file_path)
        self.downloaded_file_dir = pathlib.PurePath(self.downloaded_file_path).parent
        self.downloaded_filename = pathlib.PurePath(self.downloaded_file_path).name

        #create directory for extracted text, text chunks
        ts = str( time.time() )
        
        self.extracted_text_file_dir = os.path.join(self.downloaded_file_dir, 'extract' + self.get_random_string(4) + ts)
        os.makedirs(self.extracted_text_file_dir)
        self.baseLogger.debug("Created a temporary directory path for extracted text file name: " +self. extracted_text_file_dir)
        ##the extracted text file name will replace any space " " in its name with "_" and will have .txt suffix 
        self.extracted_text_file_path = os.path.join(self.extracted_text_file_dir, self.downloaded_filename.replace(' ','_') ) + '.txt'      
        
        self.text_chunks_dir = os.path.join(self.downloaded_file_dir, 'chunks'+ self.get_random_string(4) + ts )
        os.makedirs(self.text_chunks_dir)
        self.baseLogger.debug("Created directory for text chunks: " + self.text_chunks_dir)


    #public function
    def extractText(self):
        #This function will be written in inherited classes for each document type (xls, doc, pdf ....) 
        pass

    #private function
    def validateTextChunk(self,text_chunk:str)->str:
        out_text_chunk:str
        out_text_chunk = text_chunk
        try:
            out_text_chunk = self.detectLanguage(text_chunk)
        except:
            self.baseLogger.error('Error when validating the text chunk language')
        return out_text_chunk

    #private function
    def saveTextChunk(self, text_chunk_file_path:str, text_chunk:str):
        save_text_chunk = self.validateTextChunk(text_chunk)
        self.baseLogger.debug('Writing a text chunk at :' + text_chunk_file_path)
        #self.baselogger.debug('TEXTCHUNK:' + save_text_chunk)
        f = open(text_chunk_file_path,"w")
        f.write(save_text_chunk)
        f.close()
    

    #public function
    def createChunks(self):
        self.baseLogger.debug('MAXCHUNK SIZE is :' + str(self.MAXCHUNKSIZE))
        self.baseLogger.debug('Creating Chunks for ' + self.extracted_text_file_path)
        #This function should be called only after the extractText function has been called
        ## ##this dictionary will have key=/filepath_to_the_file_containing_text_chunk, value=integer value of the chunk number.
        chunk_dict = {}

        try:
        
            with open(  self.extracted_text_file_path,newline = "\n", encoding='ISO-8859-1') as txtfile:

                #We are using fill the bucket approach
                #We fill the current_text_chunk bucket with previous leftover words and words from new line
                #If the count whats in the bucket[word counter] + (previous leftover words + newline words) is less than bucket capacity(MAXCHUNKSIZE) then put both in the bucket, you have no leftovers 
                #If the previous leftover words and the newline will not fit in the bucket then start putting each word in the bucket until the bucket is full 
                #IF the bucket is full then we empty the bucket by saving it to a file,  the remaining words which could not be put in the bucke are treated as leftover words.
                #Process repeats until we reach end of line
                
                current_text_chunk = ''
                current_line = ''
                self.no_of_chunks = 0
                word_ctr = 0
            
                for newline in txtfile:
                    ##READ EACH LINE IN THE LOCAL TEXT FILE , REMOVE NEWLINE TO  REPLACE WITH WHITESPACE
                    #newline = newline.rstrip() ##Remove the trailing newline
                    newline = newline.rstrip()
                    current_line = current_line + newline
                    words_in_the_current_line =  current_line.split()
                    no_of_words_in_current_line = len(words_in_the_current_line)

                    while ((word_ctr <= self.MAXCHUNKSIZE) and ( no_of_words_in_current_line > 0)):  
                        self.baseLogger.debug('Word Counter: ' + str(word_ctr) + ' Words in current line: ' + str(no_of_words_in_current_line) )
                        
    
                        ##Add this line to current text chunk if the total number of words (word ctr + current_line) is below the MACHUNKSIZE 
                        if ((word_ctr + no_of_words_in_current_line) <= (self.MAXCHUNKSIZE) ):
                            #Fill the bucket with the current line since it fits in the remaining space of the text chunk bucket
                            current_text_chunk = current_text_chunk + ' ' + current_line
                            word_ctr = word_ctr + no_of_words_in_current_line ##Set size of the bucket (current total no of words)
                            #reset current line to blank
                            current_line = ''
                            words_in_the_current_line =  current_line.split()
                            no_of_words_in_current_line = 0

                            if word_ctr == self.MAXCHUNKSIZE:
                                #if the last fill has filled the text chunk bucket then save it to file
                                self.no_of_chunks = self.no_of_chunks + 1
                                chunk_file_path = os.path.join(self.text_chunks_dir, str(self.no_of_chunks) + '.txt')
                                self.baseLogger.debug('Text chunk full with this line.Write the text chunk no: ' + str(self.no_of_chunks) + ' to ' + chunk_file_path )
                                self.saveTextChunk(chunk_file_path,current_text_chunk)
                                chunk_dict[chunk_file_path] = self.no_of_chunks
                                ##The text chunk bucket has been saved. So reset current_text_chunk
                                current_text_chunk = ''
                                word_ctr = 0
                                self.baseLogger.debug('Text chunk full with this line. Added chunk number: ' + str(self.no_of_chunks))       
                        else:  
                            # the current line is too big
                            #Read each word iteratively. Stop when word counter either reaches the chunk size or 
                            # we have read all the words in the current + new line
                            i = 0
                            self.baseLogger.debug('We have to read each word in the line to fill in text chunk')
                            no_words_added_to_text_chunk = 0
                            while (word_ctr <= self.MAXCHUNKSIZE and i < no_of_words_in_current_line ):
                                current_text_chunk = current_text_chunk + words_in_the_current_line[i] + ' '
                                i = i + 1
                                word_ctr = word_ctr + 1
                                no_words_added_to_text_chunk = no_words_added_to_text_chunk + 1
                            
                                if word_ctr == self.MAXCHUNKSIZE:
                                    self.no_of_chunks = self.no_of_chunks + 1
                                    chunk_file_path = os.path.join(self.text_chunks_dir, str(self.no_of_chunks) + '.txt')
                                    self.baseLogger.debug('Text chunk full.Write the text chunk no: ' + str(self.no_of_chunks) + ' to ' + chunk_file_path )
                                    self.saveTextChunk(chunk_file_path,current_text_chunk)
                                    chunk_dict[chunk_file_path] = self.no_of_chunks
                                    current_text_chunk = ''
                                    word_ctr = 0
                                    self.baseLogger.debug('Text chunk full. Added chunk number: ' + str(self.no_of_chunks))
                                    current_line = '' ##Reset the current line
                                    new_no_of_words_in_the_current_line = 0
                                    while i < no_of_words_in_current_line :
                                        current_line =  current_line + words_in_the_current_line[i] + ' '
                                        i = i + 1
                                        new_no_of_words_in_the_current_line = new_no_of_words_in_the_current_line + 1
                                    no_of_words_in_current_line = new_no_of_words_in_the_current_line

                                    
                #After reading all the lines if the current_text_chunk has remaining words and we have read the last line, it should be saved as a new chunk     
                if(len(current_text_chunk) > 0 ):
                    self.no_of_chunks = self.no_of_chunks + 1
                    chunk_file_path = os.path.join(self.text_chunks_dir, str(self.no_of_chunks) + '.txt')
                    self.baseLogger.debug('Write the last text chunk no: ' + str(self.no_of_chunks) + ' to ' + chunk_file_path )
                    self.saveTextChunk(chunk_file_path, current_text_chunk)
                    chunk_dict[chunk_file_path] = self.no_of_chunks
                    self.baseLogger.debug('Added last chunk number: ' + str(self.no_of_chunks))
        except Exception as exc:
            self.baseLogger.error('We have a problem when creating text chunks for ' + self.extracted_text_file_path)
            self.baseLogger.error('Check text file encoding and also check if the extracted file was created')
        finally:
            self.baseLogger.info('Completed extracting text chunks')
            return chunk_dict








    
