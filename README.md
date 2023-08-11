# AIWhispr

## Overview
AIWhispr is a tool to enable  semantic search on documents 
- It is easy to install,
- Simple to cofigure
- can ingest  multiple file types (txt,csv, pdf, docx,pptx, docx) from AWS S3, Azure Blob Containers, local directory path  
- Delivers fast semantic response to search queries,

## Contact
contact@aiwhispr.com

## Prerequisites 

### Download Typesense and install
AIWhispr uses Typesense to store text, corresponding vector embeddings created by the LLM.
A big Thanks!! to the Typesense team, community. You can follow the installation instructions - 
 
https://typesense.org/docs/guide/install-typesense.html

Store the "api-key" value from the typesense configuration file ( On unix /etc/typesense/typesense-server.ini )

You will need this later to configure the AIWhispr service.

### Python packages
```
pip3 install typesense
pip3 install azure-storage-blob 
pip3 install azure-identity
pip3 install -U pip setuptools wheel
pip3 install -U spacy
python -m spacy download en_core_web_sm
pip3 install spacy-language-detection
pip3 install boto3 
pip3 install shutil
pip3 install pypdf
pip3 install textract
pip3 install -U sentence-transformers
pip3 install flask
```

### Environment variables
Setup the AIWHISPR_HOME_DIR environment variable as the fullpath to aiwhispr directory setup by git clone

Setup AIWHISPR_LOG_LEVEL environment variable to  one of the following values: DEBUG / INFO / WARNING / ERROR
```
AIWHISPR_HOME=/<...>/aiwhispr
AIWHISPR_LOG_LEVEL=DEBUG
export AIWHISPR_HOME
export AIWHISPR_LOG_LEVEL
```

## Your first setup
AIWhispr package comes with sample data, nginx configuration, index.html for nginx setup , python (flask) script to help you get started.

**1. Configuration file**

A configuration file is maintained under $AIWHISPR_HOME/config/content-site/sites-available directory. You can use the example_bbc.filepath.cfg to try your first configuration.
```
[content-site]
sitename=example_bbc.filepath
srctype=filepath
#Assuming that you have copied the $AIWHISPR_HOME/examples under your Webserver's directory orconfigured routing
srcpath=/var/www/html/bbc
#Remember to change the hostname
displaypath=http://<hostname>/bbc
#contentSiteClass is the module that will manage the content site
contentSiteModule=filepathContentSite
[content-site-auth]
authtype=filechecks
check-file-permission=Y
[vectordb]
api-address = <typesense-host-name>
api-port = <typesense-port>
api-key = <typesense-api-key>
vectorDbModule=typesenseVectorDb
[local]
##Remember to chenage them from /tmp to a seprate folder you have created for aiwhispr indexing 
working-dir=/tmp
index-dir=/tmp
[llm-service]
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
llmServiceModule=libSbertLlmService
```

[content-site]

Section to configure the source from which AIWhispr will read the files which have to be indexed. 
sitename=<sets a unique name for this configuration, content indexing>
```
srctype= <Can be filepath / s3 / azureblob. A filepath means a locally accessible directory path, s3 is for a AWS S3 bucket, azureblob is for a  Azure Blob container.>
srcpath = <path from which AIWhisper will start reading and indexing the content>
displaypath = <top level path that AIWhispr will use when returning the search results. Example : you can save all you your files under /var/www/html , when the search results are displayed, the top level path is replaced with http://hostname >
contentSiteModule = <python module that handles indexing for files/content in the specified srctype.There are are test configuration examples in the same folder for s3 , azureblob. You can extend the base class and write your custom handlers under $AIWHISPR_HOME/python/content-site>
```

[content-site-auth]
Section to configure access to the source from which files, content will be read.

```

authtype=<Type of access / authentication. This can be filechecks / aws-key (for AWS Key authentication) / az-storage-key (for Azure Storage Key) / sas (for Azure SAS Token authenticatio)
```

Examples are available for AWS, Azure in the same directory.

[vectordb]
Section to configure the vector databaase access and the python module that will handle the storage schema, access.

```
api-address = <typesense-host-name>
api-port = <typesense-port>
api-key = <typesense-api-key>
vectorDbModule=<python module to handle the vectordb storage schema. You can write your own handlers under $AIWHISPR_HOME/python/vectordb>
```

[local]
AIWhispr requires a local working directory which is used to sotre the read files, extract text.The working-dir can be cleaned up after indexing.

The index-dir configuration points to a path where AIWhispr will store a local SQLite3 database which is used when indexing the content. 

Remember to change them from /tmp to a seprate folder in production.

```
working-dir=/tmp
index-dir=/tmp
```

[llm-service]
Section to configure the large-language-model (LLM) used to create the vector embedding. AIWhispr uses sentence-transformer library.
You can customise this by writing your own LLM enciding handler under $AIWHISPR_HOME/python/llm-service

The default configuration is:

```
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
llmServiceModule=libSbertLlmService
```

**2. Start Indexing**
Confirm that the environment variables AIWHISPR_HOME and AIWHISPR_LOG_LEVEL are set and exported. 

For your first run set AIWHISPR_LOG_LEVEL=DEBUG 

The example assumes that you have setup the content files you want to index under /var/www/html (your webserver root)
Copy the sample data
```
cp -R $AIWHISPR_HOME/examples/data/bbc /var/www/html/
```

Index the file content for smeantic search
```
echo $AIWHISPR_HOME
echo $AIWHISPR_LOG_LEVEL
$AIWHISPR_HOME/shell/start-indexing-content-site.sh -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.cfg
```
