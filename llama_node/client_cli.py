import argparse
import sys
import httpx
import json

API_URL = "http://127.0.0.1:8000/query"

def query_rag(question: str) -> str:
    try:
        resp = httpx.post(API_URL, json={"query": question})
        resp.raise_for_status()
        data = resp.json()
        return data.get("answer", "<no answer>")
    except Exception as e:
        return f"Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="CLI client for Owlbearag LlamaIndex RAG node")
    parser.add_argument("question", nargs="?", help="Question to ask the RAG service")
    args = parser.parse_args()

    if args.question:
        answer = query_rag(args.question)
        print(answer)
    else:
        # Interactive mode
        print("Enter your query (type 'exit' to quit):")
        while True:
            try:
                line = input("> ")
            except EOFError:
                break
            if line.lower() in {"exit", "quit"}:
                break
            if not line.strip():
                continue
            print(query_rag(line))

if __name__ == "__main__":
    main()
