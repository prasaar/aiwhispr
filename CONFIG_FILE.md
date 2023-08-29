
# AIWhispr

## Overview of the config file

The configuration file has 5 sections

**[content-site]**

Section to configure the source from which AIWhispr will read the files which have to be indexed. 
```
sitename=<unique name; it has to be unique if you are using multiple configuration files. 
          Cannot contain whitespace, special characters except '.'  >

srctype= <Can be filepath / s3 / azureblob >

srcpath = <path from which AIWhispr will start reading and indexing files>

displaypath = <top level path that AIWhispr will use when returning the search results. 
              Example : you can save all your files under /var/www/html , 
              when the search results are displayed, 
              the top level path is replaced with http://hostname >

contentSiteModule = <python module that handles indexing for files/content in the specified srctype.
                    There are test configuration examples for s3 , azureblob. 
                    Custom modules can go under $AIWHISPR_HOME/python/content-site>

doNotReadDirList=<A comma seprated list of directories that should not be read.
                  If srctype=filepath then the full path to the directory is required
                  example: doNotReadDirList=//var/www/html/bbc/sport
                  For 3 / azure blob dont included the Bucket Name / Container Name>

doNotReadFileList=<A comma seprated list of filenames/filename pattersn that should not be read>
```

**[content-site-auth]**
Section to configure access to the source from which files, content will be read.

```
authtype=<Type of authentication for reading the content files. 
          This can be filechecks / aws-key / sas / az-storage-key 
          filechecks : is applicable for srctype=filepath
          sas : is applicable for Azure SAS token
          az-storage-key: is applicable for Azure Storage Key
          aws-key: is applicable for AWS S3 (Signed / Unsigned) >

key=<Specify the key value if authtype=aws-key/az-storage-key
    set this to UNISGNED to for AWS S3 unsigned access>

sastoken=<Azure SAS Token: applciable when authtype=sas>
```

Examples are available for AWS, Azure in the same directory.

**[vectordb]**
Section to configure the vector database access and the python module that will handle the storage schema, access.

```
api-address = <vectordb-api-adress>
api-port = <vectordb-api-port(EDIT)>
api-key = <vectordb-api-key(EDIT)>
vectorDbModule=<python module to handle the vectordb storage schema. 
                You can write your own handlers under $AIWHISPR_HOME/python/vectordb>
```

**[local]**
AIWhispr requires a local working directory that is used to extract text.
The working-dir can be cleaned up after indexing.

The index-dir configuration points to a path where AIWhispr will store a local SQLite3 database which is used when indexing the content. 

Remember to change them from /tmp to a separate folder in production. 

Keep the index-dir and working-dir in seprate directories which in production for a clean setup.

indexing-processes is configured  to an integer value 1 or greater. It should not be greater than the number of CPU's on the machine
AIWhispr spawns multiple processes for indexing based on this value.

Spawning of of multiple indexing processes is effective when you have GPU's and CPU.

If you have only CPU's  then this should be set to 50% of the CPU's on the machine so that you have enough CPU's for other processes.

Example: on a 4 CPU machine, set  indexing-processes=2
```
working-dir=/tmp
index-dir=/tmp
indexing-processes=<int:should_be_less_than_no_of_cpu>
```

**[llm-service]**
Section to configure the large-language-model (LLM) used to create the vector embedding. 
AIWhispr uses sentence-transformer library.
You can customize this by writing your own LLM encoding handler under $AIWHISPR_HOME/python/llm-service

The default configuration is:

```
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
llmServiceModule=libSbertLlmService
```
