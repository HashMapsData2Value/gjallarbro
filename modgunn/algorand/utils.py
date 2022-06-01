import os, importlib

import pyteal
import algosdk.v2client.algod as algod

algod_token = "a" * 64
algod_url = "http://localhost:4001"

def application(pyteal_code):
    return pyteal.compileTeal(pyteal_code, mode=pyteal.Mode.Application, version=pyteal.MAX_TEAL_VERSION)

def populate_teal(source, input):
    for key in input:
        source = source.replace(key, "\"{}\"".format(input[key]))
    return source

def generate_contract(contract_name, input_approval, input_clear = {}):
    contract = importlib.import_module('contracts.{}.contract'.format(contract_name))

    if not os.path.exists("build"):
        os.makedirs("build")

    with open(os.path.join("build", "approval.teal"), "w") as h:
        a = populate_teal(application(contract.approval()), input_approval)
        h.write(a)

    with open(os.path.join("build", "clear.teal"), "w") as h:
        h.write(populate_teal(application(contract.clear()), input_clear))
    
    return algod.AlgodClient(algod_token, algod_url).compile(source=a)['hash']
def list_contracts():
    return os.listdir('contracts')
