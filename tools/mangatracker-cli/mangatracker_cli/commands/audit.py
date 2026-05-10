from argparse import ArgumentParser
from mangatracker_cli.core.registry import load_sources


def add_parser(subparsers):
    parser = subparsers.add_parser("audit", help="Audit des sources et modules")
    action_sub = parser.add_subparsers(dest="action", required=True)
    p = action_sub.add_parser("sources", help="Audit du registre de sources")
    p.add_argument("--config", default=None)
    parser.set_defaults(handler=run)


def run(args):
    sources = load_sources(args.config)
    total = 0
    missing = []
    for cat, entries in sources.items():
        for key, meta in entries.items():
            total += 1
            for field in ["name_jp", "url", "reliability", "priority", "use_cases"]:
                if field not in meta:
                    missing.append(f"{cat}/{key}: champ manquant {field}")
    print(f"Sources auditées: {total}")
    if missing:
        print("Problèmes:")
        for item in missing:
            print(f"- {item}")
    else:
        print("Aucun champ critique manquant.")
