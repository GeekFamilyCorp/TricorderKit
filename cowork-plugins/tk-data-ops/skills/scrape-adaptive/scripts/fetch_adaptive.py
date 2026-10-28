#!/usr/bin/env python3
"""
fetch_adaptive.py — squelette de collecte adaptative (Scrapling, repli Playwright).

Usage :
  python3 fetch_adaptive.py --dry-run https://exemple.org/liste
  python3 fetch_adaptive.py --selector ".titre" --level http --out sortie.jsonl https://exemple.org/liste

--dry-run : n'importe aucune bibliothèque tierce, ne contacte pas la cible ; imprime le plan
(User-Agent, lecture de robots.txt, niveau de fetch, sélecteur, provenance, sortie).
Sans --dry-run : lit robots.txt AVEC notre User-Agent (R74), refuse si interdit ou si robots.txt
renvoie 403, puis collecte via Scrapling (import gardé) ou Playwright (repli, import gardé).
Sortie JSON Lines en append ; code 0 seulement si au moins un enregistrement a été écrit (R71).

Variables d'environnement :
  SCRAPE_USER_AGENT   ex. "MonProjetBot/0.1 (+https://exemple.org/contact)"  — obligatoire hors dry-run
  SCRAPE_DELAY_S      délai entre requêtes (défaut 2.0)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone

COLLECTEUR = "fetch_adaptive"
VERSION_SELECTEUR = "0.1.0"


def user_agent(strict: bool) -> str:
    ua = os.environ.get("SCRAPE_USER_AGENT", "")
    if not ua and strict:
        print("SCRAPE_USER_AGENT absent : définir un User-Agent nommé (NomBot/0.1 (+contact)).", file=sys.stderr)
        sys.exit(2)
    return ua or "<SCRAPE_USER_AGENT non défini>"


def robots_autorise(url: str, ua: str) -> tuple[bool, str]:
    """Lit robots.txt avec NOTRE User-Agent. 403/erreur réseau = refus (R74)."""
    parts = urllib.parse.urlsplit(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    req = urllib.request.Request(robots_url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            texte = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True, f"{robots_url} absent (404) : collecte permise par défaut"
        return False, f"{robots_url} → HTTP {e.code} avec notre UA : refus total"
    except (urllib.error.URLError, TimeoutError) as e:
        return False, f"{robots_url} injoignable ({e}) : on ne collecte pas à l'aveugle"
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(texte.splitlines())
    ok = rp.can_fetch(ua, url)
    delay = rp.crawl_delay(ua)
    note = f"can_fetch={ok}" + (f", Crawl-delay={delay}s" if delay else "")
    return ok, note


def provenance(url: str, contenu: str) -> dict:
    return {
        "url": url,
        "collecte_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "collecteur": COLLECTEUR,
        "version_selecteur": VERSION_SELECTEUR,
        "hash_contenu": hashlib.sha256(contenu.encode("utf-8", errors="replace")).hexdigest()[:16],
    }


def fetch_scrapling(url: str, level: str, selector: str, ua: str) -> tuple[list[str], bool] | None:
    """Retourne (textes, relocalise) ou None si Scrapling est absent."""
    try:
        from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher
    except ImportError:
        return None
    Fetcher.adaptive = True  # active le stockage adaptatif (SQLite local par domaine)
    if level == "http":
        page = Fetcher.get(url, headers={"User-Agent": ua})
    elif level == "browser":
        page = DynamicFetcher.fetch(url)
    else:
        page = StealthyFetcher.fetch(url)
    elems = page.css(selector, auto_save=True)
    relocalise = False
    if not elems:
        elems = page.css(selector, adaptive=True)  # relocalisation après refonte
        relocalise = bool(elems)
    return [e.text for e in elems], relocalise


def fetch_playwright(url: str, selector: str, ua: str) -> list[str] | None:
    """Repli : Playwright nu. Retourne None si absent."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(user_agent=ua)
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        textes = page.locator(selector).all_inner_texts()
        browser.close()
    return textes


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Collecte adaptative (Scrapling, repli Playwright).")
    p.add_argument("urls", nargs="+")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--selector", default="h1", help="sélecteur CSS de l'élément à extraire")
    p.add_argument("--level", choices=["http", "browser", "stealth"], default="http")
    p.add_argument("--out", default="collecte.jsonl")
    args = p.parse_args(argv)

    ua = user_agent(strict=not args.dry_run)
    delay = float(os.environ.get("SCRAPE_DELAY_S", "2.0"))

    if args.dry_run:
        print(json.dumps({
            "mode": "dry-run (cible non contactée)",
            "user_agent": ua,
            "etapes": [
                "1. inventaire des données locales relu (R73) — à confirmer par l'opérateur",
                "2. lecture de robots.txt avec ce User-Agent ; 403 = refus total (R74)",
                f"3. fetch niveau '{args.level}' via Scrapling (repli Playwright si absent)",
                f"4. extraction '{args.selector}' avec auto_save=True, puis adaptive=True si vide",
                f"5. écriture JSONL append dans {args.out} avec provenance (url, collecte_le, collecteur, version_selecteur, hash_contenu)",
                f"6. délai {delay}s entre pages, 1 requête à la fois par domaine",
            ],
            "urls": args.urls,
        }, ensure_ascii=False, indent=2))
        return 0

    ecrits = 0
    with open(args.out, "a", encoding="utf-8") as out:
        for i, url in enumerate(args.urls):
            if i:
                time.sleep(delay)
            ok, note = robots_autorise(url, ua)
            print(f"[robots] {url} : {note}", file=sys.stderr)
            if not ok:
                continue
            res = fetch_scrapling(url, args.level, args.selector, ua)
            relocalise = False
            if res is None:
                textes = fetch_playwright(url, args.selector, ua)
                if textes is None:
                    print('Aucun moteur disponible. Installer :\n  pip install "scrapling[fetchers]" && scrapling install\n'
                          "  ou, en repli : pip install playwright && playwright install chromium", file=sys.stderr)
                    return 2
                moteur = "playwright"
            else:
                textes, relocalise = res
                moteur = f"scrapling:{args.level}"
            rec = {"selector": args.selector, "moteur": moteur, "relocalise": relocalise,
                   "valeurs": textes, **provenance(url, "\n".join(textes))}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ecrits += 1
            if relocalise:
                print(f"[adaptive] sélecteur relocalisé sur {url} : mettre à jour VERSION_SELECTEUR", file=sys.stderr)
    print(json.dumps({"event": "collecte", "pages": len(args.urls), "ecrits": ecrits}), file=sys.stderr)
    return 0 if ecrits else 1


if __name__ == "__main__":
    sys.exit(main())
