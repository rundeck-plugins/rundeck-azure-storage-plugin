import argparse
import os
import json
import logging
import sys

from azure.storage.blob import ContainerClient

log_level = 'INFO'
if os.environ.get('RD_JOB_LOGLEVEL') == 'DEBUG':
    log_level = 'DEBUG'
else:
    log_level = 'ERROR'

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
protocol = "https"

if "RD_CONFIG_ACCOUNT_NAME" in os.environ:
    account_name = os.environ["RD_CONFIG_ACCOUNT_NAME"]
if "RD_CONFIG_ACCESS_KEY" in os.environ:
    access_key = os.environ["RD_CONFIG_ACCESS_KEY"]
if "RD_CONFIG_PREFIX" in os.environ:
    prefix = os.environ["RD_CONFIG_PREFIX"]
if "RD_CONFIG_PROTOCOL" in os.environ:
    protocol = os.environ["RD_CONFIG_PROTOCOL"]

connection_string = "DefaultEndpointsProtocol={};AccountName={};AccountKey={};EndpointSuffix=core.windows.net".format(
    protocol, account_name, access_key)

generator = ContainerClient.from_connection_string(conn_str=connection_string,
                                                   container_name=args.container,
                                                   logging_enable=True)

if not prefix:
    blob_list = generator.list_blobs()
else:
    blob_list = generator.list_blobs(name_starts_with=prefix)

result = list()

for blob in blob_list:
    result.append({'name': blob.name,
                   'last_modified': blob.last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                   'content_length': blob.size,
                   'blob_type': blob.blob_type.name,
                   'content_type': blob.content_settings.content_type,
                   'etag': blob.etag
                   })

json_response = json.dumps(result)
print(json_response)
