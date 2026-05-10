from argparse import ArgumentParser
from pathlib import Path
import shutil


def add_parser(subparsers):
    parser = subparsers.add_parser("sync", help="Synchronisation Obsidian / kintone / GitHub")
    action_sub = parser.add_subparsers(dest="action", required=True)
    p = action_sub.add_parser("obsidian", help="Copie les exports dans un vault Obsidian")
    p.add_argument("--vault", required=True)
    p.add_argument("--input", default="exports")
    p = action_sub.add_parser("kintone", help="Prépare un payload pour cli-kintone / MCP kintone")
    p.add_argument("--table", required=True)
    p.add_argument("--input", default="exports")
    parser.set_defaults(handler=run)


def run(args):
    if args.action == "obsidian":
        src = Path(args.input)
        dst = Path(args.vault)
        dst.mkdir(parents=True, exist_ok=True)
        copied = 0
        for f in src.glob("*.md"):
            shutil.copy2(f, dst / f.name)
            copied += 1
        print(f"Fichiers Markdown copiés vers Obsidian: {copied}")
    elif args.action == "kintone":
        out = Path(args.input) / f"kintone_{args.table}_payload.todo.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# Payload kintone à implémenter\n\nUtiliser cli-kintone ou kintone/mcp-server pour pousser les records validés.\n", encoding="utf-8")
        print(f"Payload kintone préparé: {out}")
