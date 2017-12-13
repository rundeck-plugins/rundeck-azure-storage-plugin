import argparse
import os
import subprocess
import sys
import azure.common
from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings
from os import listdir
from os.path import isfile, join
import magic
from urlparse import urlparse
import json

def file_mime_type(file):
    return(magic.from_file(file, mime=True))

def putFile(block_blob_service,container, blob_name, file):
    block_blob_service.create_blob_from_path(
        container,
        blob_name,
        file,
        content_settings=ContentSettings(content_type=file_mime_type(file))
    )

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
parser = argparse.ArgumentParser(description='Azure storage LS.')
parser.add_argument('container', help='Azure Container Name')
parser.add_argument('source', help='the source (LocalPath or AzureUri)')
parser.add_argument('destination', help='the destination (LocalPath or AzureUri)')
args = parser.parse_args()

logs = list()

account_name=None
access_key=None
prefix=None

sourceURI = urlparse(args.source)
destinationURI = urlparse(args.destination)

sourceProtocol=sourceURI.scheme
sourcePath=sourceURI.netloc+sourceURI.path

destinationProtocol=destinationURI.scheme
destinationPath=destinationURI.netloc+destinationURI.path

logs.append( "Source: " + sourceProtocol + " path:" + sourcePath)
logs.append( "Destination " + destinationProtocol + " path:" + destinationPath)

if "RD_CONFIG_ACCOUNT_NAME" in os.environ:
    account_name = os.environ["RD_CONFIG_ACCOUNT_NAME"]
if "RD_CONFIG_ACCESS_KEY" in os.environ:
    access_key = os.environ["RD_CONFIG_ACCESS_KEY"]

block_blob_service = BlockBlobService(account_name=account_name, account_key=access_key)
block_blob_service.create_container(args.container)

#getting files from Azure
if(sourceProtocol == "azure"):
    exist=block_blob_service.exists(args.container,sourcePath)

    if exist:
        #the source is a single file
        logs.append( "Downloading from container " +args.container + ":" +  sourcePath +  " to " + destinationPath)
        block_blob_service.get_blob_to_path(args.container, sourcePath, destinationPath)
    else:
        pathlist = block_blob_service.list_blobs(args.container,sourcePath)

        result = list()
        for blob in pathlist:
            result.append(blob.name)

        if result:
            for blob in result:
                #the source is a list of files
                if os.path.isdir(destinationPath):
                    #downloading files
                    ensure_dir(destinationPath+"/"+blob)
                    logs.append( "Downloading from container " +args.container + ":" +  blob +  " to " + destinationPath+"/"+blob)
                    block_blob_service.get_blob_to_path(args.container, blob, destinationPath+"/"+blob)
                else:
                   print "The source is a azure folder, the detination must be a folder"
                   sys.exit(1) 

        else:
            print "Blob doesn't exists"
            sys.exit(1)
                 

#Sending files to Azure
if(destinationProtocol == "azure"):
    if os.path.isfile(sourcePath):
        logs.append( 'Uploading file  ' + sourcePath + ' to ' + args.container + ":" +  destinationPath)
        putFile(block_blob_service,args.container, destinationPath, sourcePath)

    if os.path.isdir(sourcePath):
        local_file_list = [f for f in listdir(sourcePath) if isfile(join(sourcePath, f))]

        file_num = len(local_file_list)
        for i in range(file_num):
            local_file = join(sourcePath, local_file_list[i])
            blob_name = destinationPath+'/'+local_file_list[i]

            logs.append( 'Uploading file  ' + local_file + ' to ' + args.container + ":" +  blob_name)
            if os.path.isfile(local_file):
                putFile(block_blob_service,args.container, blob_name, local_file)



logs.append( 'Finish sucessfully')

json_response = json.dumps(logs) 
print json_response