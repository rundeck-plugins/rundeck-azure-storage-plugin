## Rundeck Azure Storage Plugin

This python plugin provides a connection with Azure Storage to list/get/put Azure blobs and synchronize folders from a storage account.


## Install

Build with `./gradlew build` and copy the `build/lib/azure-storage-remote-plugin-X.X.X.zip` to `$RDECK_BASE/libext` folder

## Requirements

The plugin is written in python and requires `azure-storage-blob` and `python-magic` modules to be installed on the Rundeck server or remote nodes (depending where the Rundeck jobs will be executed)

The modules can be installed with the following command:

```
pip install python-magic
pip install azure-storage-blob
```

## List commands

### Remote commands (can run on remote nodes)
* **Azure / Storage / Remote Copy**: Copies a remote file or Azure Storage Object to another location or in Azure Storage. To reference an Azure container use the following URI pattern:  `azure://path` or `azure://path/file.ext`

* **Azure / Storage / Remote Syncs**: Syncs directories with Azure Storage. . To reference an Azure container use the following URI pattern:  `azure://path` or `azure://path/file.ext`

### Local commands (commands that only runs on the Rundeck server)
* **Azure / Storage / List Blobs**: List Azure Storage blobs and common prefixes under a prefix or all Azure Storage.
* **Azure / Storage / Remove Blobs**: Deletes an Azure Storage blob from a container

## Troubleshooting

If you get an authentication error on remote nodes, make sure that you add the following entry on `/etc/ssh/sshd_config` in order to pass the RD_* variables from Rundeck server to the remote nodes:

```
AcceptEnv RD_*
```