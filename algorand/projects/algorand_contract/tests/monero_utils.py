import nacl.bindings
from Cryptodome.Hash import keccak
import secrets
from binascii import unhexlify
from monero.base58 import encode


"""
Constants
"""

l = 2 ** 252 + 27742317777372353535851937790883648493 

"""
Python byte manipulation functions
"""

def little_to_big(b, size=32):
    "little endian to big endian"
    return int.from_bytes(b, 'little').to_bytes(size, 'big')

def big_to_little(b, size=32):
    "big endian to little endian"
    return int.from_bytes(b, 'big').to_bytes(size, 'little')

def itb(integer):
    "integer to bytes"
    return (integer).to_bytes(32, 'little')

def bti(b):
    "bytes to integer"
    return int.from_bytes(b, 'little')

"""
Wrappers for the NaCl library (+ Keccak256)
"""

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

def get_pk_from_sk(sk):
    return scalar_to_point(sk)

def get_combined_sk(partial_private_spend_a, partial_private_spend_b):
    return scalar_add(partial_private_spend_a, partial_private_spend_b)

def keccak_sha3(data):
    return keccak.new(digest_bits=256).update(data).digest()


"""
Custom functions for the contract
"""

def generate_leaky_signature(sk, pk, msg):
    """
    Generates a broken signature that leaks the private key, due to the nonce (r) being 1.
    """
    r = itb(1)
    R = scalar_to_point(r)
    challenge = reduce32(nacl.bindings.crypto_hash_sha512(R + pk + msg))
    s = scalar_add(r, scalar_mult(challenge, sk))
    signature = R + s
    return signature

def make_sk_ed25519_appropriate(sk: bytes) -> bytes:
    # Convert to little-endian
    sk_le = big_to_little(sk)
    
    # Clear bits 0, 1, and 2 to 0, clear bit 255 to 0, and set bit 254 to 1
    sk_le = bytearray(sk_le)
    sk_le[0] &= 248  # Clear bits 0, 1, and 2
    sk_le[31] &= 127  # Clear bit 255
    sk_le[31] |= 64   # Set bit 254

    # Convert back to big-endian
    sk = little_to_big(bytes(sk_le))
    return sk

def generate_ed25519_keys(seed_hex=None):
    """
    Generate Ed25519 keys from a seed or randomly.
    """
    
    if seed_hex:
        seed_dec = int(seed_hex, 16)
        sk = little_to_big(itb(seed_dec))
    else:
        sk = itb(secrets.randbits(256) % l)

    sk = make_sk_ed25519_appropriate(sk)
    pk = get_pk_from_sk(sk)
    return sk, pk


def generate_monero_keys(seed_hex=None, env="main"):
    """
    Generate Monero keys from a seed or randomly.
    """
    
    spend_sk, spend_pk = generate_ed25519_keys(seed_hex)

    view_sk = make_sk_ed25519_appropriate((itb(bti(keccak_sha3(spend_sk)) % l)))
    # generate view_sk from spend_sk so we only need to store one key.
    
    view_pk = get_pk_from_sk(view_sk)

    # 18 main chain, 53 test chain, 24 stage chain
    if env == "main":
        prefix = "12" # hex(18)
    elif env == "stage":
        prefix = "18" # hex(24)
    elif env == "test":
        prefix = "35" # hex(53)

    data = prefix + spend_pk.hex() + view_pk.hex()
    checksum = keccak_sha3(bytearray(unhexlify(data)))[:4]
    address = data + checksum.hex()

    return [[spend_sk, spend_pk], [view_sk, view_pk]], encode(address)


