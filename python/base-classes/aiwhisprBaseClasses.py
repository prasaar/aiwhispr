##This file implements all the base classes in aiwhispr
##We dont use typical __ because there is no real private variable in python
import random
import string
import os
import sys
import pathlib
import logging
import time


sys.path.append("../common-functions")
import aiwhisprConstants


#Base Class siteAuth
class siteAuth:

    auth_type:str
    site_userid:str
    site_password:str
    sas_token:str

    def __init__(self,auth_type,site_userid,site_password):
        self.auth_type = auth_type
        self.site_userid = site_userid
        self.site_password = site_password

    def __init__(self,auth_type,sas_token):
         self.auth_type = auth_type
         self.sas_token = sas_token



#Base Class vectorDb:
class vectorDb:
    vectordb_type:str
    vectordb_hostname:str
    vectordb_portnumber:str
    vectordb_key:str

    def __init__(self,vectordb_type,vectordb_hostname,vectordb_portnumber, vectordb_key):
        self.vectordb_type = vectordb_type
        self.vectordb_hostname = vectordb_hostname
        self.vectordb_portnumber = vectordb_portnumber
        self.vectordb_key = vectordb_key

    #public function 
    def insert(self):
        pass

    #public function
    def purge(self):
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

#Base Class srcContentSite
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
    def __init__(self, content_site_name:str, src_type:str, src_path:str, src_path_for_results:str, working_directory:str, index_log_directory:str, vector_db:vectorDb ):
        self.content_site_name = content_site_name
        self.src_type = src_type
        self.src_path = src_path
        self.src_path_for_results = src_path_for_results
        self.working_directory = working_directory
        self.index_log_directory = index_log_directory
        self.vector_db = vector_db
        
    #Init with siteAuth e.g.  azureblob,s3,gs
    def __init__(self, content_site_name:str, src_type:str, src_path:str, src_path_for_results:str, working_directory:str, index_log_directory:str, site_auth:siteAuth, vector_db:vectorDb ):
        self.content_site_name = content_site_name
        self.src_type = src_type
        self.src_path = src_path
        self.src_path_for_results = src_path_for_results
        self.working_directory = working_directory
        self.index_log_directory = index_log_directory
        self.vector_db = vector_db
        self.site_auth = site_auth
       

    #These operations shold be implemented is the sub(child) classes
    #public function
    def connect(self):
        pass

    #public function
    def index(self):
        pass

    #public function
    def purge(self):
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

#Base class for Document Processors which extract text, then chunk the text
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
        self.extracted_text_file_path = os.path.join(self.extracted_text_file_dir, self.downloaded_filename.replace(' ','_') , '.txt')      
      
        
        
        self.text_chunks_dir = os.path.join(self.downloaded_file_dir, 'chunks'+ self.get_random_string(4) + ts )
        os.makedirs(self.text_chunks_dir)
        self.baseLogger.debug("Created directory for text chunks: " + self.text_chunks_dir)

    #public function
    def extractText(self):
        #This function will be written in inherited classes for each document type (xls, doc, pdf ....) 
        pass

    #private function
    def saveTextChunk(self, text_chunk_file_path:str, text_chunk:str):
        try:
            self.baseLogger.debug('Writing a text chunk at :' + text_chunk_file_path)
            f = open(text_chunk_file_path,"w")
            f.write(text_chunk)
            f.close()
        except:
            self.baseLogger.error('Could not write the text chunk to file:' + text_chunk_file_path )
        
    #public function
    def createChunks(self):
        self.baseLogger.debug('MAXCHUNK SIZE is :' + str(self.MAXCHUNKSIZE))
        self.baseLogger.debug('Creating Chunks for ' + self.extracted_text_file_path)
        #This function should be called only after the extractText function has been called
        ## ##the chunks will be 1.txt , 2.txt ......
        #with open(  self.extracted_text_file_path,newline = "\n", encoding='ISO-8859-1') as txtfile:
        with open(  self.extracted_text_file_path,newline = "\n") as txtfile:

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
                newline = newline.rstrip() ##Remove the trailing newline
                current_line = current_line + newline
                words_in_the_current_line =  current_line.split()
                no_of_words_in_current_line = len(words_in_the_current_line)

                while ((word_ctr <= self.MAXCHUNKSIZE) and ( no_of_words_in_current_line > 0)):  
                    self.baseLogger.debug('Word Counter: ' + str(word_ctr) + ' Words in current line: ' + str(no_of_words_in_current_line) )
                    #We are in a loop so first check if the chunk bucket is full
                    # If the word counter has reached MAXCHUNKSIZE then first save the text chunk and reset the word counter, text chunk
                    #if word_ctr == self.MAXCHUNKSIZE:
                    #    self.no_of_chunks = self.no_of_chunks + 1
                    #    chunk_file_path = os.path.join(self.text_chunks_dir, str(self.no_of_chunks) + '.txt')
                    #    self.baseLogger.debug('Write the text chunk no: ' + str(self.no_of_chunks) + ' to ' + chunk_file_path )
                    #    self.saveTextChunk(chunk_file_path,current_text_chunk)
                    #    current_text_chunk = ''
                    #   word_ctr = 0
                    #   self.baseLogger.debug('Added chunk number: ' + str(self.no_of_chunks))
 
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
                self.baseLogger.debug('Added last chunk number: ' + str(self.no_of_chunks))
