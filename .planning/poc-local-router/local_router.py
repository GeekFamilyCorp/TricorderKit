#!/usr/bin/env python3
"""
local_router.py — Routeur d'intention SLM local (zero-token Claude).

PoC TricorderKit (DEC-022 proposé). Déporte la *décision de routage* sur un petit
modèle local (Ollama) au lieu de la facturer en tokens Claude.

Flux :
    prompt utilisateur
      -> Ollama (Structured Outputs, JSON garanti, temperature=0, keep_alive=0)
      -> choix d'un profil parmi ceux déclarés dans profiles.json
      -> lancement de l'agent avec la config MCP du profil

Conception (anonymisée, paramétrable) :
    - Aucun nom de vault / chemin personnel en dur : tout vient de profiles.json.
    - Déterministe : temperature=0 + enum strict sur la sortie.
    - Frugal RAM : keep_alive=0 décharge le modèle dès la réponse (cible i5 / 16 Go).
    - Dégradé sûr : si Ollama indisponible -> profil par défaut + code retour non bloquant.

Dépendances : `pip install ollama`  (+ Ollama installé, modèle tiré au préalable).
Usage :
    python3 local_router.py "ta demande ici"
    python3 local_router.py --dry-run "ta demande"     # n'exécute pas l'agent
    python3 local_router.py --profiles ./profiles.json "ta demande"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PROFILES = Path(__file__).with_name("profiles.json")
DEFAULT_MODEL = os.environ.get("LOCAL_ROUTER_MODEL", "qwen:1.8b")
OLLAMA_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
# keep_alive : garder le modèle chaud entre routages consécutifs. "0" déchargerait
# après CHAQUE appel -> rechargement à froid -> timeout. "5m" = bon compromis RAM/latence
# (qwen:1.8b ~1.1 Go). Mettre "0" seulement si la RAM est critique et les appels espacés.
OLLAMA_KEEP_ALIVE = os.environ.get("LOCAL_ROUTER_KEEPALIVE", "5m")
# Timeout généreux pour absorber le 1er chargement à froid du modèle depuis le disque.
OLLAMA_TIMEOUT = int(os.environ.get("LOCAL_ROUTER_TIMEOUT", "120"))
# Marge keyword minimale pour trancher sans réveiller le SLM (écart top1-top2).
KEYWORD_MARGIN = int(os.environ.get("LOCAL_ROUTER_KEYWORD_MARGIN", "1"))


def load_profiles(path: Path) -> dict:
    """Charge la table des profils. Échoue proprement si absente/malformée."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"[local-router] profils introuvables : {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"[local-router] profils JSON invalides : {exc}")

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        sys.exit("[local-router] 'profiles' manquant ou vide dans le fichier de config")
    default = data.get("default_profile")
    if default not in profiles:
        default = next(iter(profiles))
    return {"profiles": profiles, "default_profile": default}


def build_system_instruction(profiles: dict) -> str:
    """Construit la consigne de routage à partir des descriptions de profils."""
    lines = [
        "Tu es un routeur d'intention. Analyse la demande de l'utilisateur "
        "et choisis EXACTEMENT un profil parmi la liste. Réponds en JSON strict.",
        "",
        "Profils disponibles :",
    ]
    for key, prof in profiles["profiles"].items():
        lines.append(f"- {key} : {prof.get('when', prof.get('description', ''))}")
    return "\n".join(lines)


_STOP = {"de", "la", "le", "les", "des", "du", "un", "une", "et", "ou", "au", "aux",
         "en", "sur", "dans", "pour", "ce", "cette", "mes", "ma", "mon"}


def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _tokenize(text: str) -> set:
    # Normalise les accents : "tâche/mémoire/métier" -> "tache/memoire/metier" pour matcher.
    text = _strip_accents(text.lower())
    return {w for w in re.findall(r"[a-z0-9]+", text) if len(w) > 2 and w not in _STOP}


def keyword_decision(prompt: str, profiles: dict):
    """Classifieur déterministe instantané (zéro token, zéro latence) : score chaque
    profil par recouvrement de mots-clés de son champ 'when'. Renvoie (profil, marge, scores) ;
    marge = écart top1-top2 (mesure de confiance)."""
    p = _tokenize(prompt)
    scores = {k: len(p & _tokenize(prof.get("when", prof.get("description", ""))))
              for k, prof in profiles["profiles"].items()}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best = ranked[0][0]
    margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0)
    return best, margin, scores


