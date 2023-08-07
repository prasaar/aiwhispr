##This file implements all the base classes in aiwhispr
##We dont use typical __ because there is no real private variable in python
from pyexpat import model
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


sys.path.append("../common-functions")
import aiwhisprConstants

#BASE CLASS: siteAuth
#Support S3, Azureblob, filepath mounts
#If you want to include other types of authentication then inherit from this class and you can process the cofigurations from kwargs
class siteAuth:

    auth_type:str
    site_userid:str
    site_password:str
    sas_token:str
    az_key:str
    aws_access_key_id:str
    aws_secret_access_key:str
    check_file_permission:str
    auth_config: dict
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
            case other:
                self.logger.debug('Dont know how to handle the auth type %s', self.auth_type)
                self.auth_config = kwargs['auth_config']
                if self.auth_config != None:
                    self.logger.debug("The auth_config dictionary is %s", str(self.auth_config) )            

#BASE CLASS: vectorDb:
class vectorDb:
    vectordb_type:str
    vectordb_hostname:str
    vectordb_portnumber:str
    vectordb_key:str
    content_site_name:str 
    src_path:str 
    src_path_for_results:str

    def __init__(self,vectordb_hostname,vectordb_portnumber, vectordb_key, content_site_name:str,src_path:str,src_path_for_results:str):
        self.vectordb_hostname = vectordb_hostname
        self.vectordb_portnumber = vectordb_portnumber
        self.vectordb_key = vectordb_key
        self.content_site_name = content_site_name
        self.src_path = src_path
        self.src_path_for_results = src_path_for_results

        self.baseLogger = logging.getLogger(__name__)
        self.baseLogger.debug("vectordb_hostname = %s", self.vectordb_hostname)
        self.baseLogger.debug("vectordb_portnumber = %s", self.vectordb_portnumber)
        self.baseLogger.debug("vectordb_key = %s", self.vectordb_key)
        self.baseLogger.debug("content_site_name = %s", self.content_site_name)
        self.baseLogger.debug("src_path = %s", self.src_path)
        self.baseLogger.debug("src_path_for_results = %s", self.src_path_for_results)
        

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
    #the Derives classes are isntatiated dynamically so it's important we have a common signature.
    def __init__(self, content_site_name:str, src_type:str, src_path:str, src_path_for_results:str, working_directory:str, index_log_directory:str, site_auth:siteAuth, vector_db:vectorDb ):
        self.content_site_name = content_site_name
        self.src_type = src_type
        self.src_path = src_path
        self.src_path_for_results = src_path_for_results
        self.working_directory = working_directory
        self.index_log_directory = index_log_directory
        self.site_auth = site_auth
        self.vector_db = vector_db
        
    #These operations shold be implemented is the sub(child) classes
    #public function
    def connect(self):
        pass

    #public function
    def index(self):
        pass

    #public function
    def deleteAll(self):
        pass

    #public function
    def display(self):
        pass

    #private function
    def get_random_string(self,length:int):
        # choose from all lowercase letter
        letters = string.ascii_letters
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str
        
    #This funtion creates the download path
    #private function
    def getDownloadPath(self,content_path:str) -> str:
        filename = pathlib.PurePath(content_path).name
        site_working_directory_subdir = os.path.join( self.working_directory , self.content_site_name)
        isDirExist = os.path.exists(site_working_directory_subdir)
        if not isDirExist:
               os.makedirs(site_working_directory_subdir)
               self.baseLogger.debug('Created working directory ' + site_working_directory_subdir)

        directory_path = os.path.join(site_working_directory_subdir , self.get_random_string(8) )
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

        self.nlp_model = spacy.load("en_core_web_sm")
        Language.factory("language_detector", func=self.get_lang_detector)
        self.nlp_model.add_pipe('language_detector', last=True)

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
        ## ##the chunks will be 1.txt , 2.txt ......
        chunk_id_dict = {}

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
                                chunk_id_dict[chunk_file_path] = self.no_of_chunks
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
                                    chunk_id_dict[chunk_file_path] = self.no_of_chunks
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
                    chunk_id_dict[chunk_file_path] = self.no_of_chunks
                    self.baseLogger.debug('Added last chunk number: ' + str(self.no_of_chunks))
        except Exception as exc:
            self.baseLogger.error('We have a problem when creating text chunks for ' + self.extracted_text_file_path)
            self.baseLogger.error('Check text file encoding and also check if the extracted file was created')
        finally:
            self.baseLogger.info('Completed extracting text chunks')
            return chunk_id_dict




#BASE CLASS: baseLlmModel
class baseLlmModel:
    model_name:str
    isApi:Boolean
    isLibrary:Boolean

    def __init__(self)
        pass




    