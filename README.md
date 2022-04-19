![logo-enterprise-search](https://user-images.githubusercontent.com/90465691/162754148-00bb1f5f-f814-46ce-a46f-ed8a2e0a0e73.png)

[Elastic Enterprise Search](https://www.elastic.co/guide/en/enterprise-search/current/index.html) | [Elastic Workplace Search](https://www.elastic.co/guide/en/workplace-search/current/index.html)

# Network Drives connector package

Use this _Elastic Enterprise Search Network Drives connector package_ to deploy and run a Network Drive connector on your own infrastructure. The connector extracts and syncs data from Network Drives. The data is indexed into a Workplace Search content source within an Elastic deployment.

⚠️ _This connector package is a **beta** feature._
Beta features are subject to change and are not covered by the support SLA of generally available (GA) features. Elastic plans to promote this feature to GA in a future release.

ℹ️ _This connector package requires a compatible Elastic subscription level._
Refer to the Elastic subscriptions pages for [Elastic Cloud](https://www.elastic.co/subscriptions/cloud) and [self-managed](https://www.elastic.co/subscriptions) deployments.

**Table of contents:**

- [Setup and basic usage](#setup-and-basic-usage)
  - [Gather Network Drives details](#gather-network-drives-details)
  - [Gather Elastic details](#gather-elastic-details)
  - [Create a Workplace Search API key](#create-a-workplace-search-api-key)
  - [Create a Workplace Search content source](#create-a-workplace-search-content-source)
  - [Choose connector infrastructure and satisfy dependencies](#choose-connector-infrastructure-and-satisfy-dependencies)
  - [Install the connector](#install-the-connector)
  - [Configure the connector](#configure-the-connector)
  - [Test the connection](#test-the-connection)
  - [Sync data](#sync-data)
  - [Log errors and exceptions](#log-errors-and-exceptions)
  - [Schedule recurring syncs](#schedule-recurring-syncs)
- [Troubleshooting](#troubleshooting)
  - [Troubleshoot extraction](#troubleshoot-extraction)
- [Advanced usage](#advanced-usage)
  - [Customize extraction and syncing](#customize-extraction-and-syncing)
  - [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)
- [Connector reference](#connector-reference)
  - [Data extraction and syncing](#data-extraction-and-syncing)
  - [Sync operations](#sync-operations)
  - [Command line interface (CLI)](#command-line-interface-cli)
  - [Configuration settings](#configuration-settings)
  - [Enterprise Search compatibility](#enterprise-search-compatibility)
  - [Runtime dependencies](#runtime-dependencies)

## Setup and basic usage

Complete the following steps to deploy and run the connector:

1. [Gather Network Drives details](#gather-network-drives-details)
1. [Gather Elastic details](#gather-elastic-details)
1. [Create a Workplace Search API key](#create-a-workplace-search-api-key)
1. [Create a Workplace Search content source](#create-a-workplace-search-content-source)
1. [Choose connector infrastructure and satisfy dependencies](#choose-connector-infrastructure-and-satisfy-dependencies)
1. [Install the connector](#install-the-connector)
1. [Configure the connector](#configure-the-connector)
1. [Test the connection](#test-the-connection)
1. [Sync data](#sync-data)
1. [Log errors and exceptions](#log-errors-and-exceptions)
1. [Schedule recurring syncs](#schedule-recurring-syncs)

The steps above are relevant to all users. Some users may require additional features. These are covered in the following sections:

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

### Gather Network Drives details

Collect the information that is required to connect to your Network Drives:

- The domain name where the Network Drive is present.
- The Network Drives path the connector will crawl to fetch files.
- The username the connector will use to log in to Network Drives.
- The password the connector will use to log in to Network Drives.
- The server IP address where the Network Drive is hosted.
- The name of the server where the Network Drive is found. (Note that server name may not be the same as the hostname. On Windows, you can get the machine name from the System panel.)
- The client machine name can be a random client name of up to 15 characters.

ℹ️ The user credentials provided for the connector must have at least **read** permissions for the folder path provided.

Later, you will [configure the connector](#configure-the-connector) with these values.

Some connector features require additional details. Review the following documentation if you plan to use these features:

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

### Gather Elastic details

First, ensure your Elastic deployment is [compatible](#enterprise-search-compatibility) with the Network Drives connector package.

Next, determine the [Enterprise Search base URL](https://www.elastic.co/guide/en/enterprise-search/current/endpoints-ref.html#enterprise-search-base-url) for your Elastic deployment.

Later, you will [configure the connector](#configure-the-connector) with this value.

You also need a Workplace Search API key and a Workplace Search content source ID. You will create those in the following sections.

If you plan to use document-level permissions, you will also need user identity information. See [Use document-level permissions (DLP)](#use-document-level-permissions-dlp) for details.

### Create a Workplace Search API key

Each Network Drives connector authorizes its connection to Elastic using a Workplace Search API key.

Create an API key within Kibana. See [Workplace Search API keys](https://www.elastic.co/guide/en/workplace-search/current/workplace-search-api-authentication.html#auth-token).

### Create a Workplace Search content source

Each Network Drives connector syncs data from Network Drives into a Workplace Search content source.

Create a content source within Kibana:

1. Navigate to **Enterprise Search** → **Workplace Search** → **Sources** → **Add Source** → **Custom Content Source**.
2. Name your Content Source, (e.g. Network Drives Connector).
3. Choose **Configure Network Drives Connector**.

Record the ID of the new content source. This value is labeled *Source Identifier* within Kibana. Later, you will [configure the connector](#configure-the-connector) with this value.

**Alternatively**, you can use the connector’s `bootstrap` command to create the content source. See [`bootstrap` command](#bootstrap-command).

### Choose connector infrastructure and satisfy dependencies

After you’ve prepared the two services, you are ready to connect them.

Provision a Windows, MacOS, or Linux server for your Network Drives connectors.

The infrastructure must provide the necessary runtime dependencies. See [Runtime dependencies](#runtime-dependencies).

Clone or copy the contents of this repository to your infrastructure.

### Install the connector

After you’ve provisioned infrastructure and copied the package, use the provided `make` target to install the connector:

```shell
make install_package
```

This command runs as the current user and installs the connector and its dependencies.

ℹ️ Within a Windows environment, first install `make`:

```
winget install make
```

Next, ensure the `ees_network_drive` executable is on your `PATH`. For example, on macOS:

```shell
export PATH=/Users/shaybanon/Library/Python/3.8/bin:$PATH
```

The following table provides the installation location for each operating system (note Python version 3.8):

| Operating system | Installation location                                        |
| ---------------- | ------------------------------------------------------------ |
| Linux            | `./local/bin`                                                |
| macOS            | `/Users/<user_name>/Library/Python/3.8/bin`                  |
| Windows          | `\Users\<user_name>\AppData\Roaming\Python\Python38\Scripts` |

### Configure the connector

You must configure the connector to provide the information necessary to communicate with each service. You can provide additional configuration to customize the connector for your needs.

Create a [YAML](https://yaml.org/) configuration file at any pathname. Later, you will include the [`-c` option](#-c-option) when running [commands](#command-line-interface-cli) to specify the pathname to this configuration file.

_Alternatively, in Linux environments only_, locate the default configuration file created during installation. The file is named `network_drives_connector.yml` and is located within the `config` subdirectory where the package files were installed. See [Install the connector](#install-the-connector) for a listing of installation locations by operating system. When you use the default configuration file, you do not need to include the `-c` option when running commands.

After you’ve located or created the configuration file, populate each of the configuration settings. Refer to the [settings reference](#configuration-settings). You must provide a value for all required settings.

Use the additional settings to customize the connection and manage features such as document-level permissions. See:

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

### Test the connection

After you’ve configured the connector, you can test the connection between Elastic and Network Drives. Use the following `make` target to test the connection:

```shell
make test_connectivity
```

### Sync data

After you’ve confirmed the connection between the two services, you are ready to sync data from Network Drives to Elastic.

The following table lists the available [sync operations](#sync-operations), as well as the [commands](#command-line-interface-cli) to perform the operations.

| Operation                             | Command                                         |
| ------------------------------------- | ----------------------------------------------- |
| [Incremental sync](#incremental-sync) | [`incremental-sync`](#incremental-sync-command) |
| [Full sync](#full-sync)               | [`full-sync`](#full-sync-command)               |
| [Deletion sync](#deletion-sync)       | [`deletion-sync`](#deletion-sync-command)      |
| [Permission sync](#permission-sync)   | [`permission-sync`](#permission-sync-command)   |

Begin syncing with an *incremental sync*. This operation begins [extracting and syncing content](#data-extraction-and-syncing) from Network Drives to Elastic. If desired, [customize extraction and syncing](#customize-extraction-and-syncing) for your use case.

Review the additional sync operations to learn about the different types of syncs. Additional configuration is required to use [document-level permissions](#use-document-level-permissions-dlp).

You can use the command line interface to run sync operations on demand, but you will likely want to [schedule recurring syncs](#schedule-recurring-syncs).

### Log errors and exceptions

The various [sync commands](#command-line-interface-cli) write logs to standard output and standard error.

To persist logs, redirect standard output and standard error to a file. For example:

```shell
ees_network_drive -c ~/config.yml incremental-sync >>~/incremental-sync.log 2>&1
```

You can use these log files to implement your own monitoring and alerting solution.

Configure the log level using the [`log_level` setting](#log_level).

### Schedule recurring syncs

Use a job scheduler, such as `cron`, to run the various [sync commands](#command-line-interface-cli) as recurring syncs.

The following is an example crontab file:

```crontab
0 */2 * * * ees_network_drive -c ~/config.yml incremental-sync >>~/incremental-sync.log 2>&1
0 0 */2 * * ees_network_drive -c ~/config.yml full-sync >>~/full-sync.log 2>&1
0 * * * * ees_network_drive -c ~/config.yml deletion-sync >>~/deletion-sync.log 2>&1
*/5 * * * * ees_network_drive -c ~/config.yml permission-sync >>~/permission-sync.log 2>&1
```

This example redirects standard output and standard error to files, as explained here: [Log errors and exceptions](#log-errors-and-exceptions).

Use this example to create your own crontab file. Manually add the file to your crontab using `crontab -e`. Or, if your system supports cron.d, copy or symlink the file into `/etc/cron.d/`.

⚠️ **Note**: It's possible that scheduled jobs may overlap.
To avoid multiple crons running concurrently, you can use [flock](https://manpages.debian.org/testing/util-linux/flock.1.en.html) with cron to manage locks. The `flock` command is part of the `util-linux` package. You can install it with `yum install util-linux`
or `sudo apt-get install -y util-linux`.
Using flock ensures the next scheduled cron runs only after the current one has completed execution. 

Let's consider an example of running incremental-sync as a cron job with flock:

```crontab
0 */2 * * * /usr/bin/flock -w 0 /var/cron.lock ees_network_drive -c ~/config.yml incremental-sync >>~/incremental-sync.log 2>&1
```

## Troubleshooting

To troubleshoot an issue, first view your [logged errors and exceptions](#log-errors-and-exceptions).

Use the following section to help troubleshoot further:

- [Troubleshoot extraction](#troubleshoot-extraction)

If you need assistance, use the Elastic community forums or Elastic support:

- [Enterprise Search community forums](https://discuss.elastic.co/c/enterprise-search/84)
- [Elastic Support](https://support.elastic.co)

### Troubleshoot extraction

The following sections provide solutions for content extraction issues.

#### Issues extracting content from attachments

The connector uses the [Tika module](https://pypi.org/project/tika/) for parsing file contents from attachments. [Tika-python](https://github.com/chrismattmann/tika-python) uses Apache Tika REST server. To use this library, you need to have Java 7+ installed on your system as tika-python starts up the Tika REST server in the background.

At times, the TIKA server fails to start hence content extraction from attachments may fail. To avoid this, make sure Tika is running in the background.

#### Issues extracting content from images

Tika Server also detects contents from images by automatically calling Tesseract OCR. To allow Tika to also extract content from images, you need to make sure tesseract is on your path and then restart tika-server in the background (if it is already running). For example, on a Unix-like system, try:

```shell
ps aux | grep tika | grep server # find PID
kill -9 <PID>
```

To allow Tika to extract content from images, you need to manually install Tesseract OCR.

## Advanced usage

The following sections cover additional features that are not covered by the basic usage described above.

After you’ve set up your first connection, you may want to further customize that connection or scale to multiple connections.

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

## Customize extraction and syncing

The connector will support the following rules for filtering files:

* Size: To filter all files of size **>** x bytes, add `>x` to the `include/exclude` field.
* Path Template: To index files in specific subdirectories or files with specific names/types, use a glob pattern. 

The Path Template can be used for following use cases:

1. Folder: For example `/Engineering/**/*` will filter all the content inside the Engineering folder. 
1. File Name: To filter files containing a given string pattern, use the following glob pattern:

- `**/<filename>.*` : files named `<filename>`.
- `**/main*.*` : filenames that start with the substring `main`.
        
1. File Type: To filter `pdf` media type files, use the glob pattern `**/*.pdf`.

These can be defined under include/exclude parameters.

Finally, you can set custom timestamps to control which objects are synced, based on their created or modified timestamps. [Configure](#configure-the-connector) the following settings:

- [`start_time`](#start_time)
- [`end_time`](#end_time)

### Use document-level permissions (DLP)

Complete the following steps to use document-level permissions:

1. Enable document-level permissions
1. Map user identities
1. Sync document-level permissions data

#### Enable document-level permissions

Within your configuration, enable document-level permissions using the following setting: [`enable_document_permission`](#enable_document_permission).

#### Map user identities

Copy to your server a CSV file that provides the mapping of user identities. The file must follow this format:

- First column: Network Drive user's/group's SID
- Second column: Elastic username

Then, configure the location of the CSV file using the following setting: [`network_drives_enterprise_search_user_mapping`](#network_drives_enterprise_search_user_mapping).

#### Sync document-level permissions data

Sync document-level permissions data from Network Drives to Elastic.

The following sync operations include permissions data:

- [Permission sync](#permission-sync)
- [Incremental sync](#incremental-sync)

Sync this information continually to ensure correct permissions. See [Schedule recurring syncs](#schedule-recurring-syncs).

## Connector reference

The following reference sections provide technical details:

- [Data extraction and syncing](#data-extraction-and-syncing)
- [Sync operations](#sync-operations)
- [Command line interface (CLI)](#command-line-interface-cli)
- [Configuration settings](#configuration-settings)
- [Enterprise Search compatibility](#enterprise-search-compatibility)
- [Runtime dependencies](#runtime-dependencies)

### Data extraction and syncing

Each Network Drives connector extracts and syncs files from Network Drives:

It extracts content from various document formats, and it performs optical character recognition (OCR) to extract content from images.

You can customize extraction and syncing per connector. See [Customize extraction and syncing](#customize-extraction-and-syncing).

### Sync operations

The following sections describe the various operations to [sync data](#sync-data) from Network Drives to Elastic.

#### Incremental sync

Syncs to Enterprise Search all files *created or modified* since the previous incremental sync.

When [using document-level permissions (DLP)](#use-document-level-permissions-dlp), each incremental sync will also perform a [permission sync](#permission-sync).

Perform this operation with the [`incremental-sync` command](#incremental-sync-command).

#### Full sync

Syncs to Enterprise Search all files *created or modified* since the configured [`start_time`](#start_time). Continues until the current time or the configured [`end_time`](#end_time).

Perform this operation with the [`full-sync` command](#full-sync-command).

#### Deletion sync

Deletes from Enterprise Search all files *deleted* since the previous deletion sync.

Perform this operation with the [`deletion-sync` command](#deletion-sync-command).

#### Permission sync

Syncs to Enterprise Search all file document permissions since the previous permission sync.

When [using document-level permissions (DLP)](#use-document-level-permissions-dlp), use this operation to sync all updates to users and groups within Network Drives.

Perform this operation with the [`permission-sync` command](#permission-sync-command).

### Command line interface (CLI)

Each Network Drives connector has the following command line interface (CLI):

```shell
ees_network_drive [-c <pathname>] <command>
```

#### `-c` option

The pathname of the [configuration file](#configure-the-connector) to use for the given command.

```shell
ees_network_drive -c ~/config.yml full-sync
```

#### `bootstrap` command

Creates a Workplace Search content source with the given name. Outputs its ID.

```shell
ees_network_drive bootstrap --name 'Accounting documents' --user 'shay.banon'
```

See also [Create a Workplace Search content source](#create-a-workplace-search-content-source).

To use this command, you must [configure](#configure-the-connector) the following settings:

- [`enterprise_search.host_url`](#enterprise_searchhost_url-required)
- [`workplace_search.api_key`](#workplace_searchapi_key-required)

And you must provide on the command line any of the following arguments that are required:

- `--name` (required): The name of the Workplace Search content source to create.
- `--user` (optional): The username of the Elastic user who will own the content source. If provided, the connector will prompt for a password. If omitted, the connector will use the configured API key to create the content source.

#### `incremental-sync` command

Performs a [incremental sync](#incremental-sync) operation.

#### `full-sync` command

Performs a [full sync](#full-sync) operation.

#### `deletion-sync` command

Performs a [deletion sync](#deletion-sync) operation.

#### `permission-sync` command

Performs a [permission sync](#permission-sync) operation.

### Configuration settings

[Configure](#configure-the-connector) any of the following settings for a connector:

#### `network_drive.domain` (required)

The domain name where your Network Drives is present.

```yaml
network_drive.domain: "Domain3"
```

#### `network_drive.username` (required)

The username of the account for Network Drives. See [Gather Network Drives details](#gather-network-drives-details).

```yaml
network_drive.username: bill.gates
```

#### `network_drive.password` (required)

The password of the account to be used for crawling the Network Drives. See [Gather Network Drives details](#gather-network-drives-details).

```yaml
network_drive.password: 'L,Ct%ddUvNTE5zk;GsDk^2w)(;,!aJ|Ip!?Oi'
```

#### `network_drive.path` (required)

The Network Drives path the connector will crawl to fetch files.

```yaml
network_drive.path: 'path1/drives/org1/ws'
```

#### `network_drive.server_name` (required)

The name of the server where the Network Drive is found. (Note that server name may not be the same as the hostname. On Windows, you can get the machine name from the System panel.)

```yaml
network_drive.server_name: 'elastic'
```

#### `network_drive.server_ip` (required)

The server ip where Network Drives is hosted.

```yaml
network_drive.server_ip: '1.2.3.4'
```

#### `client_machine.name` (required)

The client machine name can be a random client name of up to 15 characters.

```yaml
client_machine.name: 'Workplace'
```

#### `enterprise_search.api_key` (required)

The Workplace Search API key. See [Create a Workplace Search API key](#create-a-workplace-search-api-key).

```yaml
enterprise_search.api_key: 'zvksftxrudcitxa7ris4328b'
```

#### `enterprise_search.source_id` (required)

The ID of the Workplace Search content source. See [Create a Workplace Search content source](#create-a-workplace-search-content-source).

```yaml
enterprise_search.source_id: '12345678909876543ab21012a'
```

#### `enterprise_search.host_url` (required)

The [Enterprise Search base URL](https://www.elastic.co/guide/en/enterprise-search/current/endpoints-ref.html#enterprise-search-base-url) for your Elastic deployment.

```yaml
enterprise_search.host_url: https://my-deployment.ent.europe-west1.gcp.cloud.es.io
```

#### `enable_document_permission`

Whether the connector should sync [document-level permissions (DLP)](#use-document-level-permissions-dlp) from Network Drives.

```yaml
enable_document_permission: Yes
```

#### `include/exclude`

Specifies which files should be indexed based on their size or path template in Network Drives.

```yaml
include:
   size:
   path_template:
exclude:
   size:
   path_template:
```

#### `start_time`

A UTC timestamp the connector uses to determine which objects to extract and sync from Network Drives. Determines the *starting* point for a [full sync](#full-sync).
Supports the following time format `YYYY-MM-DDTHH:MM:SSZ`

```yaml
start_time: 2022-04-01T04:44:16Z
```

#### `end_time`

A UTC timestamp the connector uses to determine which objects to extract and sync from Network Drives. Determines the *stopping* point for a [full sync](#full-sync).
It supports the following time format YYYY-MM-DDTHH:MM:SSZ

```yaml
end_time: 2022-04-01T04:44:16Z
```

#### `log_level`

The level or severity that determines the threshold for [logging](#log-errors-and-exceptions) a message. One of the following values:

- `DEBUG`
- `INFO` (default)
- `WARN`
- `ERROR`

```yaml
log_level: INFO
```

#### `retry_count`

The number of retries to perform when there is a server error. The connector applies an exponential backoff algorithm to retries.

```yaml
retry_count: 3
```

#### `network_drives_sync_thread_count`

The number of threads the connector will run in parallel when fetching documents from the Network Drive. By default, the connector uses 5 threads.

```yaml
network_drives_sync_thread_count: 5
```

#### `enterprise_search_sync_thread_count`

The number of threads the connector will run in parallel when indexing documents into the Enterprise Search instance. By default, the connector uses 5 threads.

```yaml
enterprise_search_sync_thread_count: 5
```

For the Linux distribution with atleast 2 GB RAM and 4 vCPUs, you can increase the thread counts if the overall CPU and RAM are under utilized i.e. below 60-70%.

#### `network_drives_enterprise_search_user_mapping`

The pathname of the CSV file containing the user identity mappings for [document-level permissions (DLP)](#use-document-level-permissions-dlp).

```yaml
network_drives_enterprise_search_user_mapping: 'C:/Users/banon/connector/identity_mappings.csv'
```

#### Enterprise Search compatibility

The Network Drives connector package is compatible with Elastic deployments that meet the following criteria:

- Elastic Enterprise Search version greater than or equal to 7.13.0 and less than 8.0.0.
- An Elastic subscription that supports this feature. Refer to the Elastic subscriptions pages for [Elastic Cloud](https://www.elastic.co/subscriptions/cloud) and [self-managed](https://www.elastic.co/subscriptions) deployments.

#### Runtime dependencies

Each Network Drives connector requires a runtime environment that satisfies the following dependencies:

- Windows, MacOS, or Linux server. The connector has been tested with CentOS 7, MacOS Monterey v12.0.1, and Windows 10.
- Python version 3.6 or later.
- To extract content from images: Java version 7 or later, and [`tesseract` command](https://github.com/tesseract-ocr/tesseract) installed and added to `PATH`
- To schedule recurring syncs: a job scheduler, such as `cron`
