"""
private_terms.py - Private-term matching without publishing the terms.

Why: a public repository cannot contain, in clear text, the list of names it
must never publish (the list itself would be the leak). The default terms are
therefore stored as SHA-256 digests of their normalized form, and matched
against normalized word n-grams of the scanned text (and of file paths).

Sources of terms, merged:
  1. DEFAULT_DIGESTS below (hashed, public, maintained by the repo owner);
  2. the environment variable TK_PRIVATE_TERMS (comma-separated, clear text,
     e.g. a CI secret);
  3. the untracked file configs/local/private_terms.txt (one term per line,
     clear text, never committed - see .gitignore).

Normalization: lowercase, every non-alphanumeric character becomes a word
break. A term matches if its words appear consecutively, either separated
("acme corp", "acme-corp", "acme_corp") or glued ("acmecorp", "AcmeCorp"). Both forms are hashed, so "Acme-Corp", "acme corp" and
"acmecorp" are all caught by a single entry.

Add a term to the defaults:
    python plugins/security-audit-cli/private_terms.py --digest "Acme Corp"
and paste the printed digests into DEFAULT_DIGESTS.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

# SHA-256 of normalized private terms (space-joined and glued forms).
DEFAULT_DIGESTS: frozenset[str] = frozenset({
    "7f9190fc804393e2800081cbd2011a3988b05e68b18957a72738efb025b0ea89",
    "d847f80fede2f075f0d4b3525b9e0667b2f026ebe0590ed1e5568da1783cea90",
    "da4576067f7d59c83a64b282d476b8c2052b9a1a34b792b515970bd42da769d0",
    "dc3ac8c8f566be20447706e44547eb500dea9e0d4e762f82b3dd0d914c6fbbb8",
})

_WORD = re.compile(r"[a-z0-9]+")
MAX_WORDS = 4
LOCAL_FILE = Path("configs") / "local" / "private_terms.txt"


def _norm_words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def term_digests(term: str) -> set[str]:
    """Digests (spaced and glued forms) of one clear-text term."""
    words = _norm_words(term)
    if not words:
        return set()
    forms = {" ".join(words), "".join(words)}
    return {hashlib.sha256(f.encode("utf-8")).hexdigest() for f in forms}


def load_digests(root: Path | None = None, extra_terms: list[str] | None = None,
                 use_defaults: bool = True) -> dict[str, str]:
    """Return {digest: label}. Labels never contain the clear term."""
    out: dict[str, str] = {}
    if use_defaults:
        for d in DEFAULT_DIGESTS:
            out[d] = f"private-term#{d[:8]}"
    terms: list[str] = list(extra_terms or [])
    env = os.environ.get("TK_PRIVATE_TERMS", "")
    terms += [t for t in env.split(",") if t.strip()]
    if root is not None:
        p = Path(root) / LOCAL_FILE
        if p.exists():
            terms += [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
                      if l.strip() and not l.lstrip().startswith("#")]
    for t in terms:
        for d in term_digests(t):
            out[d] = f"private-term#{d[:8]}"
    return out


def find_terms(text: str, digests: dict[str, str]) -> list[str]:
    """Labels of the private terms present in text (deduplicated, ordered)."""
    if not digests:
        return []
    words = _norm_words(text)
    found: list[str] = []
    for i in range(len(words)):
        for n in range(1, MAX_WORDS + 1):
            chunk = words[i:i + n]
            if len(chunk) < n:
                break
            for form in (" ".join(chunk), "".join(chunk)):
                d = hashlib.sha256(form.encode("utf-8")).hexdigest()
                lab = digests.get(d)
                if lab and lab not in found:
                    found.append(lab)
        # glued words inside a single token are covered by the n=1 glued form
    return found


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--digest":
        for d in sorted(term_digests(sys.argv[2])):
            print(f'    "{d}",')
        sys.exit(0)
    print(__doc__)
    sys.exit(0)
