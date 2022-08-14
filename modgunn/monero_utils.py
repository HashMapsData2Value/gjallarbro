from distutils.command import build
from binascii import unhexlify
from monero.wallet import Wallet
from monero.daemon import Daemon
from monero.base58 import encode

import secrets

import utils as u

def generate_monero_keys(seed_hex=None, env="main"):
    l = 2 ** 252 + 27742317777372353535851937790883648493 
    # l prime order of the elliptic curve basepoint

    if seed_hex:
        seed_dec = int(seed_hex, 16)
        spend_sk = u.little_to_big(u.itb(seed_dec))
    else:
        spend_sk = u.itb(secrets.randbits(256) % l)
#    print(u.little_to_big(spend_sk).hex())

    view_sk = u.itb(u.bti(u.hash256(spend_sk)) % l)
    # generate view_sk from spend_sk so we only need to store one key.

    spend_pk = u.get_public_from_secret(spend_sk)
    view_pk = u.get_public_from_secret(view_sk)


    # 18 main chain, 53 test chain, 24 stage chain
    if env == "main":
        prefix = "12" # hex(18)
    elif env == "stage":
        prefix = "18" # hex(24)
    elif env == "test":
        prefix = "35" # hex(53)

    data = prefix + spend_pk.hex() + view_pk.hex()
    checksum = u.hash256(bytearray(unhexlify(data)))[:4]
    address = data + checksum.hex()

    return [[spend_sk, spend_pk], [view_sk, view_pk]], encode(address)

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

"""
Tests just to check that things work
"""

def test_monero_address():
    private_spend_key = "39c4b3cc4fa2ccad647990f67e8d84b611d5a15d53225213cc42783f227c4909"
    private_view_key = "a86be8c70784ec97a8c8d45212b1ea356759ef1ff1a0983190351c62b14b3500"
    public_spend_key = "ca5f63d230d44e6b3420edd2e797e2a18d5fb98e59dc594c02c4fac6441519f8"
    public_view_key = "f070076aa7ccf42db141bbf6dfe6131409e34a99766dc5f3db407028efeca65c"
    correct_address = "49HupRMMmXsJw1YshMsNJ5U2G2fSCdpu6DiQD7KE9NwSie2HZjD7hBZ8eGsQw2rvQr4MQBngHjNRrhniMht6xzkVBVFTY3M"

    keys, address = generate_monero_keys(seed_hex=private_spend_key)

    assert keys[0][0].hex() == private_spend_key
    assert keys[0][1].hex() == public_spend_key
    assert keys[1][0].hex() == private_view_key
    assert keys[1][1].hex() == public_view_key
    assert address == correct_address




def test_keys_addition():
    """
    Test that the generated keys can actually be added with each other.
    """

    alice, _ = generate_monero_keys()
    bob, _ = generate_monero_keys()

    keys1 = [alice[0][0], alice[0][1]]
    keys2 = [bob[0][0], bob[0][1]]

    assert u.points_add(keys1[1], keys2[1]) == u.get_public_from_secret(u.scalar_add(keys1[0], keys2[0]))

if __name__ == '__main__':
    test_keys_addition()
    test_monero_address()