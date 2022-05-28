import secrets
import nacl.bindings, nacl.signing
from Cryptodome.Hash import keccak

from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet


def itb(integer):
    return (integer).to_bytes(32, 'little')

def bti(b):
    return int.from_bytes(b, 'little')

def reduce32(b):
    try:
        return nacl.bindings.crypto_core_ed25519_scalar_reduce(b)
    except Exception as e:
        print(e)
        return b

def validate(point):
    return nacl.bindings.crypto_core_ed25519_is_valid_point(point)

def scalar_add(scalar_a, scalar_b):
    return nacl.bindings.crypto_core_ed25519_scalar_add(scalar_a, scalar_b)

def scalar_sub(scalar_a, scalar_b):
    return nacl.bindings.crypto_core_ed25519_scalar_sub(scalar_a, scalar_b)

def scalar_mult(scalar_a, scalar_b):
    return nacl.bindings.crypto_core_ed25519_scalar_mul(scalar_a, scalar_b)

def scalar_division(scalar_a, scalar_b):
    return scalar_mult(scalar_a, nacl.bindings.crypto_core_ed25519_scalar_invert(scalar_b))

def points_add(point_a, point_b):
    return nacl.bindings.crypto_core_ed25519_add(point_a, point_b)

def scalar_to_point(scalar):
    return nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(scalar)

def scalar_mult_point(scalar, point):
    return nacl.bindings.crypto_scalarmult_ed25519_noclamp(scalar, point)

def hash256(data):
    return keccak.new(digest_bits=256).update(data).digest()  

def get_public_from_secret(sk):
    return scalar_to_point(sk)

def generate_keys():
    l = 2 ** 252 + 27742317777372353535851937790883648493 
    # l prime order of the elliptic curve basepoint

    spend_sk = itb(secrets.randbits(256) % l)
    view_sk = itb(bti(hash256(spend_sk)) % l)
    # generate view_sk from spend_sk so we only need to store one key.

    spend_pk = get_public_from_secret(spend_sk)
    view_pk = get_public_from_secret(view_sk)

    return [[spend_sk, spend_pk], [view_sk, view_pk]]

def build_monero_address(): 
    
    network_bytes = 53# 18 main chain, 53 test chain, 24 stage chain
    data = (
        bytearray([network_bytes])
        + self._decoded[1:65]
    )

    checksum = hash256(data)[:4]
    pass