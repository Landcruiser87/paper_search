# -*- coding: utf-8 -*-
import sys
from textual_serve.server import Server

# Using sys.executable guarantees it uses your active Poetry virtualenv
COMMAND = f"{sys.executable} -m paper_search --no-prompt"

def main():
    server = Server(
        command=f"{sys.executable} -m paper_search --no-prompt",
        host="127.0.0.1",
        port=8000,
        title="PaperSearch",
    )
    print("Serving PaperSearch at http://localhost:8000 ...")
    server.serve()

if __name__ == "__main__":
    main()