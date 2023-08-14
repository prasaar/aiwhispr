
# AIWhispr

## Overview of the config file

The configuration file has 5 sections

**[content-site]**

Section to configure the source from which AIWhispr will read the files which have to be indexed. 
```
sitename=<sets a unique name for this configuration, content indexing(CONFIGURED)>
srctype= <Can be filepath / s3 / azureblob. is for an Azure Blob container.(CONFIGURED)>
srcpath = <path from which AIWhisper will start reading and indexing the content(CONFIGURED)>
displaypath = <top level path that AIWhispr will use when returning the search results. Example : you can save all your files under /var/www/html , when the search results are displayed, the top level path is replaced with http://hostname (CONFIGURED FOR localhost)>
contentSiteModule = <python module that handles indexing for files/content in the specified srctype.There are test configuration examples in the same folder for s3 , azureblob. You can extend the base class and write your custom handlers under $AIWHISPR_HOME/python/content-site(CONFIGURED)>
```

**[content-site-auth]**
Section to configure access to the source from which files, content will be read.

```
authtype=<Type of authentication for reading the content files. This can be filechecks / aws-key / sas (Azure SAS Token)/ az-storage-key (CONFIGURED)>
```

Examples are available for AWS, Azure in the same directory.

**[vectordb]**
Section to configure the vector database access and the python module that will handle the storage schema, access.

```
api-address = <typesense-api-adress(EDIT)>
api-port = <typesense-port(EDIT)>
api-key = <typesense-api-key(EDIT)>
vectorDbModule=<python module to handle the vectordb storage schema. You can write your own handlers under $AIWHISPR_HOME/python/vectordb(CONFIGURED)>
```

**[local]**
AIWhispr requires a local working directory that is used to extract text.The working-dir can be cleaned up after indexing.

The index-dir configuration points to a path where AIWhispr will store a local SQLite3 database which is used when indexing the content. 

Remember to change them from /tmp to a separate folder in production.

```
working-dir=/tmp
index-dir=/tmp
```

**[llm-service]**
Section to configure the large-language-model (LLM) used to create the vector embedding. AIWhispr uses sentence-transformer library.
You can customize this by writing your own LLM encoding handler under $AIWHISPR_HOME/python/llm-service

The default configuration is:

```
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
llmServiceModule=libSbertLlmService
```