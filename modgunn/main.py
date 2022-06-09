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


approval_teal, clear_teal = au.generate_contract(importlib.import_module('contract'), {
    "TMPL_ALICE_ALGO_ADDRESS": ali_algorand_account[0],
    "TMPL_ALICE_PARTIAL_PK": ali_monero_keys[0][1],
    "TMPL_BOB_ALGO_ADDRESS": bob_algorand_account[0],
    "TMPL_BOB_PARTIAL_PK": bob_monero_keys[0][1],
})

program_hash = au.get_program_hash(approval_teal)
signature = u.get_signature(bob_monero_keys, bytes(program_hash, "utf-8"))
print(signature)

t0 = int(time.time()) + 60
t1 = t0 + 60

app_index = au.deploy_contract(ali_algorand_account[0], ali_algorand_account[1], approval_teal, clear_teal, [t0, t1])



# Alice funds the smart contract
print(au.fund_contract(app_index, ali_algorand_account, int(500 * 1e6)))

# Bob sees the contract and seeds combined account
"""INSERT ALGORAND QUERY HERE"""
"""INSERT MONERO STUFF HERE"""

# Alice queries Monero history (for combined view key)
# -> flags as ready

"""INSERT MONERO STUFF HERE"""

print(au.alice_set_ready(app_index, ali_algorand_account))

# Bob leakily claims the funds to his account


print(au.bob_leaky_claim(app_index, bob_algorand_account, signature.hex()))

# Alice queries Algorand history (for signature input)
# -> calculates Bob's partial key and computes combined private key
"""INSERT ALGORAND QUERY HERE"""
"""INSERT MONERO STUFF HERE"""

# Delete Contract

print(au.either_deletes_app(app_index, ali_algorand_account))