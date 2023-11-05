# Flask App Services

AIWhispr is a no/low code tool to automate vector embedding pipelines for semantic search.
A simple configuration drives the pipeline for reading files, extracting text, create vector embeddings and storing them in a vector database.

## Index Service
The indexing service is an API service that accepts a Json payload for semantic index.
The indexing service is started using the below command

```
python3 $AIWHISPR_HOME/python/flask-app/indexingService.py -H 127.0.0.1 -P 10001 -C <PATH_TO_CONFIG_FILE>
```

The configuration file is generally maintained under $AIWHISPR_HOME/config/index-service/

A typical figuration file for MongoDb as the vector database, SBert all-mpnet-base-v2 for vector embeddings. 
```
[content-site]
sitename=<uniqe_name.myconfig>
srctype=index-service
srcpath=
displaypath=aiwhisprStreamlit
contentSiteModule=indexServiceContentSite
[content-site-auth]
authtype=index-service-key
access-key-id=<password_to_access_index_service>
[vectordb]
vectorDbModule=<mongodbVectorDb>
connection-string=mongodb+srv://mongodbUser:myPasswrod@cluster0.mongodb.mongodb.net/
dbname=<dbname>
collection-name=<collection_name>
vector-index=<atlas_search_vector_index_created_using_dashboard>
text-index=<atlas_search_text_index>
vector-dim=768
[llm-service]
llmServiceModule=libSbertLlmService
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
chunk-size=307
[local]
working-dir=/tmp
index-dir=/tmp
indexing-processes=1
```

The Json payload example: 
```
{
 "id": "UUID", 
 "content_path": "https://site.domain.com/mycontent1", 
 "tags": "TAG1 TAG2", 
 "text_chunk": "This is the text section", 
 "text_chunk_no": 1, 
  "access_key_id": <password_to_access_index_service>
}
```

The directory $AIWHISPR_HOME/examples/index-service contains python based example to test the index service.
The file nike_data.json contains 112 json records which are loaded using
```
cd $AIWHISPR_HOME/examples/index-service
./load_json.py
```
The python script load_json.py 
```
import json
import requests

url_post = "http://127.0.0.1:10001/index"

f_in = open("./nike_data.json")
data_in = json.load(f_in)
# The API endpoint to communicate with

for new_data in data_in:
# A POST request to the API
    post_response = requests.post(url_post, json=new_data)
    # Print the response
    print(post_response)
```

## Search Service

The search service is an API service that returns semantic and text search results. 
To start the search service 
```
python3 /Users/arunprasad/python-venv/aiwhispr/python/flask-app/searchService.py  -H 127.0.0.1 -P 10002 -C <PATH_TO_CONFIG_FILE>
```

You run a search query, example 
```
curl -sS 'http://127.0.0.1:10002/aiwhispr?query=Top%20TV%20moments%in%20sports&resultformat=json&withtextsearch=Y'
```
The query paramters are 

query=<search_query>
      
resultformat=<json|html>

withtextsearch=<Y|N>  i.e. if Y then include text search results alongwith semantic search results
             

