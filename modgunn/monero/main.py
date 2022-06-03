from argparse import ArgumentParser
from ast import arg
from utils import *

def get_signature(private_key, public_key, program_hash):
    r = itb(1)
    R = scalar_to_point(r)

    msg = str.encode("ProgData") + str.encode(program_hash) + str.encode("gjallarbro")
    sec = bytes.fromhex(private_key)
    pub = bytes.fromhex(public_key)
    s = scalar_add(r, scalar_mult(reduce32(nacl.bindings.crypto_hash_sha512(R + pub + msg)), sec))
    assert scalar_to_point(s) == points_add(R, scalar_mult_point(reduce32(nacl.bindings.crypto_hash_sha512(R + pub + msg)), pub))
    
    return R+s

def get_new_keys():
    keys = generate_keys()
    return keys[0][0], keys[0][1]


if __name__ == '__main__':
    parser = ArgumentParser(description="Modgunn Monero actions")

    subparser = parser.add_subparsers(dest="command")

    signature_parser = subparser.add_parser("signature", help="generate R, s")
    signature_parser.add_argument("-p", "--public", help="specify public key")
    signature_parser.add_argument("-s", "--private", help="specify private key")
    signature_parser.add_argument("-H", "--hash", help="specify program hash")

    new_keys = subparser.add_parser("keys", help="get keys")
    new_keys.add_argument("-n", "--new", help="generates new ed25519 keys, prints private (scalar) and public (point)")
    args = parser.parse_args()

    if args.command == "signature":
        Rs = get_signature(private_key = args.private, public_key=args.public, program_hash=args.hash)
        print(Rs.hex())

    if args.command == "keys":
        private_spend, public_spend = get_new_keys()
        print(private_spend.hex(), public_spend.hex())