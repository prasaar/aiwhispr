#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -Q query -F resultformat  -T textsearchflag -H hostname -P portnumber"
   echo "	-Q Provide the query in url ready format (e.g.space character should be %20)"
   echo "	-F result format json/html"
   echo "	-H hostname on which aiwhispr search service module is running"
   echo "	-P port number on which aiwhispr search service module is running"
   echo "	-T Y/N flag to indicate whether text search should be performed alogwith semantic search"
   exit 1 # Exit script after printing help
}

while getopts "Q:F:H:P:T:" opt
do
   case "$opt" in
      Q ) query="$OPTARG" ;;
      F ) resultformat="$OPTARG" ;;
      T ) withtextsearch="$OPTARG" ;;
      H ) hostname="$OPTARG" ;;
      P ) portnumber="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$query" ] || [ -z "$resultformat" ] || [ -z "$withtextsearch" ] || [ -z "$hostname" ] || [ -z "$portnumber" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

# Begin script in case all parameters are correct
URL=http://"$hostname":"$portnumber"/search?query="$query"'&resultformat='$resultformat'&withtestsearch='$withtextsearch
echo $URL
curl -sS  $URL
