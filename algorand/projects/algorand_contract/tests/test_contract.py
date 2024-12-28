import typing
from collections.abc import Generator
import traceback

import algopy
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context, arc4_prefix
from smart_contracts.leak_swap.contract import LeakSwap
from algopy import arc4, Bytes
from tests.utils import generate_ed25519_keys, generate_leaky_signature
from algosdk import account


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx

@pytest.fixture()
def ali_xternal_keys() -> typing.List[bytes]:
    ali_xternal_keys = generate_ed25519_keys()
    return ali_xternal_keys

@pytest.fixture()
def xin_xternal_keys() -> typing.List[bytes]:
    xin_xternal_keys = generate_ed25519_keys()
    return xin_xternal_keys

@pytest.fixture()
def ali_algo_address() -> str:
    _, ali_algo_address = account.generate_account()
    return ali_algo_address

@pytest.fixture()
def xin_algo_address() -> str:
    _, xin_algo_address = account.generate_account()
    return xin_algo_address

@pytest.fixture()
def contract(ali_xternal_keys, xin_xternal_keys, ali_algo_address, xin_algo_address) -> LeakSwap:

    contract = LeakSwap()
    print("Before contract.create")
    try:
        contract.create(
            ali_algo_addr=arc4.Address(ali_algo_address),
            ali_xternal_pk=arc4.DynamicBytes(ali_xternal_keys[1]),
            xin_algo_addr=arc4.Address(xin_algo_address),
            xin_xternal_pk=arc4.DynamicBytes(xin_xternal_keys[1]),
            t0=arc4.UInt64(0),
            t1=arc4.UInt64(9999999999)
        )
        print("After contract.create")
    except Exception as e:
        print(f"Exception during contract.create: {e}")
        traceback.print_exc()
        raise

    print(contract)
    print(contract.ali_algo_addr)
    return contract

def test_LeakSwap_hello(context: AlgopyTestContext, contract: LeakSwap) -> None:
    print("Running test_LeakSwap_hello")
    # Act
    result = contract.hello(arc4.String("Alice"))
    # Assert
    assert result == "Hello, Alice"

""" def test_LeakSwap_set_ready(context: AlgopyTestContext, contract: LeakSwap) -> None:
    print("Running test_LeakSwap_set_ready")
    # Act
    contract.set_ready()
    # Assert
    assert contract.ali_ready.value == True

def test_LeakSwap_leaky_refund(context: AlgopyTestContext, contract: LeakSwap) -> None:
    print("Running test_LeakSwap_leaky_refund")
    # Arrange
    contract.t0.value = 9999999999  # Future timestamp
    assert contract.data_to_sign == context.ledger.get_app(contract).address.bytes
    leaky_sig = generate_leaky_signature(ali_xternal_keys[0], contract.data_to_sign)
    # Act
    contract.leaky_refund(leaky_sig)
    # Assert
    # Add appropriate assertions based on the expected state changes

def test_LeakSwap_leaky_claim(context: AlgopyTestContext, contract: LeakSwap) -> None:
    print("Running test_LeakSwap_leaky_claim")
    # Arrange
    contract.t0.value = 0  # Past timestamp
    contract.t1.value = 9999999999  # Future timestamp
    assert contract.data_to_sign == context.ledger.get_app(contract).address.bytes
    leaky_sig = generate_leaky_signature(xin_xternal_keys[0], contract.data_to_sign)
    # Act
    contract.leaky_claim(leaky_sig)
    # Assert
    # Add appropriate assertions based on the expected state changes

def test_LeakSwap_punish_refund(context: AlgopyTestContext, contract: LeakSwap) -> None:
    print("Running test_LeakSwap_punish_refund")
    # Arrange
    contract.t1.value = 0  # Past timestamp
    # Act
    contract.punish_refund()
    # Assert
    # Add appropriate assertions based on the expected state changes
 """
