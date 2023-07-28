#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -k TypesenseAdminKey -h TypesenseHost -p TypesensePort "
   echo -e "\t-k Provide the TypesenseAdminKey"
   echo -e "\t-h IP Address of the Typesense Server"
   echo -e "\t-p Port number of the typesense server"
   exit 1 # Exit script after printing help
}

while getopts "k:h:p:" opt
do
   case "$opt" in
      k ) key="$OPTARG" ;;
      h ) hostname="$OPTARG" ;;
      p ) portnumber="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$key" ] || [ -z "$hostname" ] || [ -z "$portnumber" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

# Begin script in case all parameters are correct
echo "$key"
echo "$hostname"
echo "$portnumber"

curl -H X-TYPESENSE-API-KEY:"$key" -X POST http://"$hostname":"$portnumber"/operations/db/compact
