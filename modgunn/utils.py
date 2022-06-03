import secrets
import nacl.bindings, nacl.signing
from Cryptodome.Hash import keccak

from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet



"""
GENERAL UTILS
"""

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


"""
ALGORAND UTILS
"""



def get_Algorand_accounts(KMDClient, KMD_TOKEN, KMD_ADDRESS, KMD_WALLET_NAME, KMD_WALLET_PASSWORD): #h ttps://github.com/algorand-devrel/decipher-drop
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






"""
Tests just to check that things work
"""


def test_keys():
    """
    Test that the generated keys can actually be added with each other.
    """

    alice = generate_keys()
    bob = generate_keys()

    keys1 = [alice[0][0], alice[0][1]]
    keys2 = [bob[0][0], bob[0][1]]


    #print('sec1 + sec2 = sec', scalar_add(keys1[0], keys2[0]).hex())
    #print('pub1 + pub2 = pub', points_add(keys1[1], keys2[1]).hex())
    #print('toPub(sec)  = pub', get_public_from_secret(scalar_add(keys1[0], keys2[0])).hex())
    assert points_add(keys1[1], keys2[1]) == get_public_from_secret(scalar_add(keys1[0], keys2[0]))


#def generate_from_keys_rpc_test(...):
    # use "generate_from_keys" Monero Wallet RPC call to generate from keys. 
    #w1 = Wallet(JSONRPCWallet(port=28088))
    #w2 = Wallet(JSONRPCWallet(port=38088))
    #add pub spend and view keys together
    #once partial private key leaked, generate_from_keys



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
    keys = generate_keys()
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

    keys = generate_keys()
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



if __name__ == '__main__':
    test_keys()
    test_extract_private_key_own_signing()
    test_extract_private_key_import_verify()
