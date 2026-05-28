# -*- coding: utf-8 -*-

from textual_serve.server import Server
fp = "poetry run python tui/__main__.py"
pub_url = "https://www.andypapersearch.com"
server = Server(
    command = f"{fp}",
    # host="0.0.0.0",        # Serve on all interfaces so the proxy can reach it
    # port=8000,             # The port the proxy should target
    title = "PaperSearch", # Application Title
    # public_url=pub_url     # URL 
)

server.serve()
