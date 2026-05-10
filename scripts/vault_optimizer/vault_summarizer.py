#!/usr/bin/env python3
import argparse
from pathlib import Path
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--out'); ap.add_argument('--max-lines',type=int,default=120); a=ap.parse_args(); p=Path(a.file); lines=p.read_text(encoding='utf-8',errors='ignore').splitlines(); heads=[l for l in lines if l.startswith('#')][:80]
    s='# Summary: '+p.name+'\n\n## Headings\n'+'\n'.join('- '+h for h in heads)+'\n\n## Opening sample\n```markdown\n'+'\n'.join(lines[:a.max_lines])+'\n```\n'
    Path(a.out).write_text(s,encoding='utf-8') if a.out else print(s)
if __name__=='__main__': main()
