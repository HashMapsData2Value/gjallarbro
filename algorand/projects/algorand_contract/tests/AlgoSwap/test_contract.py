from time import sleep
import pytest
from smart_contracts.leak_swap.contract import LeakSwap
from algopy import arc4
from algopy_testing import AlgopyTestContext
from tests.monero_utils import generate_leaky_signature

from algosdk.encoding import decode_address

from tests.utils import get_latest_timestamp

@pytest.fixture()
def contract(ali_xternal_keys,
             xin_xternal_keys,
             ali_algo_address,
             xin_algo_address,
             timestamp_0,
             timestamp_1) -> LeakSwap:

    contract = LeakSwap()
    contract.create(
        ali_algo_addr=arc4.Address(ali_algo_address.address),
        ali_xternal_pk=arc4.DynamicBytes(ali_xternal_keys[1]),
        xin_algo_addr=arc4.Address(xin_algo_address.address),
        xin_xternal_pk=arc4.DynamicBytes(xin_xternal_keys[1]),
        t0=arc4.UInt64(timestamp_0),
        t1=arc4.UInt64(timestamp_1),
    )

    return contract

def test_LeakSwap_set_ready(context: AlgopyTestContext, contract: LeakSwap) -> None:
    # Still in the initial state
    assert contract.get_contract_state() == 0

    # Act
    with context.txn.create_group(active_txn_overrides={"sender": contract.ali_algo_addr.value}):
        contract.set_ready()
    # Assert
    assert contract.get_contract_state() == 1

def test_LeakSwap_leaky_refund(
        context: AlgopyTestContext,
        contract: LeakSwap,
        ali_xternal_keys) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    assert contract.data_to_sign == context.ledger.get_app(contract).address.bytes

    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))

    leaky_sig = generate_leaky_signature(
        ali_xternal_keys[0],
        ali_xternal_keys[1],
        contract_address_decoded)
    # Act
    with context.txn.create_group(active_txn_overrides={"sender": contract.ali_algo_addr.value}):
        contract.leaky_refund(arc4.DynamicBytes(leaky_sig))
    # Assert
    # Add appropriate assertions based on the expected state changes


def test_LeakSwap_leaky_claim_set_ready(
        context: AlgopyTestContext,
        contract: LeakSwap,
        algod_client,
        xin_xternal_keys) -> None:
    
    """
    Test the case where the contract has been set ready, due to time passing.
    """
    # Arrange

    assert contract.get_contract_state() == arc4.UInt64(0)

    with context.txn.create_group(active_txn_overrides={"sender": contract.ali_algo_addr.value}):
        contract.set_ready()

    assert contract.get_contract_state() == arc4.UInt64(1)
    assert contract.data_to_sign == context.ledger.get_app(contract).address.bytes

    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))

    leaky_sig = generate_leaky_signature(
        xin_xternal_keys[0],
        xin_xternal_keys[1],
        contract_address_decoded)
    # Act
    with context.txn.create_group(active_txn_overrides={"sender": contract.xin_algo_addr.value}):
        contract.leaky_claim(arc4.DynamicBytes(leaky_sig))
    # Assert
    # Add appropriate assertions based on the expected state changes

def test_LeakSwap_leaky_claim_t0(
        context: AlgopyTestContext,
        contract: LeakSwap,
        algod_client,
        timestamp_0,
        xin_xternal_keys) -> None:
    
    """
    Test the case where the contract has entered post t0 state, due to time passing.
    """
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    #time_warp(timestamp_0 + 1)
    sleep(timestamp_0 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(2)
    assert contract.data_to_sign == context.ledger.get_app(contract).address.bytes

    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))

    leaky_sig = generate_leaky_signature(
        xin_xternal_keys[0],
        xin_xternal_keys[1],
        contract_address_decoded)
    # Act
    with context.txn.create_group(active_txn_overrides={"sender": contract.xin_algo_addr.value}):
        contract.leaky_claim(arc4.DynamicBytes(leaky_sig))
    # Assert
    # Add appropriate assertions based on the expected state changes

