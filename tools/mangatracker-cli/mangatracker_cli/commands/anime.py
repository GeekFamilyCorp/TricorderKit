from argparse import ArgumentParser
from mangatracker_cli.core.registry import get_source
from mangatracker_cli.core.exporter import export_json, export_markdown
from mangatracker_cli.connectors.parsers import placeholder_record

CATEGORY = "anime"


def add_parser(subparsers):
    parser = subparsers.add_parser("anime", help="Veille anime JP")
    action_sub = parser.add_subparsers(dest="action", required=True)
    p = action_sub.add_parser("scan-news", help="Scan médias pro anime")
    p.add_argument("--source", required=True)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", default="exports")
    p = action_sub.add_parser("scan-official-sites", help="Scan sites officiels anime")
    p.add_argument("--source", required=False)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", default="exports")
    p = action_sub.add_parser("scan-cast", help="Scan cast")
    p.add_argument("--source", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", default="exports")
    p = action_sub.add_parser("scan-staff", help="Scan staff")
    p.add_argument("--source", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output", default="exports")
    parser.set_defaults(handler=run)


def run(args):
    output_dir = getattr(args, "output", "exports")
    fmt = getattr(args, "format", "markdown")
    source = getattr(args, "source", None) or getattr(args, "agency", None) or getattr(args, "studio", None) or getattr(args, "maker", None) or "manual"
    title = getattr(args, "title", "N/A")
    meta = get_source(CATEGORY, source) if source != "manual" else {"url": "N/A", "reliability": "manual"}
    note = f"Commande scaffold exécutée. Parseur spécifique à implémenter pour {CATEGORY}/{source}."
    rec = placeholder_record(CATEGORY, args.action, source, meta, note, title)
    if fmt == "json":
        path = export_json([rec], output_dir, f"{CATEGORY}_{args.action}.json")
    else:
        path = export_markdown([rec], output_dir, f"{CATEGORY}_{args.action}.md", f"MangaTracker - {CATEGORY} - {args.action}")
    print(f"Export créé: {path}")
