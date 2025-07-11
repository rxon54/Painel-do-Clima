import sys
import tiktoken
import os

def count_tokens(file_path, model="gpt-4"):
    # Load the appropriate tokenizer for the model
    encoding = tiktoken.encoding_for_model(model)

    # Read file content
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Tokenize and count
    tokens = encoding.encode(text)
    token_count = len(tokens)

    print(f"Model: {model}")
    print(f"File: {file_path}")
    print(f"Token count: {token_count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_tokens.py <path-to-text-file> [model]")
    else:
        file_path = sys.argv[1]
        model = sys.argv[2] if len(sys.argv) > 2 else "gpt-4"
        count_tokens(file_path, model)

