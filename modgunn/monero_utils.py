from monero.wallet import Wallet
from monero.daemon import Daemon

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

def generate_from_keys(wallet_filename, address, spendkey, viewkey, pw):
    """ Example from https://www.getmonero.org/resources/developer-guides/wallet-rpc.html#generate_from_keys
    curl -X POST http://127.0.0.1:18082/json_rpc -d '
        {
            "jsonrpc":"2.0",
            "id":"0",
            "method":"generate_from_keys",
            "params"= {
                "restore_height":0,
                "filename":"wallet_name",
                "address":"42gt8cXJSHAL4up8XoZh7fikVuswDU7itAoaCjSQyo6fFoeTQpAcAwrQ1cs8KvFynLFSBdabhmk7HEe3HS7UsAz4LYnVPYM",
                "spendkey":"11d3fd247672c4cb29b6e38791dcf07629cd2d68d868f0b78811ce584a6b0d01",
                "viewkey":"97cf64f2cd6c930242e9bed5f14f8f16a33047229aca3eababf4af7e8d113209",
                "password":"pass",
                "autosave_current":true
            }
        },' -H 'Content-Type: application/json'
    """
    
    w1 = Wallet()
    result = w1.raw_request(method="generate_from_keys", params={
            "restore_height": 0,
            "filename":wallet_filename,
            "address":address,
            "spendkey":spendkey,
            "viewkey":viewkey,
            "password":pw,
        })
    
    return result

def get_combined_private_key(partial_private_spend_a, partial_private_spend_b):
    return u.scalar_add(partial_private_spend_a, partial_private_spend_b)

def build_monero_address(): 
    
    network_bytes = 53# 18 main chain, 53 test chain, 24 stage chain
    data = (
        bytearray([network_bytes])
        + self._decoded[1:65]
    )

    checksum = u.hash256(data)[:4]
    pass

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

if __name__ == '__main__':
    test_keys()