"""
The entire sequence. Proof-of-Concept.
"""

from algosdk import *
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import *
from algosdk.future.transaction import *

import utils
import contract

KMD_WALLET_NAME = "unencrypted-default-wallet"
KMD_WALLET_PASSWORD = ""
KMD_ADDRESS = "http://localhost:4002"
KMD_TOKEN = "a" * 64

client = AlgodClient("a" * 64, "http://localhost:4001")





# Generate Keys/Accounts

algorand_accounts = utils.get_Algorand_accounts(KMDClient, KMD_TOKEN, KMD_ADDRESS, KMD_WALLET_NAME, KMD_WALLET_PASSWORD)
print(algorand_accounts)

# Build Pyteal & Deploy contract to Algorand


# Alice funds the smart contract


# Bob seeds combined account


# Bob leakily claims the funds to his account


# Alice queries blockchain history & Calculates Bob's partial key and computes combined private key