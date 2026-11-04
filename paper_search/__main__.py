# -*- coding: utf-8 -*-

from __future__ import annotations
import argparse
import logging
import platform
import sys

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

from .support import logger, launch_tui
from .app import PaperSearch
from . import __prog_name__, __version__

WINDOWS = platform.system() == "Windows"
DEBUGPY_PORT = 5678

def main():
    parser = argparse.ArgumentParser(
        prog=__prog_name__, description="PaperSearch. Exploring high quality machine learning papers", epilog=f"v{__version__}"
    )

    parser.add_argument(
        "-V",
        "--version",
        help="Show version information.",
        action="version",
        version=f"%(prog)s {__version__} (Textual v{importlib_metadata.version( 'textual' )})",
    )

    parser.add_argument(
        "--log", nargs="?", help="Log level for enable debugpy", default="INFO"
    )

    parser.add_argument(
        "path",
        nargs="?",
        type=argparse.FileType(encoding="utf-8", mode="r"),
        metavar="PATH",
        help="path to file, or stdin",
        default=sys.stdin,
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip the dataset selection prompt and start with an empty workspace.",
    )
    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        logger.warning(f"Invalid log level {args.log!r}")
    file_choice = ""
    # Check if no path was provided as a command-line argument
    if args.path is sys.stdin:
        if not args.no_prompt and sys.stdin.isatty():
            file_choice = launch_tui()
            if file_choice:
                try:
                    args.path = open(file_choice, mode="r", encoding="utf-8")
                except Exception as e:
                    logger.error(f"Error opening file {file_choice}: {e}")
                    sys.exit(1)
            else:
                args.path = None
        else:
            args.path = None
    
    try:
        # See:Textualize/textual/issues/153#issuecomment-1256933121
        if not WINDOWS:
            sys.stdin = open("/dev/tty", "r")

        app = PaperSearch(args.path)
        app.run()

        if not sys.stdin.closed:
            sys.stdin.close()

    except Exception as error:
        logger.warning(f"Unable to read {args.path!r}; {error}")
        sys.exit(-1)

if __name__ == "__main__":
    main()