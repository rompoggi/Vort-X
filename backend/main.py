import argparse
import asyncio
from src.test_api_rag import test_rag
from src.test_api_basic import test_basic

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the FastAPI server with optional RAG or basic mode')
    parser.add_argument('-rag', action='store_true', help='Enable RAG mode')
    parser.add_argument('-basic', action='store_true', help='Enable Basic mode')
    args = parser.parse_args()

    if args.rag:
        print("Running in RAG mode")
        asyncio.run(test_rag())
    elif args.basic:
        print("Running in Basic mode")
        asyncio.run(test_basic())
    else:
        print("Running in default mode")
