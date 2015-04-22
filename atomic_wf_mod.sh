#!/bin/bash

# $1 == URL (https://restapi.ultradns.com)
# $2 == username
# $3 == password
# $4 == zone name
# $5 == host
# $6 == request to
# $7 == redirect to
# $8 == default forward type

resp=`curl -s -H "Content-Type: application/x-www-form-urlencoded" --data "grant_type=password&username=$2&password=$3" $1/v1/authorization/token`
token=`echo $resp | grep -o "\"accessToken\":\".*\"\,"| grep -o ":\".*\"," | grep -oEi "[a-zA-Z0-9]+"`
echo "Extracted: $token"
if [ -z $token ]
  then
    echo "FAIL auth"
    exit
fi

resp=`curl -s -H "Authorization: Bearer $token" -H "Content-Type: application/json" -X POST -d "[{\"method\": \"DELETE\", \"uri\":\"/v1/zones/$4/rrsets/A/$5\"},{\"method\": \"POST\", \"uri\":\"/v1/zones/$4/webforwards\", \"body\":{\"requestTo\":\"$6\", \"defaultRedirectTo\": \"$7\", \"defaultForwardType\": \"$8\"}}]" $1/v1/batch`
echo $resp
if [ -z "$resp" ]
    then
        echo "FAIL rrset to web forward update for $5"
        exit
fi