def _route_slm(prompt: str, profiles: dict, model: str) -> dict:
    """Appel SLM local via REST (/api/chat, Structured Outputs), urllib stdlib.
    Repli sur le profil par défaut si le serveur est injoignable (jamais bloquant)."""
    import urllib.request

    keys = list(profiles["profiles"].keys())
    schema = {
        "type": "object",
        "properties": {
            "profile": {"type": "string", "enum": keys},
            "reason": {"type": "string"},
        },
        "required": ["profile", "reason"],
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_instruction(profiles)},
            {"role": "user", "content": prompt},
        ],
        "format": schema,                  # Structured Outputs : JSON garanti
        "stream": False,
        "options": {"temperature": 0.0},   # déterministe
        "keep_alive": OLLAMA_KEEP_ALIVE,   # garde le modèle chaud entre routages
    }
    url = OLLAMA_API_BASE.rstrip("/") + "/api/chat"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        result = json.loads(body["message"]["content"])
    except Exception as exc:  # serveur éteint, modèle absent, JSON invalide, timeout...
        return {"profile": profiles["default_profile"],
                "reason": f"échec routage local ({exc}) — profil par défaut"}
    if result.get("profile") not in profiles["profiles"]:
        return {"profile": profiles["default_profile"],
                "reason": "profil hors enum — profil par défaut"}
    return result


def route(prompt: str, profiles: dict, model: str) -> dict:
    """Routage HYBRIDE : mots-clés d'abord (instantané, déterministe, zéro token),
    SLM local en secours UNIQUEMENT si le prompt est ambigu (marge < seuil).

    Mesuré 2026-06-01 sur ce poste : sur des prompts nets, le keyword fait 9/9 en ~0 ms,
    là où qwen:1.8b fait 6/9 en 8-30 s. Le SLM ne sert donc qu'à lever les ambiguïtés,
    et le keyword reste le filet de sécurité si le SLM est indisponible."""
    best, margin, scores = keyword_decision(prompt, profiles)
    if scores[best] > 0 and margin >= KEYWORD_MARGIN:
        return {"profile": best, "reason": f"keyword (score={scores[best]}, marge={margin})"}
    slm = _route_slm(prompt, profiles, model)
    if "défaut" in slm["reason"] and scores[best] > 0:
        return {"profile": best,
                "reason": f"keyword-fallback (SLM indispo ; score={scores[best]})"}
    return slm


def launch_agent(profile_cfg: dict, prompt: str, dry_run: bool) -> int:
    """Lance l'agent avec la config MCP du profil. Respecte --dry-run."""
    config_path = profile_cfg.get("mcp_config")
    agent_cmd = profile_cfg.get("agent_cmd", ["claude"])

    cmd = list(agent_cmd)
    if config_path:
        cmd += ["--config", config_path]
    cmd += ["--prompt", prompt]

    if dry_run:
        print(f"[local-router] DRY-RUN — commande prévue : {' '.join(cmd)}")
        return 0
    if not shutil.which(cmd[0]):
        print(f"[local-router] binaire agent introuvable : {cmd[0]} — abandon non bloquant")
        return 0
    return subprocess.run(cmd).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Routeur d'intention SLM local (zero-token).")
    parser.add_argument("prompt", nargs="*", help="Demande utilisateur")
    parser.add_argument("--profiles", default=str(DEFAULT_PROFILES), help="Chemin profiles.json")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modèle Ollama (def: qwen:1.8b)")
    parser.add_argument("--dry-run", action="store_true", help="N'exécute pas l'agent")
    args = parser.parse_args()

    prompt = " ".join(args.prompt) or input("Que voulez-vous faire ? ").strip()
    if not prompt:
        sys.exit("[local-router] prompt vide")

    profiles = load_profiles(Path(args.profiles))
    decision = route(prompt, profiles, args.model)
    profile_key = decision["profile"]
    print(f"[local-router] profil = {profile_key} · raison : {decision['reason']}")

    return launch_agent(profiles["profiles"][profile_key], prompt, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
