#!/usr/bin/env python3
import sys
payload=sys.stdin.read()
for x in ['cat **/*.md','cat *.md',"find . -name '*.md' -exec cat",'grep -R . .']:
    if x in payload:
        print('BLOCKED: broad vault read detected. Use manifest or CLI summaries first.', file=sys.stderr); sys.exit(2)
sys.exit(0)
