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

echo "Start the search service"
case "${machine}" in
    Mac) (nohup $AIWHISPR_HOME/shell/start-search-service.sh -H 127.0.0.1 -P 5002 -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.macos.cfg &> /tmp/example_bbc.searchservice.log &; echo $!);;
    *) (nohup $AIWHISPR_HOME/shell/start-search-service.sh -H 127.0.0.1 -P 5002 -C $AIWHISPR_HOME/config/content-site/sites-available/example_bbc.filepath.cfg &> /tmp/example_bbc.searchservice.log &;echo $!);;
esac

echo
echo "Start the exampleHttpResponder"
cd $AIWHISPR_HOME/examples/http
(python3 exampleHttpResponder.py &> /tmp/example_bbc.exampleHttpResponder.log &; echo $!);

echo
echo "Start a python HttpServer at port 9000"
cd $AIWHISPR_HOME/examples/http
(python3 -m http.server 9000 &> /tmp/example_bbc.httpServer.log &; echo $!);
