import argparse
from mangatracker_cli import __version__
from mangatracker_cli.commands import manga, ln, anime, seiyu, studio, game, goods, events, sync, audit


def build_parser():
    parser = argparse.ArgumentParser(prog="mangatracker", description="CLI Japan-Alliance / MangaTracker")
    parser.add_argument("--version", action="version", version=f"mangatracker {__version__}")
    subparsers = parser.add_subparsers(dest="module", required=True)
    for mod in [manga, ln, anime, seiyu, studio, game, goods, events, sync, audit]:
        mod.add_parser(subparsers)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)

if __name__ == "__main__":
    main()
