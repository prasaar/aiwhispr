#!/bin/bash

if [ -z "${AIWHISPR_HOME}" ] 
then 
   echo "AIWHISPR_HOME environment variable is not set. So I dont know where searchService.py is installed"
   exit 1
fi

if [ -z "${AIWHISPR_LOG_LEVEL}" ] 
then 
   echo "AIWHISPR_LOG_LEVEL environment variable is not set"
   exit 1
fi

cd $AIWHISPR_HOME/examples/http

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    MSYS_NT*)   machine=Git;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo ${machine}

if [ "${machine}" = "Mac" ]
then
DYLD_LIBRARY_PATH=/opt/homebrew/lib
export DYLD_LIBRARY_PATH
fi

echo "Start the search service on port 5002"
case "${machine}" in
    Mac) ($AIWHISPR_HOME/shell/start-search-service.sh -H 127.0.0.1 -P 5002 -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.qdrant.cfg &> /tmp/search.example_bbc.filepath.qdrant.log & );;
    *) ($AIWHISPR_HOME/shell/start-search-service.sh -H 127.0.0.1 -P 5002 -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.qdrant.cfg &> /tmp/search.example_bbc.filepath.qdrant.log &);;
esac

ps -ef | grep "start-search-service.sh"

echo
echo "Start the exampleHttpResponder on port 9101"
cd $AIWHISPR_HOME/examples/http
(python3 exampleHttpResponder.py &> /tmp/example_bbc.exampleHttpResponder.log &);
ps -ef | grep "exampleHttpResponder.py"

echo
echo "Start a python HttpServer at port 9100"
cd $AIWHISPR_HOME/examples/http
(python3 -m http.server 9100 &> /tmp/example_bbc.httpServer.log &);
ps -ef | grep 'http.server'
