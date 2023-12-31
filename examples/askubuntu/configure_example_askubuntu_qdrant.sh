#!/bin/bash

if [ -z "${AIWHISPR_HOME}" ] 
then 
   echo "AIWHISPR_HOME environment variable is not set. So I dont know  where I should store the config file"
   echo "please set this environment variable, it is usually the full path to the aiwhispr directory" 
   exit 1
fi

if [ -z "${AIWHISPR_LOG_LEVEL}" ] 
then 
   echo "AIWHISPR_LOG_LEVEL environment variable is not set"
   exit 1
fi

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    MSYS_NT*)   machine=Git;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo "Identified machine OS as  ${machine}"

vectordbApiAddress=localhost
vectordbApiPort=6333
vectordbKey=

configFile="${AIWHISPR_HOME}"/config/content-site/sites-available/example_askubuntu.xml.qdrant.cfg
if [ -f "${configFile}" ]; then  
echo "A config file already exists at ${configFile}"
echo "Do you want to continue?[Y/N] (capital characters only)"
read continueFlag
if [ $continueFlag != "Y" ]
then
exit 1;
fi
fi  

echo "Rewriting existing config file"
tmpConfigFile="/tmp/example_askubuntu.xml.qdrant.cfg.tmp"

echo 
echo "#### Review the path which contains the files your want to index ####"
echo 

srcpath=${AIWHISPR_HOME}/examples/askubuntu/Posts.xml
echo "srcpath="$srcpath
echo "Do you want to change this [Y/N]" 
read changeFlag
if [ "${changeFlag}" = "Y" ]
then
echo
echo "Enter new srcpath. It should not have spaces, the only special character allowed is '.'"
read srcpath
echo "Using srcpath="$srcpath
fi

echo "#### Review the vector database connection config ####"
echo 

echo "api-address="$vectordbApiAddress
echo "Do you want to change this [Y/N]" 
read changeFlag
if [ "${changeFlag}" = "Y" ]
then
echo
echo "Enter new api-address"
read vectordbApiAddress
echo "Using api-key="$vectordbApiAddress
fi
echo

echo "api-port="$vectordbApiPort
echo "Do you want to change this [Y/N]" 
read changeFlag
if [ "${changeFlag}" = "Y" ]
then
echo
echo "Enter new api-port"
read vectordbApiPort
echo "Using api-port="$vectordbApiPort
fi
echo

echo "api-key="$vectordbKey
echo "Do you want to change this [Y/N]" 
read changeFlag
if [ "${changeFlag}" = "Y" ]
then
echo
echo "Enter new api-key. "
read vectordbKey
echo "Using api-key="$vectordbKey
fi
echo

workingDir="${AIWHISPR_HOME}"/examples/askubuntu/working-dir
echo "Current  working-dir="$workingDir
echo "Do you want to change this [Y/N]" 
read changeFlag
if [ "${changeFlag}" = "Y" ]
then
echo
echo "Enter new working-dir. It should be a full path to a directory"
read workingDir
echo "Using working-dir="$workingDir
if [ -d "${workingDir}" ]
then
echo "Checked directory exists. Please ensure that read/ write permissions are set"
else
echo "Directory does not exist. Exiting...."
exit 1
fi
echo
fi

indexDir="${AIWHISPR_HOME}"/examples/askubuntu/index-dir
echo "Current  index-dir="$indexDir
echo "Do you want to change this [Y/N]" 
read changeFlag
if [ "${changeFlag}" = "Y" ]
then
echo
echo "Enter new index-dir. It should be a full path to a directory"
read indexDir
echo "Using index-dir="$indexDir
if [ -d "${indexDir}" ]
then
echo "Checked directory exists. Please ensure that read/ write permissions are set"
else
echo "Directory does not exist. Exiting...."
exit 1
fi
echo
fi


echo
echo
echo "Now creating a temporary config file in "$tmpConfigFile
echo "[content-site]" > $tmpConfigFile
echo "sitename=example_askubuntu.xml.qdrant" >> $tmpConfigFile
echo "srctype=filepath" >> $tmpConfigFile
echo "srcpath="$srcpath >> $tmpConfigFile
echo "displaypath=http://askubuntu.com/questions" >> $tmpConfigFile
echo "contentSiteModule=stackexchangeContentSite" >> $tmpConfigFile

echo "[content-site-auth]" >> $tmpConfigFile
echo "authtype=filechecks" >> $tmpConfigFile
echo "check-file-permission=Y" >> $tmpConfigFile

echo "[vectordb]" >> $tmpConfigFile
echo "vectorDbModule=qdrantVectorDb" >> $tmpConfigFile
echo "api-address="$vectordbApiAddress >> $tmpConfigFile
echo "api-port="$vectordbApiPort >> $tmpConfigFile
echo "api-key="$vectordbKey >> $tmpConfigFile

echo "[local]" >> $tmpConfigFile
echo "working-dir="$workingDir >> $tmpConfigFile
echo "index-dir="$indexDir >> $tmpConfigFile

echo "[llm-service]" >> $tmpConfigFile
echo "model-family=sbert" >> $tmpConfigFile
echo "model-name=all-mpnet-base-v2" >> $tmpConfigFile
echo "llm-service-api-key=" >> $tmpConfigFile
echo "llmServiceModule=libSbertLlmService" >> $tmpConfigFile


echo
echo
echo "#### CONFIG FILE ####"
cat $tmpConfigFile
echo "#Copying the new config file#"
cp  $tmpConfigFile $configFile
