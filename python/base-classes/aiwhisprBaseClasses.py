##This file implements all the base classes in aiwhispr
##We dont use typical __ because there is no real private variable in python

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

    def insert(self):
        pass

    def purge(self):
        pass

    def update(self):
        pass

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
    #Init withoout siteAuth e.g. local file directory
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
    def connect(self):
        pass

    def index(self):
        pass

    def purge(self):
        pass

    def display(self):
        pass
