# AIWhispr

## Overview
AIWhispr is a tool to enable  semantic search on documents 
- It is easy to install,
- Simple to cofigure
- can ingest  multiple file types (txt,csv, pdf, docx,pptx, docx) from AWS S3, Azure Blob Containers, local directory path  
- Delivers fast semantic response to search queries,

## Contact
contact@aiwhispr.com

## Prerequisite software, python packages 

### Download Typesense and install
AIWhispr uses Typesense to store text, corresponding vector embeddings created by the LLM.
A big Thanks!! to the Typesense team, community. 
You can follow the instructions on 
https://typesense.org/docs/guide/install-typesense.html

Store the "api-key" value from the typesense configuration file ( /etc/typesense/typesense-server.ini )
You will need this later to configure the AIWhispr service.

### Prerequisite Python packages
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

##Environment variables
Setup the AIWHISPR_HOME_DIR environment variable as the fullpath to aiwhispr directory setup by git clone
Setup AIWHISPR_LOG_LEVEL environment variable to  one of the following values: DEBUG / INFO / WARNING / ERROR
If you dont provide AIWHISPR_LOG_LEVEL then the default is DEBUG


