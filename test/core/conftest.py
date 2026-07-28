"""test/core: real-cloud Azure matrix -- {azure-az, azure-abfss} (a suite-level `matrix=`,
docs/RESOURCE-PLANNING.md §5 phase 9 in the driver). `azurite-az` is NOT in this matrix: DuckDB's
`CREDENTIAL_CHAIN` provider hardcodes `https://<account>.<endpoint>` (azure_storage_account_client.cpp
`AccountUrl`) and has no way to accept a static key at all, so it's structurally incompatible with
Azurite's `http://host:port/<account>` shape -- confirmed both by reading the C++ and by a live probe
against a running Azurite instance.

Auth: ONE SPN credential (AZURE_CLIENT_ID/CLIENT_SECRET/TENANT_ID), fetched via 1Password the same way
`scripts/env_azure` already does, adopted into `os.environ` (`adopt="env"`) so `CREDENTIAL_CHAIN`'s
default chain (its `EnvironmentCredential` link) picks it up automatically -- no explicit auth params
in the injected `CREATE SECRET` at all.

Both cells share the SAME injected `CREATE SECRET` text (`auto_init_sql=True`, the non-`--repl`
generalization of `to_init_sql` -- see driver docs): each cell's DATA_DIR/TEMP_DIR is a FULLY
QUALIFIED URI (`{scheme}://<account>.<endpoint>/<container>/<path>`), so DuckDB resolves account +
endpoint straight from the query URL (`is_fully_qualified ? AccountUrl(url) : AccountUrl(secret)`,
same file) and never even looks at the secret's `account_name`/`endpoint` -- confirmed the same way.
That's what makes the ONE secret cell-agnostic despite az/abfss using different storage accounts.
"""

import os
import subprocess

from ducktest import credential, register_suite

# `op read <item> | op inject` -- same 1Password vault item scripts/env_azure already reads.
_VAULT_ITEM = "op://testing-rw/azure/_env"
_SPN_VARS = ("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID")

# Real infra (scripts/env_azure): the SAME container/path text under two different storage accounts
# (az's account has hierarchical namespace off; abfss's has it on).
_CONTAINER_PATH = "duckdblabs-data/common/azure_data"
_TEMP_CONTAINER_PREFIX = "duckdblabs-write-testing/extension/azure"
_AZ_ACCOUNT = "duckdblabstestdatablob"
_ABFSS_ACCOUNT = "duckdblabstestdata"


def _cell_properties(scheme: str, account: str, endpoint: str) -> dict:
    """Per-cell `properties` (driver's `_matrix_cell_properties`/`_split_matrix_cell_properties`):
    DATA_DIR/TEMP_DIR are permanently reserved by DuckDB's own C++ harness for its local
    scratch/data path (`test_config.cpp`'s `test_env["DATA_DIR"|"TEMP_DIR"]`, unconditionally
    copied into a fresh test's substitution map before the body parses -- `require-env` against
    either name always hard-fails "already defined", override or not). Declaring `data_dir`/
    `temp_dir_root` here routes them (the driver's call, not ours) into `--data-dir`/
    `--temp-dir-root` instead, which sets the SAME reserved names to OUR values at the source, so
    `{DATA_DIR}`/`{TEMP_DIR}` in read.test/write.test resolve correctly with no `require-env` gate
    needed (and none possible). `temp_dir_root` gets `/<session-id>/<batch-id>/<test-id>` appended
    by the driver/harness themselves, so no manual suffix is needed for uniqueness."""
    return {
        "data_dir": f"{scheme}://{account}.{endpoint}/{_CONTAINER_PATH}",
        "temp_dir_root": f"{scheme}://{account}.{endpoint}/{_TEMP_CONTAINER_PREFIX}",
    }


def _fetch_azure_spn(config) -> dict:
    """Fetch the SPN triple via 1Password, mirroring scripts/env_azure's `op read | op inject` --
    parsed directly from the `export KEY=VALUE` lines it emits (no shell eval of injected content)."""
    proc = subprocess.run(["bash", "-c", f"op read {_VAULT_ITEM} | op inject"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"`op read {_VAULT_ITEM} | op inject` failed: {proc.stderr.strip()}")
    found = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        key, _, value = line[len("export ") :].partition("=")
        found[key.strip()] = value.strip().strip("'\"")
    missing = [v for v in _SPN_VARS if v not in found]
    if missing:
        raise RuntimeError(f"1Password item {_VAULT_ITEM!r} did not yield {missing}")
    return {k: found[k] for k in _SPN_VARS}


def _spn_available() -> bool:
    """Skip the 1Password fetch entirely when the SPN triple is already in the env (e.g. a shell that
    already ran scripts/env_azure) -- same non-interactive short-circuit every credential() supports.

    CAVEAT (see Credential's own docstring): when this short-circuits, `_read_provisioned_credential`
    has nothing to read back (nothing was ever fetched/stored), so `auto_init_sql` contributes NO
    CREATE SECRET even though the creds are genuinely usable -- a pre-existing to_init_sql limitation,
    not new here. If that combination ever matters, the fix belongs in the driver, not this conftest.
    """
    return all(os.environ.get(v) for v in _SPN_VARS)


def _azure_secret_sql(value, *, redact=False) -> str:
    """`require azure` (not `LOAD azure;`): --init-sqllogic runs before this file's own `require azure`
    ever would, and only `require` routes through the reliable LoadExtension path (local-repo install
    first) -- see driver's `Credential.to_init_sql` docstring."""
    return "require azure\n\nCREATE SECRET az1 (TYPE AZURE, PROVIDER CREDENTIAL_CHAIN);\n"


def pytest_configure(config):
    register_suite(
        config,
        "core",
        path="test/core",
        marker="core",
        default=False,
        auto_init_sql=True,
        matrix=[
            {"backend": "azure-az", "properties": _cell_properties("az", _AZ_ACCOUNT, "blob.core.windows.net")},
            {
                "backend": "azure-abfss",
                "properties": _cell_properties("abfss", _ABFSS_ACCOUNT, "dfs.core.windows.net"),
            },
        ],
        credentials=[
            credential(
                "azure_spn",
                fetch=_fetch_azure_spn,
                adopt="env",
                available=_spn_available,
                to_init_sql=_azure_secret_sql,
            )
        ],
    )