def test_LeakSwap_punish_refund(
        context: AlgopyTestContext,
        contract: LeakSwap,
        algod_client,
        timestamp_1) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    #time_warp(timestamp_1 + 1)
    sleep(timestamp_1 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(3)

    # Act
    with context.txn.create_group(active_txn_overrides={"sender": contract.ali_algo_addr.value}):
        contract.punish_refund()

# New tests for invalid actions

def test_invalid_leaky_refund_by_non_ali(context: AlgopyTestContext, contract: LeakSwap, ali_xternal_keys, xin_algo_address) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))
    leaky_sig = generate_leaky_signature(ali_xternal_keys[0], ali_xternal_keys[1], contract_address_decoded)
    
    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": xin_algo_address.address}):
            contract.leaky_refund(arc4.DynamicBytes(leaky_sig))

def test_invalid_leaky_claim_by_non_xin(context: AlgopyTestContext, contract: LeakSwap, ali_algo_address, xin_xternal_keys, timestamp_0, algod_client) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    sleep(timestamp_0 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(2)
    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))
    leaky_sig = generate_leaky_signature(xin_xternal_keys[0], xin_xternal_keys[1], contract_address_decoded)
    
    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": ali_algo_address.address}):
            contract.leaky_claim(arc4.DynamicBytes(leaky_sig))

def test_invalid_punish_refund_before_t1(context: AlgopyTestContext, contract: LeakSwap, ali_algo_address, timestamp_1, algod_client) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    sleep(timestamp_1 - get_latest_timestamp(algod_client) - 1)
    assert contract.get_contract_state() != arc4.UInt64(3)
    
    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": ali_algo_address.address}):
            contract.punish_refund()

def test_invalid_leaky_claim_after_t1(context: AlgopyTestContext, contract: LeakSwap, xin_algo_address, xin_xternal_keys, timestamp_1, algod_client) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    sleep(timestamp_1 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(3)
    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))
    leaky_sig = generate_leaky_signature(xin_xternal_keys[0], xin_xternal_keys[1], contract_address_decoded)
    
    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": xin_algo_address.address}):
            contract.leaky_claim(arc4.DynamicBytes(leaky_sig))

def test_invalid_leaky_refund_after_t0(context: AlgopyTestContext, contract: LeakSwap, ali_algo_address, ali_xternal_keys, timestamp_0, algod_client) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    sleep(timestamp_0 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(2)
    contract_address_decoded = decode_address(str(context.ledger.get_app(contract).address))
    leaky_sig = generate_leaky_signature(ali_xternal_keys[0], ali_xternal_keys[1], contract_address_decoded)
    
    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": ali_algo_address.address}):
            contract.leaky_refund(arc4.DynamicBytes(leaky_sig))

# Additional tests for invalid actions

def test_invalid_leaky_refund_with_wrong_signature(context: AlgopyTestContext, contract: LeakSwap, ali_xternal_keys) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    wrong_signature = b'\x00' * 64  # Invalid signature

    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": contract.ali_algo_addr.value}):
            contract.leaky_refund(arc4.DynamicBytes(wrong_signature))

def test_invalid_leaky_claim_with_wrong_signature(context: AlgopyTestContext, contract: LeakSwap, xin_xternal_keys, timestamp_0, algod_client) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    sleep(timestamp_0 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(2)
    wrong_signature = b'\x00' * 64  # Invalid signature

    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": contract.xin_algo_addr.value}):
            contract.leaky_claim(arc4.DynamicBytes(wrong_signature))

def test_invalid_punish_refund_by_non_ali(context: AlgopyTestContext, contract: LeakSwap, xin_algo_address, timestamp_1, algod_client) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)
    sleep(timestamp_1 - get_latest_timestamp(algod_client) + 1)
    assert contract.get_contract_state() == arc4.UInt64(3)

    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": xin_algo_address.address}):
            contract.punish_refund()

def test_invalid_set_ready_by_non_ali(context: AlgopyTestContext, contract: LeakSwap, xin_algo_address) -> None:
    # Arrange
    assert contract.get_contract_state() == arc4.UInt64(0)

    # Act & Assert
    with pytest.raises(AssertionError):
        with context.txn.create_group(active_txn_overrides={"sender": xin_algo_address.address}):
            contract.set_ready()
