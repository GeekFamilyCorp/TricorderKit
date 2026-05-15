"""
conftest.py — Configuration pytest pour tk-orchestrator
Gère les imports depuis un dossier avec tiret (tk-orchestrator).
"""
import sys
from pathlib import Path

# tk-orchestrator/ est le parent du dossier tests/
_SKILL_DIR = Path(__file__).parent.parent          # skills/tk-orchestrator/
_PROJECT_ROOT = _SKILL_DIR.parent.parent           # TricorderKit_v0.7/

# Injecter les deux en tête de sys.path
for p in [str(_SKILL_DIR), str(_PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)
