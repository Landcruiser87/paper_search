from textual_serve.server import Server
fp = "poetry run python tui\__main__.py"
server = Server(
    command = f"{fp}",
    title = "PaperSearch",
    # public_url= "https://www.andypapersearch.com"
)
server.serve()
