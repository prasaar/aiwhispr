#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -C <full_path_to_content-site_config_file> -H<Machine Interface IP Address to which start service will bind> -P<service port number>"
   echo "    -C Full path the content site confile"
   echo "    -H IP Address on the current machine to which searchService will bind"
   echo "    -P Port number at which the search service will listen"
   exit 1 # Exit script after printing help
}

while getopts "C:H:P:" opt
do
   case "$opt" in
      C ) configfile="$OPTARG" ;;
      H ) servicehostip="$OPTARG" ;;
      P ) serviceportnumber="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

if [ -z $servicehostip ]
then
   servicehostip='127.0.0.1'
fi

if [ -z "$configfile" ] || [ -z "$serviceportnumber" ]
then
	helpFunction ;

        if [ -z "${AIWHISPR_HOME}" ] 
        then 
            echo "AIWHISPR_HOME environment variable is not set. So I dont know where searchService.py is installed"
        fi

fi

if [ -z "${AIWHISPR_HOME}" ] 
then 
   echo "AIWHISPR_HOME environment variable is not set. So I dont know where searchService.py is installed"
else
   python3 ${AIWHISPR_HOME}/python/flask-app/searchService.py -C $configfile -P $serviceportnumber -H $servicehostip
fi

