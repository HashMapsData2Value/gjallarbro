"""
ALGORAND UTILS
"""

import os, base64
import pyteal

from algosdk import *
from algosdk.logic import get_application_address
from algosdk.kmd import KMDClient
from algosdk.v2client import algod, indexer
from algosdk.future import transaction

algod_client = algod.AlgodClient("a" * 64, "http://localhost:4001")
algo_indexer = indexer.IndexerClient("a" * 64, "http://localhost:8980")


def get_Algorand_accounts(): #h ttps://github.com/algorand-devrel/decipher-drop 
    KMD_TOKEN = "a" * 64
    KMD_ADDRESS="http://localhost:4002"
    KMD_WALLET_NAME="unencrypted-default-wallet"
    KMD_WALLET_PASSWORD=""
    
    
    kmd = KMDClient(KMD_TOKEN, KMD_ADDRESS)
    wallets = kmd.list_wallets()

    walletID = None
    for wallet in wallets:
        if wallet["name"] == KMD_WALLET_NAME:
            walletID = wallet["id"]
            break

    if walletID is None:
        raise Exception("Wallet not found: {}".format(KMD_WALLET_NAME))

    walletHandle = kmd.init_wallet_handle(walletID, KMD_WALLET_PASSWORD)

    try:
        addresses = kmd.list_keys(walletHandle)
        privateKeys = [
            kmd.export_key(walletHandle, KMD_WALLET_PASSWORD, addr)
            for addr in addresses
        ]
        kmdAccounts = [(addresses[i], privateKeys[i]) for i in range(len(privateKeys))]
    finally:
        kmd.release_wallet_handle(walletHandle)

    return kmdAccounts


def application(pyteal_code):
    return pyteal.compileTeal(pyteal_code, mode=pyteal.Mode.Application, version=pyteal.MAX_TEAL_VERSION)

def populate_teal(source, input):
    for key in input:
        source = source.replace(key, "{}".format(input[key]))
    return source

def generate_contract(contract, input_approval, input_clear = {}):
    if not os.path.exists("build"):
        os.makedirs("build")

    a = populate_teal(application(contract.approval()), input_approval)
    c = populate_teal(application(contract.clear()), input_clear)
    with open(os.path.join("build", "approval.teal"), "w") as h:
        a = populate_teal(application(contract.approval()), input_approval)
        h.write(a)

    with open(os.path.join("build", "clear.teal"), "w") as h:
        h.write(populate_teal(application(contract.clear()), input_clear))

    return a, c

def get_program_hash(src):
    return algod_client.compile(src)['hash']

def execute_transaction(txn, private_Key):
    signed_txn = txn.sign(private_Key)

    txid = algod_client.send_transaction(signed_txn)

    result = transaction.wait_for_confirmation(algod_client, txid, 4)
    return result

def execute_group_transaction(txns, private_key):
    stxns = []
    for txn in txns:
        stxns.append(txn.sign(private_key))

    tx_id = algod_client.send_transactions(stxns)

    result = transaction.wait_for_confirmation(algod_client, tx_id, 10)
    return result


def deploy_contract( # https://github.com/algorand-devrel/demo-avm1.1/blob/master/demos/utils/deploy.py
    addr: str, pk: str, approval_teal, clear_teal, timestamps: list,
) -> int:
    # Get suggested params from network
    sp = algod_client.suggested_params()

    # Read in approval teal source && compile
    app_result = algod_client.compile(approval_teal)
    app_bytes = base64.b64decode(app_result["result"])

    # Read in clear teal source && compile
    clear_result = algod_client.compile(clear_teal)
    clear_bytes = base64.b64decode(clear_result["result"])

    # We do need some stinkin storage
    g_schema = transaction.StateSchema(4, 3)
    l_schema = transaction.StateSchema(0, 0)

    # Create the transaction
    create_txn = transaction.ApplicationCreateTxn(
        addr,
        sp,
        0,
        app_bytes,
        clear_bytes,
        g_schema,
        l_schema,
        app_args=timestamps
    )

    result = execute_transaction(create_txn, pk)


    #print(result)
    return result["application-index"]

def fund_contract(app_id, account, amount):
    
    app_addr = get_application_address(app_id)
    sp = algod_client.suggested_params()

    create_txn = transaction.PaymentTxn(account[0], sp, app_addr, amount)

    result = execute_transaction(create_txn, account[1])
    return result


def alice_set_ready(app_id, account):

    sp = algod_client.suggested_params()

    create_txn = transaction.ApplicationCallTxn(
        sender=account[0],
        sp=sp,
        index=app_id,
        app_args=[b"ready"],
        on_complete=transaction.OnComplete.NoOpOC,       
    )

    result = execute_transaction(create_txn, account[1])
    return result

def bob_leaky_claim(app_id, account, input):

    sp = algod_client.suggested_params()

    leaky_claim_txn = transaction.ApplicationCallTxn(
        sender=account[0],
        sp=sp,
        index=app_id,
        app_args=[b"leaky_claim"],
        note=input,
        on_complete=transaction.OnComplete.NoOpOC,       
    )

    add_700_txn_1 = transaction.ApplicationCallTxn(
        sender=account[0],
        sp=sp,
        index=app_id,
        app_args=[b"+700"],
        note=input,
        on_complete=transaction.OnComplete.NoOpOC,       
    )

    add_700_txn_2 = transaction.ApplicationCallTxn(
        sender=account[0],
        sp=sp,
        index=app_id,
        app_args=[b"+700"],
        note=input,
        on_complete=transaction.OnComplete.NoOpOC,       
    )

    groupTxnId = transaction.calculate_group_id([leaky_claim_txn, add_700_txn_1, add_700_txn_2])

    leaky_claim_txn.group = groupTxnId
    add_700_txn_1.group = groupTxnId
    add_700_txn_2.group = groupTxnId

    result = execute_group_transaction([leaky_claim_txn, add_700_txn_1, add_700_txn_2], account[1])
    return result

# def bob_leaky_claim(app_id, account, input):

#     sp = algod_client.suggested_params()

#     create_txn = transaction.ApplicationCallTxn(
#         sender=account[0],
#         sp=sp,
#         index=app_id,
#         app_args=[b"leaky_claim"],
#         note=input,
#         on_complete=transaction.OnComplete.NoOpOC,       
#     )

#     signed_txn = create_txn.sign(account[1])

#     drr = transaction.create_dryrun(algod_client, [signed_txn])

#     filename = "dryrun.msgp"
#     with open(filename, "wb") as f:
#         f.write(base64.b64decode(encoding.msgpack_encode(drr)))

#     txid = algod_client.send_transaction(signed_txn)

#     result = transaction.wait_for_confirmation(algod_client, txid, 4)
#     return result

def either_deletes_app(app_id, account):
    
    sp = algod_client.suggested_params()

    create_txn =transaction.ApplicationDeleteTxn(
        sender=account[0],
        sp=sp,
        index=app_id
    )
    
    result = execute_transaction(create_txn, account[1])
    return result
