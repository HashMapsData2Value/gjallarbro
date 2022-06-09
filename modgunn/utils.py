import nacl.bindings, nacl.signing
from Cryptodome.Hash import keccak

import monero_utils

"""
GENERAL UTILS
"""

def little_to_big(b, size=32):
    return (int.from_bytes(b, 'little')).to_bytes(size, 'big')

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




####
def test_extract_private_key_own_signing():
    """
    If you can understand this you understand the protocol.

    How Schnorr signatures work:
    s == r + hash(R|C|msg)*c
    sG == R + hash(R|C|msg)*C
    R|s (| concat) is the signature.
    c and C are the private respectively public key.
    msg is the message we are signing.

    If Algorand exposed ed25519 scalarmult as an opcode, it would be trivial to check.
    It doesn't, but it does expose ed25519verify. We can hack it to our favor. 
    If we force r = 1 (r = 0 seems to not be allowed by nacl :C):

    s == 1 + hash(G|C|msg)*c
    s - 1 == hash(G|C|msg)*c
    (s - 1)*hash(R|C|msg)^-1 == c

    The smart contract can ensure that R really is 1G, in which case s - 1 must
    be the hash(R|C|msg)*c. Since we know R, we know C and we know msg, we can calculate the
    hash and take its multiplicative inverse with s to produce the scalar c, i.e. private key.

    (Note that ed25519verify sees msg as b'progData'| program_hash | data. The new 
    ed25519verify_bare will not require those things.) 

    """
    keys = monero_utils.generate_monero_keys()
    c = keys[0][0] # private key
    C = keys[0][1] # public key

    msg = b"ProgData" + b"programhash" + b"data_A"

    r = itb(1) #We fixate r = 1
    R = scalar_to_point(r)

    challenge = reduce32(nacl.bindings.crypto_hash_sha512(R + C + msg))

    s = scalar_add(r, scalar_mult(challenge, c)) # s == r + hash(...)*c
    sG = scalar_to_point(s)

    # sG == R + hash(...)*C
    right_hand_side = points_add(R, scalar_mult_point(challenge, C)) 
    assert(sG == right_hand_side)

    # (s-r)*hash(...)^-1 == c
    c_extracted = scalar_division(scalar_sub(s, r), challenge)
    assert c == c_extracted

def test_extract_private_key_import_verify():
    """
    Instead of verifying using "math", we verify against libsodium's verification func.
    """

    keys = monero_utils.generate_monero_keys()
    c = keys[0][0]
    C = keys[0][1]
    
    msg = b"ProgData" + b"programhash" + b"data_A"
    r = itb(1)
    R = scalar_to_point(r)
    challenge = reduce32(nacl.bindings.crypto_hash_sha512(R + C + msg))
    s = scalar_add(r, scalar_mult(challenge, c))
    signature = R + s
    smessage = signature + msg
    # crypto_sign_open returns msg IF it the signature is right, otherwise raises error
    assert msg == nacl.bindings.crypto_sign_open(smessage, C)


def get_signature(monero_keys, programhash):

    c = monero_keys[0][0]
    C = monero_keys[0][1]

    msg = b"ProgData" + programhash + b"gjallarbro"
    r = itb(1)
    R = scalar_to_point(r)
    challenge = reduce32(nacl.bindings.crypto_hash_sha512(R + C + msg))
    s = scalar_add(r, scalar_mult(challenge, c))
    signature = little_to_big(R) + little_to_big(s)
    return signature


if __name__ == '__main__':
    test_extract_private_key_own_signing()
    test_extract_private_key_import_verify()
