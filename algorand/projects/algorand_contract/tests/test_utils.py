from tests.utils import *


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
    If we force r = 1:

    s == 1 + hash(R|C|msg)*c
    s - 1 == hash(R|C|msg)*c
    (s - 1)*hash(R|C|msg)^-1 == c

    The smart contract can ensure that R really is 1G, in which case s - 1 must
    be the hash(R|C|msg)*c. Since we know R, we know C and we know msg, we can calculate the
    hash and take its multiplicative inverse with s to produce the scalar c, i.e. private key.

    (Note that ed25519verify sees msg as b'progData'| program_hash | data. The new 
    ed25519verify_bare will not require those things.) 

    """
    # keys, _ = generate_monero_keys()
    # c = keys[0][0] # private spend keyx
    # C = keys[0][1] # public spend key

    c, C = generate_ed25519_keys()

    msg = b"ProgData" + b"programhash" + b"data_A"

    r = itb(1) #We fixate r = 1
    R = scalar_to_point(r)

    challenge = reduce32(nacl.bindings.crypto_hash_sha512(R + C + msg))

    s = scalar_add(r, scalar_mult(challenge, c)) # s == r + hash(...)*c
    sG = scalar_to_point(s)

    # The equivalent of doing a signature verification:
    # sG == R + hash(...)*C
    right_hand_side = points_add(R, scalar_mult_point(challenge, C)) 
    assert(sG == right_hand_side)

    # (s-r)*hash(...)^-1 == c
    c_extracted = scalar_division(scalar_sub(s, r), challenge)
    
    # Logging for debugging
    print(f"Original private key: {c.hex()}")
    print(f"Xtracted private key: {c_extracted.hex()}")
    print(f"s: {s.hex()}")
    print(f"r: {r.hex()}")
    print(f"challenge: {challenge.hex()}")

    assert c == c_extracted

def test_verify_sig_recognized_by_libsodium():
    """
    We verify that the signature is recognized by the libsodium package.
    """

    keys, _ = generate_monero_keys()
    c = keys[0][0]
    C = keys[0][1]
    
    msg = (b"ProgData" + b"programhash" + b"data_A")
    r = itb(1)
    R = scalar_to_point(r)
    challenge = reduce32(nacl.bindings.crypto_hash_sha512(R + C + msg))
    s = scalar_add(r, scalar_mult(challenge, c))
    signature = R + s
    smessage = signature + msg
    # crypto_sign_open returns msg IF it the signature is right, otherwise raises error
    assert msg == nacl.bindings.crypto_sign_open(smessage, C)

def test_monero_address():
    private_spend_key = "78c4b3cc4fa2ccad647990f67e8d84b611d5a15d53225213cc42783f227c4948"
    private_view_key = "7075bf8708639cdaaadefa89f0de2966a8061dd75777ef83e0be7bc4e3c6a108"
    public_spend_key = "ac18b8fedc504ab032a95bed75bb2a0b7c5a29df605191f9a987232dd8e25701"
    public_view_key = "7138b258606f682e86d922e99ac4ea679edb18687f7263ea22db1d1cc0cd5a32"
    correct_address = "489NDGyUxkyWULjp51d7Ld2vRidw8oDcLim36yAdU2jQ1EzXYgnpm598nNLAA7bq5sJLFSTduyb1UgAR1hzUWeZF6fnybm2"

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

    assert points_add(alice[0][1], bob[0][1]) == get_pk_from_sk(scalar_add(alice[0][0], bob[0][0]))
    assert points_add(alice[1][1], bob[1][1]) == get_pk_from_sk(scalar_add(alice[1][0], bob[1][0]))
