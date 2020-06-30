import logging

import argparse
import os
import sys
from azure.storage.blob import BlobServiceClient

from os import listdir
from os.path import isfile, join
from urllib.parse import urlparse
import magic


log_level = logging.INFO
if os.environ.get('RD_JOB_LOGLEVEL') == 'DEBUG':
    log_level = logging.DEBUG

# Create a logger for the 'azure.storage.blob' SDK
logger = logging.getLogger('azure.storage.blob')
logger.setLevel(log_level)

# Configure a console output
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def file_mime_type(file):
    return (magic.from_file(file, mime=True))


def putFile(blob_name, file):
    blob_client = container_client.get_blob_client(blob_name)

    with open(file, "rb") as data:
        blob_client.upload_blob(data, blob_type="BlockBlob", overwrite=True)


def downloadFile (blob_name, file):
    blob_client = container_client.get_blob_client(blob_name)

    os.makedirs(os.path.dirname(file), exist_ok=True)

    with open(file, "wb") as my_blob:
        download_stream = blob_client.download_blob(logging_enable=True)
        my_blob.write(download_stream.readall())


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def exists(block_blob_service, container):
    list = block_blob_service.list_containers(name_starts_with=container)
    if list != None:
        return list[0]



parser = argparse.ArgumentParser(description='Azure storage LS.')
parser.add_argument('container', help='Azure Container Name')
parser.add_argument('source', help='the source (LocalPath or AzureUri)')
parser.add_argument('destination', help='the destination (LocalPath or AzureUri)')
args = parser.parse_args()

logs = list()

logger.info("")
logger.info("---------------------------")
logger.info("Starting Azure Copy")
logger.info("---------------------------")

account_name = None
access_key = None
prefix = None

sourceURI = urlparse(args.source)
destinationURI = urlparse(args.destination)

sourceProtocol = sourceURI.scheme
sourcePath = sourceURI.netloc + sourceURI.path

destinationProtocol = destinationURI.scheme
destinationPath = destinationURI.netloc + destinationURI.path

logger.info("Source: " + sourceProtocol + " path:" + sourcePath)
logger.info("Destination " + destinationProtocol + " path:" + destinationPath)
logger.info("")

protocol = "https"

if "RD_CONFIG_ACCOUNT_NAME" in os.environ:
    account_name = os.environ["RD_CONFIG_ACCOUNT_NAME"]
if "RD_CONFIG_ACCESS_KEY" in os.environ:
    access_key = os.environ["RD_CONFIG_ACCESS_KEY"]
if "RD_CONFIG_PROTOCOL" in os.environ:
    protocol = os.environ["RD_CONFIG_PROTOCOL"]

connection_string = "DefaultEndpointsProtocol={};AccountName={};AccountKey={};EndpointSuffix=core.windows.net".format(
    protocol, account_name, access_key)
blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string, logging_enable=True)

container_client = blob_service_client.get_container_client(args.container)

try:
    container_client.create_container()
except:
    logger.info("Container exists")
    logger.info("")

# getting files from Azure
if sourceProtocol == "azure":
    blob_client = container_client.get_blob_client(sourcePath)

    try:
        exist = blob_client.get_blob_properties()
    except:
        exist = False

    if exist:
        # the source is a single file
        logger.info("Downloading from container " + args.container + ":" + sourcePath + " to " + destinationPath)

        downloadFile(sourcePath, destinationPath)
        #blob_service_client.get_blob_to_path(args.container, sourcePath, destinationPath)
    else:

        pathlist = container_client.list_blobs(name_starts_with=sourcePath, logging_enable=True)
        result = list()
        for blob in pathlist:
            result.append(blob.name)

        if result:
            for blob in result:
                # the source is a list of files
                if os.path.isdir(destinationPath):
                    # downloading files
                    ensure_dir(destinationPath + "/" + blob)
                    logger.info( "Downloading from container " + args.container + ":" + blob + " to " + destinationPath + "/" + blob)
                    downloadFile(blob, destinationPath + "/" + blob)
                else:
                    print("The source is a azure folder, the detination must be a folder")
                    sys.exit(1)

        else:
            print("Blob doesn't exists")
            sys.exit(1)

# Sending files to Azure
if (destinationProtocol == "azure"):

    if os.path.isfile(sourcePath):
        logger.info('Uploading file  ' + sourcePath + ' to ' + args.container + ":" + destinationPath)
        putFile(destinationPath, sourcePath)

    if os.path.isdir(sourcePath):
        local_file_list = [f for f in listdir(sourcePath) if isfile(join(sourcePath, f))]

        file_num = len(local_file_list)
        for i in range(file_num):
            local_file = join(sourcePath, local_file_list[i])
            blob_name = destinationPath + '/' + local_file_list[i]

            logger.info('Uploading file  ' + local_file + ' to ' + args.container + ":" + blob_name)
            if os.path.isfile(local_file):
                putFile( blob_name, local_file)

logger.info('Finish successfully')
logger.info("")
