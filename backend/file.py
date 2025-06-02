import argparse
import os

FILENAME = "document.txt"

def create_file():
    if os.path.exists(FILENAME):
        print(f"{FILENAME} already exists. Exiting.")
        return
    with open(FILENAME, "w") as f:
        pass  # Create an empty file
    print(f"{FILENAME} created.")

def open_file():
    if not os.path.exists(FILENAME):
        print(f"{FILENAME} does not exist.")
        return
    with open(FILENAME, "r") as f:
        content = f.read()
    print(content)

def main():
    parser = argparse.ArgumentParser(description="Create or open document.txt")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", action="store_true", help="Create document.txt if it does not exist")
    group.add_argument("-o", action="store_true", help="Open and print document.txt")
    args = parser.parse_args()

    if args.c:
        create_file()
    elif args.o:
        open_file()

if __name__ == "__main__":
    main()
