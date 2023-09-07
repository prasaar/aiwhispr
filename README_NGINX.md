# AIWhispr

## Overview
AIWhispr is a no/low-code tool to enable AI powered semantic search. 
- It is easy to install.
- Simple to configure.
- Delivers fast semantic response to search queries.
- Can handle multiple file formats (txt,csv, pdf, docx,pptx, docx) stored on AWS S3, Azure Blob Containers,Google Cloud Storage, local directory path.
- Supports multiple vector databases (Qdrant,Weaviate,Typesense) 

![Alt Text](./resources/aiwhispr-example.gif)

## Contact
contact@aiwhispr.com

## Prerequisites for a Linux install with Nginx

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
AIWhispr package comes with sample data, nginx configuration, index.html for nginx setup , python (flask) script to help you get started.

**1. Setup the example content(files) that you want to index and search**

In this example the content files you want to index are setup under /var/www/html(nginx webserver root). 

Copy the sample data under webserver root
```
cp -R $AIWHISPR_HOME/examples/data/bbc /var/www/html/
```

**2. Configuration file**

A configuration file is maintained under $AIWHISPR_HOME/config/content-site/sites-available directory. 

You can create 

$AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.cfg 

The sections you have to edit typically include 

[vectordb] to add the typesense api-address, api-port, api-key

[content-site] - if your nginx webserver root is different from /var/www/html ; - if your webserver is internet facing you have to provide the hostname for the displaypath configuration instead of 127.0.0.1

For more details about sections in the config file please refer to [CONFIG_FILE.md](./CONFIG_FILE.md)

A typical configuration file would look like
```
[content-site]
sitename=example_bbc.filepath
srctype=filepath
#Assuming that you have copied the $AIWHISPR_HOME/examples/bbc under your Webserver's root directory
srcpath=/var/www/html/bbc
#Remember to change the hostname if it's internet facing
displaypath=http://127.0.0.1/bbc
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
##Remember to change them from /tmp to a separate folder you have created for aiwhispr indexing 
working-dir=/tmp
index-dir=/tmp
[llm-service]
model-family=sbert
model-name=all-mpnet-base-v2
llm-service-api-key=
llmServiceModule=libSbertLlmService
```

**3. Start Indexing**
Confirm that the environment variables AIWHISPR_HOME and AIWHISPR_LOG_LEVEL are set and exported. 

Set AIWHISPR_LOG_LEVEL=DEBUG 


Index the file content for semantic search.

The logs are redirected to /tmp/aiwhispr_index_job.log

This job takes some time because it ,sets up the LLM, has to index, create vector embeddings for over 2000 files.
```
echo $AIWHISPR_HOME
echo $AIWHISPR_LOG_LEVEL
$AIWHISPR_HOME/shell/start-indexing-content-site.sh -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.cfg &>> /tmp/aiwhispr_index_job.log
```
**4. Configure nginx, html files, web service gateways**

###  Nginx config
$AIWHISPR_HOME/examples/nginx/aiwhispr-search.nginx.conf is an example of a typical nginx configuration.

Copy this file to /etc/nginx/sites-available.
```
cp $AIWHISPR_HOME/examples/nginx/aiwhispr-search.nginx.conf /etc/nginx/sites-available/
```
Edit the server_name configuration to reflect your host ip (e.g. 127.0.0.1) /host domain name for internet facing server

Add index.html as first option under index configuration

Add the location configurations

```
server {
    listen 80;
    #server_name domain.com www.domain.com;
    server_name 127.0.0.1 ;

    root /var/www/html;

    # Add index.html 
    index index.html index.htm index.nginx-debian.html;

    server_name _;

    #location configurations
    location / {
        # First attempt to serve request as file, then
        # as directory, then fall back to displaying a 404.
          try_files $uri $uri/ =404;
     }

    #Route http://<domain>/search  through UWSGI to flash app
    location /search {
        uwsgi_read_timeout 600s;
        uwsgi_send_timeout 600s;
        include uwsgi_params;
        uwsgi_pass unix:/tmp/aiwhispr.sock;
    }
}
```

Create a soft link under /etc/nginx/sites-enabled  and restart your nginx server
```
cd /etc/nginx/sites-enabled
ln -s /etc/nginx/sites-available/aiwhispr-search.nginx.conf  ./aiwhispr-search.nginx.conf
sudo systemctl restart nginx
```

### HTML File (index.html)
**(Please take a backup of your existing index.html file)**
Copy the examples/index.html to Webserver root /var/www/html
```
cp $AIWHISPR_HOME/examples/nginx/index.html  /var/www/html/ 

```
Edit index.html, replace your_domain with your server IP/hostname
```
 <form action = "http://127.0.0.1/search" method = "post">
``` 

Restart nginx
```
sudo systemctl restart nginx
```

Please note that your browser may have cached the original nginx results locally.
You can test if the new index.html is served by nginx using curl
Example:
```
curl http://127.0.0.1
```
It should return
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="theme-color" content="#000000">
    <title>AIWhispr</title>
</head>
<body>
<header class="header" style="margin:0px;background-image: linear-gradient(284deg, #fedd4e, #fcb43a);color:#fff;display:flex;flex-direction:column;align-items: center;min-height:200px">
        <h1 class="headertitle" style="display:flex;font-size:1.2rem;font-weight:normal;align-items: center; text-align:center" name="AIWhispr Search"> </h1>
    <p class="headersubtitle" style="display:flex;font-size:1.2rem;align-items: center; text-align:center" name="relevance discovered">
      <div style="display:flex;justify-content:center;align-items:center;padding:5px">
        <img src="http://demo.aiwhispr.com/aiwhispr_logo_results.png" height="190px" width=190px"/>
      </div`>
    </p>
</header>
<form action = "http://127.0.0.1/search" method = "post">
......       
......

```

###  Start the AIWhispr search service

Start the AIWhispr search service on port 5002. 

The logs are redirected to /tmp/aiwhispr_search_service.log
```
($AIWHISPR_HOME/shell/start-search-service.sh -H 127.0.0.1 -P 5002 -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.cfg  &>> /tmp/aiwhispr_search_service.log &); exit 0
```

###  Start the webServiceResponder example
Start the example webServiceResponder that responds to search requests from your index.html GET/POST.

If you are running this in a virtualenv then you will have to add --virtualenv /path_to_virtualenv as a uwsgi command line option

The logs are redirected to /tmp/aiwhispr_webServiceResponder.log
```
cd $AIWHISPR_HOME/examples/nginx
uwsgi --ini $AIWHISPR_HOME/examples/nginx/uwsgi_aiwhispr.ini  [--virtualenv /path_to_virtualenv]   &>> /tmp/aiwhispr_webServiceResponder.log &
```

### Ready to go
Try the search on http://<yourdomain/IP Address>

Some examples of meaning drive search queries 

"What are the top TV moments in Olympics"

"Which is the best laptop to buy"

"How is inflation impacting the economy"

You can compare the semantic search results against text search results. 


