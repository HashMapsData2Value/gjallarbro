"""
The entire sequence, ideal case. Proof-of-Concept.
"""

from encodings import utf_8
import importlib, time
import utils as u
import algorand_utils as au
import monero_utils as mu

# Generate Keys/Accounts

algorand_accounts = au.get_Algorand_accounts()
alice_algorand_account = algorand_accounts[0]
bob_algorand_account = algorand_accounts[1]
eve_algorand_account = algorand_accounts[2]

alice_monero_keys = mu.generate_monero_keys() # [0][0] is private spend, [0][1] is public spend, [1][0] is private view, [1][1] is public view
bob_monero_keys = mu.generate_monero_keys()

alice_trades_algos = 500
bob_trades_xmr = 1.1

t0 = int(time.time()) + 70
t1 = t0 + 60

SHARED_OR_PUBLIC_INFORMATION = {
    'alice_algorand_address': alice_algorand_account[0],
    'alice_monero_pubspend': alice_monero_keys[0][1],
    'alice_monero_viewkeys': alice_monero_keys[1],
    'alice_algos': alice_trades_algos,
    'bob_algorand_address': bob_algorand_account[0],
    'bob_monero_pubspend': bob_monero_keys[0][1],
    'bob_monero_viewkeys': bob_monero_keys[1],
    'bob_xmr': bob_trades_xmr,
    't0': t0,
    't1': t1
    }

bob_before =  au.get_balance(bob_algorand_account)
alice_before = au.get_balance(alice_algorand_account)

# Build Pyteal & Deploy contract to Algorand
## Alice generates the contract using publicly shared information
approval_teal, clear_teal = au.generate_contract(importlib.import_module('contract'), {
    "alice_addr": alice_algorand_account[0],
    "alice_partial_pk": "0x{}".format(alice_monero_keys[0][1].hex()),
    "bob_addr": bob_algorand_account[0],
    "bob_partial_pk": "0x{}".format(bob_monero_keys[0][1].hex()),
    "t0_timestamp": t0,
    "t1_timestamp": t1,
})

program_hash = au.get_program_hash(approval_teal)

## Bob can also produce the same program_hash
## TODO: BOB, ON HIS SIDE, COMPILES PROGRAM
SHARED_OR_PUBLIC_INFORMATION['program_hash'] = program_hash

## Alice deploys the contract 
app_id = au.deploy_contract(alice_algorand_account[0], alice_algorand_account[1], approval_teal, clear_teal)

## TODO: BOB SCANS FOR APP_ID
SHARED_OR_PUBLIC_INFORMATION['app_id'] = app_id


# Alice funds the smart contract
au.fund_contract(app_id, alice_algorand_account, int(500 * 1e6))

# Bob sees the contract and seeds combined account
"""INSERT ALGORAND QUERY HERE"""
"""INSERT MONERO STUFF HERE"""

# Alice queries Monero history (for combined view key)
# -> flags as ready

"""INSERT MONERO STUFF HERE"""

au.alice_set_ready(app_id, alice_algorand_account)

# Bob leakily claims the funds to his account

signature = au.get_signature(bob_algorand_account, bob_monero_keys, program_hash)

au.bob_leaky_claim(app_id, bob_algorand_account, signature)

# Alice queries Algorand history (for signature input)
# -> calculates Bob's partial key
recovered_signature = au.get_counterparty_signature(app_id)
recovered_private_key = au.recover_counterparty_private_key(program_hash, SHARED_OR_PUBLIC_INFORMATION['bob_algorand_address'], recovered_signature, SHARED_OR_PUBLIC_INFORMATION['bob_monero_pubspend'])
assert recovered_private_key == bob_monero_keys[0][0]

"""INSERT MONERO STUFF HERE"""
# TODO: Alice reconstructs combined private key and has control over the combined account.
combined_private_spend = mu.get_combined_private_key(alice_monero_keys[0][0], recovered_private_key)
print(combined_private_spend)

# Delete Contract...

au.either_deletes_app(app_id, alice_algorand_account)

bob_after = au.get_balance(bob_algorand_account)
alice_after = au.get_balance(alice_algorand_account)