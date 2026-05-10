#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''): h.update(c)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--vault',default='.'); ap.add_argument('--manifest',default='.tricorderkit/index/manifest.jsonl'); ap.add_argument('--out',default='.tricorderkit/reports/delta_report.md'); a=ap.parse_args(); root=Path(a.vault).resolve()
    old={}
    mp=Path(a.manifest)
    if mp.exists():
        for line in mp.read_text(encoding='utf-8').splitlines():
            if line.strip():
                o=json.loads(line); old[o['path']]=o
    changed=[]; missing=[]
    for rel,o in old.items():
        p=root/rel
        if not p.exists(): missing.append(rel)
        elif p.is_file() and sha(p)!=o.get('sha256'): changed.append(rel)
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('# Vault Delta Report\n\n- changed_files: %d\n- missing_files: %d\n\n## Changed files\n%s\n\n## Missing files\n%s\n'%(len(changed),len(missing),'\n'.join('- `'+x+'`' for x in changed) or '- none','\n'.join('- `'+x+'`' for x in missing) or '- none'),encoding='utf-8')
    print('Wrote',out)
if __name__=='__main__': main()
