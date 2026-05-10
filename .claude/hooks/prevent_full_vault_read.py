#!/usr/bin/env python3
import sys, re
payload=sys.stdin.read()
if re.search(r'cat\s+\*\*/\*\.md|find\s+\.\s+-name', payload):
    print('BLOCKED: full vault read detected.', file=sys.stderr); sys.exit(2)
sys.exit(0)
