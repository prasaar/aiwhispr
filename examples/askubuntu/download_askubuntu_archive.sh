#!/bin/bash

if [ -z "${AIWHISPR_HOME}" ]
then
   echo "AIWHISPR_HOME environment variable is not set. So I dont know  where I should store the config file"
   echo "please set this environment variable, it is usually the full path to the aiwhispr directory"
   exit 1
fi

ARCHIVEURL="https://archive.org/download/stack-exchange-data-dump-2023-03-08/askubuntu.com.7z" 
ARCHIVE7Z="askubuntu.com.7z" 

cd  "${AIWHISPR_HOME}"/examples/askubuntu
wget "$ARCHIVEURL" 

7za e $ARCHIVE7Z
