import hashlib
import magic
from urlparse import urlparse
import json
import argparse
import os
from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings
from os import listdir
from os.path import isfile, join
import ntpath

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



def md5_for_file(f, block_size=2**20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest().encode('base64')[:-1] 

def get_files_from_folder(path):
    file_list = {}
    if os.path.isdir(path):
        local_file_list = [f for f in listdir(path) if isfile(join(path, f))]

        file_num = len(local_file_list)
        for i in range(file_num):
            local_file = join(path, local_file_list[i])
            content_md5 = md5_for_file(open(local_file, 'rb'))

            file_list[ntpath.basename(local_file)]=content_md5
    return  file_list 

def get_blobs_from_container(container, prefix):
    azure_blob_list = {}

    generator = block_blob_service.list_blobs(container,prefix=prefix)

    for blob in generator:
        azure_blob_list[ntpath.basename(blob.name)]=blob.properties.content_settings.content_md5

    return azure_blob_list

def put(protocol,block_blob_service,container,sourcePath,destinationPath):
    if(protocol == "azure"):
        block_blob_service.create_blob_from_path(
            container,
            destinationPath,
            sourcePath,
            content_settings=ContentSettings(content_type=file_mime_type(sourcePath))
        )

    else:
        #if the destination if the local folder, download the file
        block_blob_service.get_blob_to_path(container, sourcePath, destinationPath)
    
def remove(protocol,block_blob_service,container,path):
    if(protocol == "azure"):
        block_blob_service.delete_blob(container,path)
    else:
        #if the destination if the local folder, download the file
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

if(sourceProtocol == "azure"):
    source_list = get_blobs_from_container(args.container,sourcePath)
else:
    source_list = get_files_from_folder(sourcePath)
    
if(destinationProtocol == "azure"):
    destination_list = get_blobs_from_container(args.container,destinationPath)
else:
    destination_list = get_files_from_folder(destinationPath)
    

difference = DictDiffer(source_list, destination_list)
print "Changed:", difference.changed()
print "Added:", difference.added()
print "Removed:", difference.removed()
#print "Unchanged:", difference.unchanged()

print "------------------------------------"

if len(difference.changed())==0 and len(difference.added())==0 and  len(difference.removed())==0:
    print "Folders are sincorinized"

for key in source_list:

    sourceFile=sourcePath+"/"+key
    destinationFile=destinationPath+"/"+key

    if key in difference.changed():
        print key +" need to be update, sending "+ sourceFile +" to " + destinationFile
        put(destinationProtocol,block_blob_service,args.container,sourceFile,destinationFile)
    if key in difference.added():
        print key +" need to be added: , sending "+ sourceFile +" to " + destinationFile
        put(destinationProtocol,block_blob_service,args.container,sourceFile,destinationFile)


for key in destination_list:    
    destinationFile=destinationPath+"/"+key

    if key in difference.removed():
        print key +" deleting file: "+ destinationFile
        remove(destinationProtocol,block_blob_service,args.container,destinationFile)
