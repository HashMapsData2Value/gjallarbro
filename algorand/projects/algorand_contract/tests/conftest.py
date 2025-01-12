from datetime import datetime
from typing import List, Final
from collections.abc import Generator
import pytest

from tests.monero_utils import generate_ed25519_keys

from algopy_testing import AlgopyTestContext, algopy_testing_context

from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils import (
    EnsureBalanceParameters,
    ensure_funded,
    get_algod_client,
    get_default_localnet_config,
    get_indexer_client,
)

from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
)


INITIAL_ALGO_FUNDS: Final[int] = 10_000_000_000  # microALGO

@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx

@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    # by default we are using localnet algod
    client = get_algod_client(get_default_localnet_config("algod"))
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client(get_default_localnet_config("indexer"))


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client


@pytest.fixture()
def ali_xternal_keys() -> List[bytes]:
    ali_xternal_keys = generate_ed25519_keys()
    return ali_xternal_keys

@pytest.fixture()
def xin_xternal_keys() -> List[bytes]:
    xin_xternal_keys = generate_ed25519_keys()
    return xin_xternal_keys

@pytest.fixture()
def ali_algo_address(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_ALGO_FUNDS,
        ),
    )
    return account

@pytest.fixture()
def xin_algo_address(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    # TODO: Add logicsig combo to allow xin_algo_address to not have to be funded
    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_ALGO_FUNDS,
        ),
    )
    return account

@pytest.fixture()
def now() -> int:
    return int(datetime.now().timestamp())

@pytest.fixture()
def timestamp_0(now: int) -> int:
    return now + 10

@pytest.fixture()
def timestamp_1(timestamp_0: int) -> int:
    return timestamp_0 + 10
    
