from argparse import ArgumentParser
import sys, os
import utils


if __name__ == "__main__":
    parser = ArgumentParser(description="Modgunn Algorand actions")

    subparser = parser.add_subparsers(dest="command")

    generate_parser = subparser.add_parser("generate", help="generate TEAL code from specified contract")
    generate_parser.add_argument("-c", "--contract", help="specify folder under contracts")
    generate_parser.add_argument("-aaa", "--alice_algo_address", help="specify Alice's Algorand address")
    generate_parser.add_argument("-aed", "--alice_ed25519_pubkey", help="specify Alice's Partial Pubkey on other ed25519 chain")
    generate_parser.add_argument("-baa", "--bob_algo_address", help="specify Bob's Algorand address")
    generate_parser.add_argument("-bed", "--bob_ed25519_pubkey", help="specify Bob's Partial Pubkey on other ed25519 chain")

    list_parser = subparser.add_parser("list", help="list folders under contracts")

    args = parser.parse_args()

    if args.command == "generate":
        if args.contract:
            program_hash = utils.generate_contract(args.contract, {
                "TMPL_ALICE_ALGO_ADDRESS": args.alice_algo_address,
                "TMPL_ALICE_PARTIAL_PK": args.alice_ed25519_pubkey,
                "TMPL_BOB_ALGO_ADDRESS": args.bob_algo_address,
                "TMPL_BOB_PARTIAL_PK": args.bob_ed25519_pubkey,
            })
            print(program_hash)
    if args.command == "list":
        print(utils.list_contracts())