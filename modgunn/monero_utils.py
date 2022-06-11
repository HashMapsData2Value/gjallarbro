from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet

import secrets

import utils as u

def generate_monero_keys():
    l = 2 ** 252 + 27742317777372353535851937790883648493 
    # l prime order of the elliptic curve basepoint

    spend_sk = u.itb(secrets.randbits(256) % l)
    view_sk = u.itb(u.bti(u.hash256(spend_sk)) % l)
    # generate view_sk from spend_sk so we only need to store one key.

    spend_pk = u.get_public_from_secret(spend_sk)
    view_pk = u.get_public_from_secret(view_sk)

    return [[spend_sk, spend_pk], [view_sk, view_pk]]


"""
Tests just to check that things work
"""


def test_keys():
    """
    Test that the generated keys can actually be added with each other.
    """

    alice = generate_monero_keys()
    bob = generate_monero_keys()

    keys1 = [alice[0][0], alice[0][1]]
    keys2 = [bob[0][0], bob[0][1]]


    #print('sec1 + sec2 = sec', scalar_add(keys1[0], keys2[0]).hex())
    #print('pub1 + pub2 = pub', points_add(keys1[1], keys2[1]).hex())
    #print('toPub(sec)  = pub', get_public_from_secret(scalar_add(keys1[0], keys2[0])).hex())
    assert u.points_add(keys1[1], keys2[1]) == u.get_public_from_secret(u.scalar_add(keys1[0], keys2[0]))


#def generate_from_keys_rpc_test(...):
    # use "generate_from_keys" Monero Wallet RPC call to generate from keys. 
    #w1 = Wallet(JSONRPCWallet(port=28088))
    #w2 = Wallet(JSONRPCWallet(port=38088))
    #add pub spend and view keys together
    #once partial private key leaked, generate_from_keys


def build_monero_address(): 
    
    network_bytes = 53# 18 main chain, 53 test chain, 24 stage chain
    data = (
        bytearray([network_bytes])
        + self._decoded[1:65]
    )

    checksum = u.hash256(data)[:4]
    pass

def get_combined_private_key(partial_private_spend_a, partial_private_spend_b):
    return u.scalar_add(partial_private_spend_a, partial_private_spend_b)

if __name__ == '__main__':
    test_keys()