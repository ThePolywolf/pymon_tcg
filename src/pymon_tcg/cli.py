import argparse
from .build_data import build

def main():
    parser = argparse.ArgumentParser(description="Pymon TCG Toolkit")
    subparsers = parser.add_subparsers(dest="command")

    fetch_parser = subparsers.add_parser("fetch", help="Download required TCG data from database")

    args = parser.parse_args()

    if args.command == "fetch":
        print("Starting data download...")
        print("-------")
        build()
        print("-------")
        print("FETCH complete")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()