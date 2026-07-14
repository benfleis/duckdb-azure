"""Azure suite wiring on ducktest — azurite as an EAGER, env-adopting, self-populating service.

On selection of the `azurite` suite, the driver (controller, pre-fork) boots azurite, runs `_populate`
(the rclone equivalent of `scripts/upload_test_files_to_azurite.sh`), and adopts `_azure_env` into
`os.environ` — so even a bare `.test` body (no `.py` driver, no fixture to pull) gets
`${AZURE_STORAGE_CONNECTION_STRING}`/`${AZ_DATA_DIR}` and the seeded `data/`. See driver docs/SERVICES.md.
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
    """Structure + data (idempotent): create the containers, sync `data/` into the read ones."""
    remote = rclone_remote(block)
    for c in (PRIVATE, PUBLIC, WRITES):
        rclone.mkdir(remote, c)
    for c in (PRIVATE, PUBLIC):
        rclone.sync(str(DATA), remote, c)  # data/l.csv -> <c>/l.csv, etc.


def _azure_env(block):
    """The env a bare `.test` body needs: azurite's connection string/account + AZ_DATA_DIR."""
    return {**azurite_env(block), "AZ_DATA_DIR": PRIVATE}


def pytest_configure(config):
    register_suite(
        config,
        "azurite",
        path="test/azurite",
        marker="azurite",
        default=True,
        services=[
            use_service(
                AZURITE_SERVICE,
                provision="eager",
                to_env=_azure_env,
                populate=_populate,
            )
        ],
    )


@pytest.fixture(scope="session")
def azurite(request):
    """The azurite block for a Python test (already eagerly booted — this returns the shared instance)."""
    return types.SimpleNamespace(**provision_service(request.config, AZURITE_SERVICE))
