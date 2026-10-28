#!/usr/bin/env python3
import sys,re
payload=sys.stdin.read()
for pat in [r'AKIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9_\-]{20,}', r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}']:
    if re.search(pat,payload):
        print('BLOCKED: possible secret detected.', file=sys.stderr); sys.exit(2)
sys.exit(0)
