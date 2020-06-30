import argparse
import os
import sys
import logging

from azure.storage.blob import BlobServiceClient

log_level = logging.INFO
if os.environ.get('RD_JOB_LOGLEVEL') == 'DEBUG':
    log_level = logging.DEBUG

# Create a logger for the 'azure.storage.blob' SDK
logger = logging.getLogger('azure.storage.blob')
logger.setLevel(log_level)

# Configure a console output
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

parser = argparse.ArgumentParser(description='Azure storage LS.')
parser.add_argument('container', help='Azure Container Name')
parser.add_argument('prefix', help='Prefix')
args = parser.parse_args()

account_name = None
access_key = None
prefix = None
blob_path = None

logger.info("")
logger.info("---------------------------")
logger.info("Starting Azure Delete Blob")
logger.info("---------------------------")

if "RD_CONFIG_BLOB_PATH" in os.environ:
    blob_path = os.environ["RD_CONFIG_BLOB_PATH"]

if "RD_CONFIG_ACCOUNT_NAME" in os.environ:
    account_name = os.environ["RD_CONFIG_ACCOUNT_NAME"]
if "RD_CONFIG_ACCESS_KEY" in os.environ:
    access_key = os.environ["RD_CONFIG_ACCESS_KEY"]
if "RD_CONFIG_PREFIX" in os.environ:
    prefix = os.environ["RD_CONFIG_PREFIX"]

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

if not blob_path:
    # removing a list
    if not prefix:
        generator = container_client.list_blobs(logging_enable=True)
    else:
        generator = container_client.list_blobs(name_starts_with=prefix, logging_enable=True)

    for blob in generator:
        blob_client = container_client.get_blob_client(blob.name)
        logger.info("Removing " + blob.name + " from container " + args.container)
        blob_client.delete_blob()
else:
    # removing a file
    blob_client = container_client.get_blob_client(blob_path)

    if blob_client:
        logger.info("Removing " + blob_path + " from container " + args.container)
        blob_client.delete_blob()
    else:
        logger.warning("Blob doesn't exists")
        sys.exit(1)

logger.info('Finish sucessfully')
