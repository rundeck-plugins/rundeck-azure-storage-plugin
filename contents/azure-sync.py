import hashlib
import magic
from urllib.parse import urlparse
import argparse
import os
from azure.storage.blob import BlobServiceClient
import sys
from os import listdir
from os.path import isfile, join
import ntpath
import logging

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


def downloadFile(blob_name, file):
    blob_client = container_client.get_blob_client(blob_name)

    os.makedirs(os.path.dirname(file), exist_ok=True)

    with open(file, "wb") as my_blob:
        download_stream = blob_client.download_blob(logging_enable=True)
        my_blob.write(download_stream.readall())


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def md5_for_file(f, block_size=2 ** 20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest()[:-1]


def get_files_from_folder(path):
    file_list = {}
    if os.path.isdir(path):
        local_file_list = [f for f in listdir(path) if isfile(join(path, f))]

        file_num = len(local_file_list)
        for i in range(file_num):
            local_file = join(path, local_file_list[i])
            content_md5 = md5_for_file(open(local_file, 'rb'))

            file_list[ntpath.basename(local_file)] = content_md5
    return file_list


def get_blobs_from_container(prefix):
    azure_blob_list = {}

    generator = container_client.list_blobs(name_starts_with=prefix, logging_enable=True)

    for blob in generator:
        azure_blob_list[ntpath.basename(blob.name)] = bytes(blob.content_settings.content_md5)

    return azure_blob_list


def put(protocol, sourcePath, destinationPath):
    if (protocol == "azure"):
        putFile(destinationPath, sourcePath)
    else:
        downloadFile(sourcePath, destinationPath)


def remove(protocol, path):
    if protocol == "azure":
        blob_client = container_client.get_blob_client(path)
        logger.info("Removing " + path + " from container " + args.container)
        blob_client.delete_blob()
    else:
        # if the destination if the local folder, download the file
        os.remove(path)


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


parser = argparse.ArgumentParser(description='Azure storage LS.')
parser.add_argument('container', help='Azure Container Name')
parser.add_argument('source', help='the source (LocalPath or AzureUri)')
parser.add_argument('destination', help='the destination (LocalPath or AzureUri)')
args = parser.parse_args()

logger.info("")
logger.info("---------------------------")
logger.info("Starting Azure Sync")
logger.info("---------------------------")

logs = list()

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

protocolConnection = "https"

if "RD_CONFIG_ACCOUNT_NAME" in os.environ:
    account_name = os.environ["RD_CONFIG_ACCOUNT_NAME"]
if "RD_CONFIG_ACCESS_KEY" in os.environ:
    access_key = os.environ["RD_CONFIG_ACCESS_KEY"]
if "RD_CONFIG_PROTOCOL" in os.environ:
    protocolConnection = os.environ["RD_CONFIG_PROTOCOL"]

connection_string = "DefaultEndpointsProtocol={};AccountName={};AccountKey={};EndpointSuffix=core.windows.net".format(
    protocolConnection, account_name, access_key)
blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string, logging_enable=True)

container_client = blob_service_client.get_container_client(args.container)

try:
    container_client.create_container()
except:
    logger.info("Container exists")
    logger.info("")

if sourceProtocol == "azure":
    source_list = get_blobs_from_container(sourcePath)
else:
    source_list = get_files_from_folder(sourcePath)

if destinationProtocol == "azure":
    destination_list = get_blobs_from_container(destinationPath)
else:
    destination_list = get_files_from_folder(destinationPath)

logger.debug(source_list)
logger.debug(destination_list)


difference = DictDiffer(source_list, destination_list)
logger.info("Changed: {}".format(difference.changed()))
logger.info("Added: {}".format(difference.added()))
logger.info("Removed: {}".format(difference.removed()))

logger.info("------------------------------------")

if len(difference.changed()) == 0 and len(difference.added()) == 0 and len(difference.removed()) == 0:
    logger.info("Folders are synchronized")

for key in source_list:

    sourceFile = sourcePath + "/" + key
    destinationFile = destinationPath + "/" + key

    if key in difference.changed():
        logger.info(key + " need to be update, sending " + sourceFile + " to " + destinationFile)

        put(destinationProtocol, sourceFile, destinationFile)
    if key in difference.added():
        logger.info(key + " need to be added: , sending " + sourceFile + " to " + destinationFile)

        put(destinationProtocol, sourceFile, destinationFile)

for key in destination_list:
    destinationFile = destinationPath + "/" + key

    if key in difference.removed():
        logger.info( key + " deleting file: " + destinationFile)
        remove(destinationProtocol, destinationFile)
