#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -C <full_path_to_content-site_config_file>"
   echo "    -C Full path the content site confile"
   exit 1 # Exit script after printing help
}

while getopts "C:" opt
do
   case "$opt" in
      C ) configfile="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

if [ -z "$configfile" ] 
then

        if [ -z "${AIWHISPR_HOME}" ] 
        then 
            echo "AIWHISPR_HOME environment variable is not set. So I dont know where searchService.py is installed"
        fi
        if [ -z "${AIWHISPR_LOG_LEVEL}" ] 
        then 
            echo "AIWHISPR_LOG_LEVEL environment variable is not setLogging level default is DEBUG.This means a verbose output"
            echo "AIWHISPR_LOG_LEVEL environment variable  can be set to  DEBUG / INFO / WARNING / ERROR"
        fi

	helpFunction ;

fi

if [ -z "${AIWHISPR_LOG_LEVEL}" ] 
then 
        echo "AIWHISPR_LOG_LEVEL environment variable is not setLogging level default is DEBUG.This means a verbose output"
        echo "AIWHISPR_LOG_LEVEL environment variable  can be set to  DEBUG / INFO / WARNING / ERROR"
fi

if [ -z "${AIWHISPR_HOME}" ] 
then 
   echo "AIWHISPR_HOME environment variable is not set. So I dont know where searchService.py is installed"
else
   python3 ${AIWHISPR_HOME}/python/common-functions/index_content_site.py -C $configfile 
fi

