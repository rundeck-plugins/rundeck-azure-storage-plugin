## Rundeck Azure Storage Plugin

This Python plugin provides a connection with Azure Storage to list/get/put Azure blobs and synchronize folders from a storage account.

## Build Requirements

- Java 8+ (for building the plugin)
- Gradle 8.10.2+ (included via Gradle wrapper)

## Installation

1. **Build the plugin:**
   ```bash
   ./gradlew clean build
   ```

2. **Install the plugin:**
   Copy the `build/libs/rundeck-azure-storage-plugin-X.X.X.zip` to `$RDECK_BASE/libext` folder

3. **Restart Rundeck** to load the new plugin

## Runtime Requirements

The plugin is written in Python and requires the following modules to be installed on the Rundeck server or remote nodes (depending on where the Rundeck jobs will be executed):

```bash
# Install required Python packages (recommended: use requirements.txt)
pip install -r requirements.txt

# Or install individually:
# pip install python-magic azure-storage-blob aiohttp
```

**Security Note:** It's strongly recommended to use a virtual environment for Python dependencies to avoid conflicts and security issues:

```bash
# Using virtual environment (recommended)
python -m venv rundeck-azure-env
source rundeck-azure-env/bin/activate  # On Windows: rundeck-azure-env\Scripts\activate
pip install -r requirements.txt
```

## Available Commands

### Remote Commands (can run on remote nodes)

* **Azure / Storage / Remote Copy**: Copies a remote file or Azure Storage Object to another location or in Azure Storage. To reference an Azure container use the following URI pattern: `azure://path` or `azure://path/file.ext`

* **Azure / Storage / Remote Sync**: Synchronizes directories with Azure Storage. To reference an Azure container use the following URI pattern: `azure://path` or `azure://path/file.ext`

### Local Commands (run only on the Rundeck server)

* **Azure / Storage / List Blobs**: List Azure Storage blobs and common prefixes under a prefix or all Azure Storage
* **Azure / Storage / Remove Blobs**: Deletes an Azure Storage blob from a container

## Configuration

The plugin requires Azure Storage account credentials. These can be provided through:

1. **Environment variables** (recommended for security):
   - `AZURE_STORAGE_ACCOUNT_NAME`
   - `AZURE_STORAGE_ACCOUNT_KEY` or `AZURE_STORAGE_CONNECTION_STRING`

2. **Rundeck job configuration** (less secure, credentials visible in job definitions)

## Security Considerations

- **Credentials**: Never store Azure Storage credentials in plain text. Use Rundeck's Key Storage facility or environment variables
- **Network**: Use HTTPS protocol (default) for all Azure Storage communications
- **Access Control**: Limit Azure Storage account permissions to only what's necessary for your use case
- **Audit**: Enable Azure Storage logging to track access and operations

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/rundeck-plugins/rundeck-azure-storage-plugin.git
cd rundeck-azure-storage-plugin

# Build the plugin
./gradlew clean build

# The plugin zip will be created in build/libs/
```

### Running Tests

```bash
./gradlew test
```

## Troubleshooting

### Authentication Issues on Remote Nodes

If you get authentication errors on remote nodes, add the following entry to `/etc/ssh/sshd_config` to pass RD_* variables from the Rundeck server to remote nodes:

```
AcceptEnv RD_*
```

Then restart the SSH daemon:
```bash
sudo systemctl restart sshd
```

### Python Module Issues

If you encounter Python module import errors:

1. Verify Python modules are installed in the correct environment
2. Check Python path and virtual environment activation
3. Ensure compatible versions of azure-storage-blob and dependencies

### Build Issues

If the build fails:

1. Ensure Java 8+ is installed: `java -version`
2. Try cleaning and rebuilding: `./gradlew clean build`
3. Check for proper file permissions on gradlew: `chmod +x gradlew`

## License

This project is licensed under the Apache License 2.0 - see the plugin.yaml file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

Please ensure your code follows security best practices and passes all tests before submitting.