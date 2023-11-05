This directory contains a sample file(nike_data.json) that has scraped data from Nike
The data is in json format which is used to run the pipeline with an indexing service.

Python script load_json.py reads the sample data file and does a POST request to
the indexing service URL specified in the url_post variable. 

You can start the indexing service 

```
python3 $AIWHISPR_HOME/python/flask-app/indexingService.py -C <PATH_TO_INDEX_SERVICE_CONFIG_FILE> -H 127.0.0.1 -P 10001
```

then run 

```
cd $AIWHISPR_HOME/examples/index-service
./load_json.py
```

