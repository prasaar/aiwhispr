#AIWhispr

##Overview
AIWhispr is a semantic search engine that is 
- easy to install,
- fast response time to search queries,
- can ingest  multiple file types, data sources(on OS,Cloud) with simple configuration.

## Guardrails
- A semantic search engine should be easy to install.  Developers , system administrators, users should be able to follow the instruction to install and configure the semantic search engine without any source code changes.
- A semantic search engine should have fast response times for search queries. Take more time for data preparation, indexing if it helps improve the search response time.
- A semantic search engine should be able to ingest content from both on OS, cloud (e.g. Azure Blob, AWS S3 ) with simple configuration, no code changes.
- A semantic search engine should be able to ingest multiple file types. If a file type is not handled then code changes should be minimum.
- A semantic search engine should clean the data before it submits it to the LLM for encoding. 
- A semantic search engine should be able to run in multiple levels of logging (DEBUG,CRITICAL,ERROR, INFO) so that developers, system administrators can monitor the health, setup alerts.
- Every AIWhispr feature will be built based on community feedback.Feedback from users will define the desired outcome of the feature.


##Contact
contact@aiwhispr.com

##License
GNU GPL

##Prerequisite : Install and configure Typesense vector database

###Download Typesense and install
You can follow the instructions on 
https://typesense.org/docs/guide/install-typesense.html

###Configure Typesense for aiwhispr
Run the below setup commands [ Example is for Ubuntu Linux.]

```
sudo vi /etc/typesense/typesense-server.ini 
```
Open the configuration file for typesense server
You will see the contents similar to 

```
; Typesense Configuration

[server]

api-address = 0.0.0.0
api-port = 8108
data-dir = /var/lib/typesense
api-key = <TYPESENSE_ADMIN_API_KEY>
log-dir = /var/log/typesense
```

Now change the data-dir and log-dir configurations to a separate directory which keeps aiwhispr
Example
```
data-dir = /aiwhispr-data/typesense
log-dir = /aiwhispr-data/log/typesense
```
Also, store the <TYPESENSE_ADMIN_API_KEY> safely. You will need this later to setup the schema for the vector database.


The below  3 commands will create the data and log directories before you start the type sense-server with the changed configuration.
```
sudo  mkdir /aiwhispr-data/typesense 
sudo  mkdir /aiwhispr-data/log 
sudo  mkdir /aiwhispr-data/log/typesense
```

Confirm that the typsesense-server is enabled
```
sudo systemctl status typesense-server.service

```
Restart the typsesense-server 
```
sudo systemctl  stop  typesense-server.service
sudo systemctl  start typesense-server.service
```

Check that typesense database directory structure is created
```
ls -l /aiwhispr-data/typesense 

Output should be like
```
total 12
drwxr-xr-x 3 root root 4096 Jul 27 06:35 db
drwxr-xr-x 3 root root 4096 Jul 27 06:35 meta
drwxr-xr-x 5 root root 4096 Jul 27 06:35 state
```

Check that typesense log file created , like
```
ls -l /aiwhispr-data/log/typesense 
```

Output should be like
```
total 12
-rw-r--r-- 1 root root 9600 Jul 27 06:37 typesense.log
```

Allow the Linux firewall to open the Typesense-Server port.
```
sudo ufw allow 8108
```
Check the health status of typesense-server
```
curl http://localhost:8108/health
```

install the typesense client
```
pip3 install typesense
```
##Prerequisite Python packages

###Azure
```
pip install azure-storage-blob 
pip install azure-identity
```

###SpaCy
```
pip install -U pip setuptools wheel
pip install -U spacy
python -m spacy download en_core_web_sm
pip install spacy-language-detection
```

###AWS
```
pip install boto3 
```

### Document Reader which will extract text from different document types
```
pip install pypdf
```

##Environment variables
You can setup the AIWHISPR_HOME_DIR environment variable 

##Security of AIWhispr config files
Configuration files for each content site is stored under $AIWHISPR_HOME_DIR/config/sites-available/
The config files that AIWhispr reads contains the access keys , so please ensure that these config files don't have public read access.Also ensure that these config files are not managed under a public source code repository.
    
