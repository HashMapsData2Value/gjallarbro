from utils import *

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

    How Schorr signatures work:
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