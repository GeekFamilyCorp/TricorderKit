#!/usr/bin/env python3
from pathlib import Path
import sys
if not Path('.tricorderkit/index/manifest.jsonl').exists(): print('WARNING: manifest is missing. Run /vault-analyze before broad reads.', file=sys.stderr)
sys.exit(0)
