# DuckDB Azure Extension

This extension adds a filesystem abstraction for Azure blob storage to DuckDB. To use it, install latest DuckDB. The extension currently supports only **reads** and **globs**.

When debugging issues, especially authentication, start by adding the environment variable `AZURE_LOG_LEVEL=verbose` to duckdb.

## TODO: Note this and its side effects

<https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-known-issues>

My favorite:

> Third party applications that use REST APIs to work will continue to work if you use them with Data Lake Storage. Applications that call Blob APIs will likely work.

## Basics

Setup authentication (leverages either Azure CLI or Managed Identity):

```sql
CREATE SECRET secret1 (
    TYPE AZURE,
    PROVIDER CREDENTIAL_CHAIN,
    ACCOUNT_NAME '⟨storage account name⟩'
);
```

Then to query a file on azure:

```sql
SELECT count(*) FROM 'az://<my_container>/<my_file>.<parquet_or_csv>';
```

Globbing is also supported:

```sql
SELECT count(*) FROM 'az://dummy_container/*.csv';
```

## Other authentication methods

Other authentication options available:

### Connection string

```sql
CREATE SECRET secret2 (
    TYPE AZURE,
    CONNECTION_STRING '<value>'
);
```

### Service Principal

(replace `CLIENT_SECRET` with `CLIENT_CERTIFICATE_PATH` to use a client certificate)

```sql
CREATE SECRET azure3 (
    TYPE AZURE,
    PROVIDER SERVICE_PRINCIPAL,
    TENANT_ID '⟨tenant id⟩',
    CLIENT_ID '⟨client id⟩',
    CLIENT_SECRET '⟨client secret⟩',
    ACCOUNT_NAME '⟨storage account name⟩'
);
```

### Access token

(its audience needs to be `https://storage.azure.com`)

```sql
CREATE SECRET secret4 (
    TYPE AZURE,
    PROVIDER ACCESS_TOKEN,
    ACCESS_TOKEN '⟨value⟩'
    ACCOUNT_NAME '⟨storage account name⟩'
);
```

### Anonymous

```sql
CREATE SECRET secret5 (
    TYPE AZURE,
    PROVIDER CONFIG,
    ACCOUNT_NAME '⟨storage account name⟩'
);
```

### Managed Identity with User-assigned ID (UAMI)

```sql
CREATE SECRET secret1 (
    TYPE AZURE,
    PROVIDER MANAGED_IDENTITY,
    ACCOUNT_NAME '⟨storage account name⟩',
    CLIENT_ID '⟨used-assigned managed identity client id⟩'
);
```

`CLIENT_ID` is optional; if not specified, the Azure SDK will attempt to find and use either a
System-assigned Managed Identity (SAMI) or User-assigned Managed Identity (UAMI). If both are
defined, or more than 1 UAMI is available, order and behavior is undefined.

Alternatively, `OBJECT_ID` or `RESOURCE_ID` may be used instead of `CLIENT_ID`. Only 1 of these
IDs may be specified.

See also [Azure Identity Managed Identity Support](https://github.com/Azure/azure-sdk-for-cpp/tree/main/sdk/identity/azure-identity#managed-identity-support)

## Supported architectures

The extension is tested & distributed for Linux (x64, arm64), MacOS (x64, arm64) and Windows (x64)

## Documentation

See the [Azure page in the DuckDB documentation](https://duckdb.org/docs/extensions/azure).

Check out the tests in `test/sql` for more examples.

## Building

For development, this extension requires [CMake](https://cmake.org), Python3, a `C++11` compliant compiler, and the Azure C++ SDK. Run `make` in the root directory to compile the sources. Run `make debug` to build a non-optimized debug version. Run `make test` to verify that your version works properly after making changes. Install the Azure C++ SDK using [vcpkg](https://vcpkg.io/en/getting-started.html) and set the `VCPKG_TOOLCHAIN_PATH` environment variable when building.

```shell
sudo apt-get update && sudo apt-get install -y git g++ cmake pkg-config ninja-build libssl-dev
git clone --recursive https://github.com/duckdb/duckdb_azure
git clone https://github.com/microsoft/vcpkg
./vcpkg/bootstrap-vcpkg.sh
cd duckdb_azure
GEN=ninja VCPKG_TOOLCHAIN_PATH=$PWD/../vcpkg/scripts/buildsystems/vcpkg.cmake make
```

## Testing

Tests are typical run both locally, using Azurite (az:// blob store only), and the cloud using
both Azure's Blob and ADLSv2 storage services.

In order to run tests against Azurite, you'll need to run it with default configuration, and populate
it with test data:

```
azurite --location ./azurite 2>&1
```

In another window, populate the data:

```
scripts/upload_test_files_to_azurite.sh
```

And thereafter you can execute the tests with (assuming a debug build):

```
scripts/env_azurite --az build/debug/test/unittest
```

Note that while many test names are listed, in this case only those ending with `__local_az` will actually be executed, all `__cloud_*` tests will be skipped in this configuration. Additionally `.test_slow` tests are also skipped by default. To run those, run as follows:

```
scripts/env_azurite --az build/debug/test/unittest 'test/sql/*'
```

Cloud based Azure tests can be run similarly; we suggest copying `scripts/env_azure` and editing to set all appropriate variables for your use case (az and/or abfss). The tests can also be authenticated via the az cli. Seek "cli" in [Github Workflow definition](.github/workflow/CloudTesting.yml) to see how `az login` can be used to accomplish this.

Please also refer to our [Build Guide](https://duckdb.org/dev/building) and [Contribution Guide](<[CONTRIBUTING.md](https://github.com/duckdb/duckdb/blob/main/CONTRIBUTING.md)>).
