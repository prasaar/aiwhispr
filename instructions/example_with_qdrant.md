# AIWhispr

## Overview
AIWhispr is a tool to enable AI powered semantic search on documents 
- It is easy to install.
- Simple to configure.
- Can handle multiple file formats (txt,csv, pdf, docx,pptx, docx) stored on AWS S3, Azure Blob Containers, local directory path.
- Delivers fast semantic response to search queries.

![Alt Text](../resources/aiwhispr-example.gif)

## Contact
contact@aiwhispr.com

## Prerequisites for a Linux install with Qdrant as vector database

### Environment variables
AIWHISPR_HOME_DIR environment variable should be the full path to aiwhispr directory.

AIWHISPR_LOG_LEVEL environment variable can be set to  DEBUG / INFO / WARNING / ERROR
```
AIWHISPR_HOME=/<...>/aiwhispr
AIWHISPR_LOG_LEVEL=DEBUG
export AIWHISPR_HOME
export AIWHISPR_LOG_LEVEL
```
### Download Qdrant and install

[Install instructions at Qdrant site](https://qdrant.tech/documentation/quick-start/)

Or

Download from DockerHub
```
docker pull qdrant/qdrant
```

Run the service
```
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

Qdrant should be accessible at localhost:6333


### Python packages
```
$AIWHISPR_HOME/shell/install_python_packages.sh
```

**Remember to add the environment variables in your shell login script**

## Your first setup
**1. Configuration file**

A configuration file is maintained under $AIWHISPR_HOME/config/content-site/sites-available

We will use the example under examples/http to create a config file to index over 2000+ files which contain BBC news content.

To create the config file run the following commands. 

You can enter "N" and choose to go with the default values
```
cd $AIWHISPR_HOME/examples/http
./configure_example_filepath_qdrant.sh
```

It will finally display a config file that has been created.
```
#### CONFIG FILE ####
[content-site]
sitename=example_bbc.filepath.qdrant
srctype=filepath
srcpath=/<aiwhispr_home>/aiwhispr/examples/http/bbc
displaypath=http://127.0.0.1:9000/bbc
contentSiteModule=filepathContentSite
[content-site-auth]
authtype=filechecks
check-file-permission=Y
[vectordb]
vectorDbModule=qdrantVectorDb
api-address= localhost
api-port= 6333
api-key= 
[local]
working-dir=/<aiwhispr_home>/aiwhispr/examples/http/working-dir
index-dir=/<aiwhispr_home>/aiwhispr/examples/http/working-dir
[llm-service]
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
llmServiceModule=libSbertLlmService
```

Check that config file has been created.
```
ls $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.qdrant.cfg
```

For more details about sections in the config file please refer to [CONFIG_FILE.md](./CONFIG_FILE.md)

**2. Start Indexing**
Confirm that the environment variables AIWHISPR_HOME and AIWHISPR_LOG_LEVEL are set and exported.

Index the file content for semantic search. This will take some time as it has to process over 2000 files.
```
($AIWHISPR_HOME/shell/start-indexing-content-site.sh -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.qdrant.cfg &>/tmp/example_bbc.filepath.qdrant.log &)
```
The log file is /tmp/example_bbc.filepath.qdrant.log

**3. Start the AIWhispr search service**

3 services will be started under this shell script.

- the AIWhispr searchServic(port:5002) which intefaces with the vectordb

- a flask python script(port:9001) that takes in user query , sends the query  to AIWhispr searchService and formats the results for HTML display

- a python http.server(port 9000)

The log files for these 3 processes is created in /tmp/

```
cd $AIWHISPR_HOME/examples/http; $AIWHISPR_HOME/examples/http/start_search_filepath_qdrant.sh
```

### Ready to go
Try the search on http://127.0.0.1:9000/IP Address>

Some examples of meaning drive search queries

"What are the top TV moments in Olympics"

"Which is the best laptop to buy"

"How is inflation impacting the economy"

You can compare the semantic search results against text search results.

