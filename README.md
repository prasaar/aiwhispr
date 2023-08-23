# AIWhispr

## Overview
AIWhispr is a tool to enable AI powered semantic search on documents 
- It is easy to install.
- Simple to configure.
- Can handle multiple file formats (txt,csv, pdf, docx,pptx, docx) stored on AWS S3, Azure Blob Containers, local directory path.
- Delivers fast semantic response to search queries.

![Alt Text](./resources/aiwhispr-example.gif)

## Contact
contact@aiwhispr.com

## Prerequisites for a Linux install with Typesense

[For Linux install with Qdrant vector database, refer to example_with_qdrant.md](./howto/example_with_qdrant.md)

[For MacOS refer to README_MACOS.md](./howto/README_MACOS.md)

For Windows 10/11 you can follow the same instructions as below on wsl (Windows Subsystem for Linux) 

### Environment variables
AIWHISPR_HOME_DIR environment variable should be the full path to aiwhispr directory.

AIWHISPR_LOG_LEVEL environment variable can be set to  DEBUG / INFO / WARNING / ERROR
```
AIWHISPR_HOME=/<...>/aiwhispr
AIWHISPR_LOG_LEVEL=DEBUG
export AIWHISPR_HOME
export AIWHISPR_LOG_LEVEL
```
### Download Typesense and install
AIWhispr uses Typesense to store text, corresponding vector embeddings created by the LLM.
A big Thanks!! to the Typesense team, community. You can follow the installation instructions - 
 
https://typesense.org/docs/guide/install-typesense.html

Note down the "api" values from the typesense configuration file typically at /etc/typesense/typesense-server.ini

You will need this later to configure the AIWhispr service.
```
cat /etc/typesense/typesense-server.ini | grep api
```

### Python packages
```
$AIWHISPR_HOME/shell/install_python_packages.sh
```
If uwsgi install is failing then ensure you have gcc, python-dev , python3-dev installed.
```
sudo apt-get install gcc 
sudo apt install python-dev
sudo apt install python3-dev
pip3 install uwsgi
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
./configure_example_filepath_typesense.sh
```

It will finally display a config file that has been created.
```
#### CONFIG FILE ####
[content-site]
sitename=example_bbc.filepath.typesense
srctype=filepath
srcpath=/<aiwhispr_home>/aiwhispr/examples/http/bbc
displaypath=http://127.0.0.1:9000/bbc
contentSiteModule=filepathContentSite
[content-site-auth]
authtype=filechecks
check-file-permission=Y
[vectordb]
vectorDbModule=typesenseVectorDb
api-address= 0.0.0.0
api-port= 8108
api-key= xyz
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
ls $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.typesense.cfg
```

For more details about sections in the config file please refer to [CONFIG_FILE.md](./CONFIG_FILE.md)

**2. Start Indexing**
Confirm that the environment variables AIWHISPR_HOME and AIWHISPR_LOG_LEVEL are set and exported.

Index the file content for semantic search. This will take some time as it has to process over 2000 files.
```
$AIWHISPR_HOME/shell/start-indexing-content-site.sh -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.typesense.cfg
```

**3. Start the AIWhispr search service**

3 services will be started under this shell script.

- the AIWhispr searchService(port:5002) which intefaces with the vectordb

- a flask python script(port:9001) that takes in user query , sends the query  to AIWhispr searchService and formats the results for HTML display

- a python http.server(port 9000)

The log files for these 3 processes is created in /tmp/

```
cd $AIWHISPR_HOME/examples/http; $AIWHISPR_HOME/examples/http/start_search_filepath_typesense.sh
```

### Ready to go
Try the search on http://127.0.0.1:9000/IP Address>

Some examples of meaning drive search queries

"What are the top TV moments in Olympics"

"Which is the best laptop to buy"

"How is inflation impacting the economy"

You can compare the semantic search results against text search results.

## How can I access through an internet facing IP/host

If you want to access the search site through an internet facing IP/host then then do the following changes

**1. Edit the config file.**

In file $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.cfg

edit displaypath  configuration

From
```
displaypath=http://127.0.0.1:9000/bbc
```

To
```
displaypath=http://<Internet IP/domain>:9000/bbc 
```

**2. Edit the index.html file for the example**

edit $AIWHISPR_HOME/examples/http/index.html 


Edit index.html, replace 127.0.0.1  with your server IP/hostname

From
```
 <form action = "http://127.0.0.1:9001/search" method = "post">
```

To
```
 <form action = "http://<Internet IP/host>:9001/search" method = "post">
```

**3. Open the firewall for ports 9000, 9001**

```
sudo ufw allow 9000
sudo ufw allow 9001
```
On a cloud server, you might have to edit the firewall configs on your cloud providers portal too.

For a secure approach using nginx installation, you can follow  [README_NGINX.md](./README_NGINX.md]

**4. Kill the existing search service processes and restart**

Find the existing processes and issue a kill command to stop them
```
ps -ef | grep searchService.py 

ps -ef | grep exampleHttpResponder.py 

ps -ef | grep 'python3 -m http.server 9000'
```

Restart the processes 

```
cd $AIWHISPR_HOME/examples/http; $AIWHISPR_HOME/examples/http/start_http_service.sh
```


