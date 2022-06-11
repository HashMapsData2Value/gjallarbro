"""
The entire sequence. Proof-of-Concept.
"""

from encodings import utf_8
import importlib, time
import utils as u
import algorand_utils as au
import monero_utils as mu

# Generate Keys/Accounts

algorand_accounts = au.get_Algorand_accounts()
ali_algorand_account = algorand_accounts[0]
bob_algorand_account = algorand_accounts[1]
eve_algorand_account = algorand_accounts[2]

ali_monero_keys = mu.generate_monero_keys() # [0][0] private spend, [0][1] public spend, [1][0] private view, [1][1] public view
bob_monero_keys = mu.generate_monero_keys()

# Build Pyteal & Deploy contract to Algorand

t0 = int(time.time()) + 70
t1 = t0 + 60

approval_teal, clear_teal = au.generate_contract(importlib.import_module('contract'), {
    "alice_addr": ali_algorand_account[0],
    "alice_partial_pk": "0x{}".format(ali_monero_keys[0][1].hex()),
    "bob_addr": bob_algorand_account[0],
    "bob_partial_pk": "0x{}".format(bob_monero_keys[0][1].hex()),
    "t0_timestamp": t0,
    "t1_timestamp": t1,
})

program_hash = au.get_program_hash(approval_teal)

app_index = au.deploy_contract(ali_algorand_account[0], ali_algorand_account[1], approval_teal, clear_teal)


print("Before Bob has:", au.get_balance(bob_algorand_account))

# Alice funds the smart contract
au.fund_contract(app_index, ali_algorand_account, int(500 * 1e6))

# Bob sees the contract and seeds combined account
"""INSERT ALGORAND QUERY HERE"""
"""INSERT MONERO STUFF HERE"""

# Alice queries Monero history (for combined view key)
# -> flags as ready

"""INSERT MONERO STUFF HERE"""

au.alice_set_ready(app_index, ali_algorand_account)

# Bob leakily claims the funds to his account

signature = au.get_signature(bob_algorand_account, bob_monero_keys, program_hash)

au.bob_leaky_claim(app_index, bob_algorand_account, signature)

# Alice queries Algorand history (for signature input)
# -> calculates Bob's partial key and computes combined private key
"""INSERT ALGORAND QUERY HERE"""
"""INSERT MONERO STUFF HERE"""

# Delete Contract

au.either_deletes_app(app_index, ali_algorand_account)

print("After Bob has:", au.get_balance(bob_algorand_account))