"""Azure test suites on ducktest.

- ``local`` (test/azurite/) — azurite-backed, smoke / DEFAULT. Eager azurite boots, seeds ``data/`` (the
  rclone equivalent of scripts/upload_test_files_to_azurite.sh), and adopts the azure connection env, so
  the bare ``.test`` bodies run with no manual env script. ``auto_init_sql=True`` also auto-injects
  AZURITE_SERVICE's own ``CREATE SECRET`` (``azurite_init_sql``, driver-side) ahead of the test body, so
  a body that just needs A secret to exist -- not testing secret creation/scoping itself -- writes none
  of its own.
- ``local_auth`` (test/azurite_auth/) — SAME azurite backing/env as ``local`` (no ``auto_init_sql``,
  deliberately, and a DISTINCT marker -- see below): these bodies test secret/credential MECHANICS
  itself (creation, scoping, the no-credentials-configured error path, an invalid-target error message
  that changes once ANY secret exists) as their actual subject, not incidentally-needed scaffolding --
  auto-injecting a secret ahead of the body would corrupt exactly what they're asserting (e.g.
  ``azure.test`` blanks ``azure_storage_connection_string`` and expects "No valid Azure credentials
  found"; a pre-existing secret would make that silently pass for the wrong reason; ``azure_vfs_ops.test``
  expects "Cannot identify the storage account" for an invalid ``abfss://`` target -- pre-empted by a
  secret, DuckDB instead tries to actually connect and gets "Could not connect to server", since Azurite
  doesn't serve DFS/abfss at all). Split into its own suite because `auto_init_sql` has no per-item
  opt-out -- only a per-suite one, and `_item_in_suite` has no nearest-path-wins precedence, so a nested
  carve-out under ``local`` wouldn't actually exclude anything (both suites would still match by path).
  DISTINCT marker (``local_auth``, not ``local``) is load-bearing, not cosmetic: `_apply_suite_markers`
  auto-stamps each suite's OWN marker by path, so sharing ``local``'s marker name would make
  `_item_in_suite`'s marker-check (which can't tell which suite registration caused a given stamp)
  wrongly match these items against the ``local`` suite too -- reintroducing the exact auto-injection
  this split exists to prevent. Found live: it did, silently, until the marker was split out.
- ``cloud`` (test/azure/) — real Azure (AZURE_* creds / ABFSS). Opt-in (``-m cloud``); the bodies'
  ``require-env`` gates them until creds are present (a ``credential`` wiring is future work -- see
  ``test/core``'s newer suite for the pattern this one predates and should eventually migrate to).
- ``proxy`` (test/proxy/) — via squid. Opt-in, deferred (needs a squid service that ``depends_on`` azurite).

Suite/marker names are the ROLES (local/cloud/proxy); the directories are the backing (azurite/azure).
"""

import pathlib
import types

import pytest

from ducktest import provision_service, register_suite, use_service
from ducktest.resources.azurite import AZURITE_SERVICE, azurite_env, rclone_remote
from ducktest.tools import rclone

DATA = pathlib.Path(__file__).parent.parent / "data"  # repo data/
PRIVATE, PUBLIC, WRITES = (
    "testing-private",
    "testing-public",
    "writes",
)  # match the upload script


def _populate(block, config):
    """Structure + data (idempotent): create the containers, sync ``data/`` into the read ones."""
    remote = rclone_remote(block)
    for c in (PRIVATE, PUBLIC, WRITES):
        rclone.mkdir(remote, c)
    for c in (PRIVATE, PUBLIC):
        rclone.sync(str(DATA), remote, c)  # data/l.csv -> <c>/l.csv, etc.


def _azure_env(block):
    """The env a bare ``.test`` body needs: azurite's connection string/account + the data/temp dirs.

    ``STORAGE_ACCOUNT`` (not ``AZ_``-prefixed): this suite only ever exercises the ``az://`` protocol
    against the one azurite account, so there's no second simultaneous value to disambiguate (see
    docs/RESOURCE-PLANNING.md). ``azurite_env`` still layers in its own ``AZ_STORAGE_ACCOUNT`` alias too
    (driver-side, unused here).

    ``AZ_DATA_DIR``/``AZ_TEMP_DIR`` (NOT plain ``DATA_DIR``/``TEMP_DIR``): found live (a real
    reverse-port-mapped azurite run) that DuckDB's own C++ harness pre-registers `DATA_DIR`/`TEMP_DIR`
    for its LOCAL scratch/data path (`test_config.cpp`'s `test_env["DATA_DIR"|"TEMP_DIR"]`) -- a `.test`
    file's `require-env TEMP_DIR` against an already-registered name hard-fails at parse time
    ("Environment variable 'TEMP_DIR' has already been defined", `sqllogic_test_runner.cpp:1217`).
    These two names are permanently claimed by the harness for a different (local filesystem) concept;
    azure's remote-path env vars need their own names regardless of any future matrix/foreach cleanup.
    """
    return {**azurite_env(block), "AZ_DATA_DIR": PRIVATE, "AZ_TEMP_DIR": WRITES, "STORAGE_ACCOUNT": block["account"]}


def pytest_configure(config):
    register_suite(
        config,
        "local",
        path="test/azurite",
        marker="local",
        default=True,
        auto_init_sql=True,
        services=[
            use_service(
                AZURITE_SERVICE,
                to_env=_azure_env,
                populate=_populate,
            )
        ],
    )
    register_suite(
        config,
        "local_auth",
        path="test/azurite_auth",
        marker="local_auth",
        default=True,
        services=[
            use_service(
                AZURITE_SERVICE,
                to_env=_azure_env,
                populate=_populate,
            )
        ],
    )
    register_suite(config, "cloud", path="test/azure", marker="cloud", default=False)
    register_suite(config, "proxy", path="test/proxy", marker="proxy", default=False)


@pytest.fixture(scope="session")
def azurite(request):
    """The azurite block for a Python test (already eagerly booted — this returns the shared instance)."""
    return types.SimpleNamespace(**provision_service(request.config, AZURITE_SERVICE))
