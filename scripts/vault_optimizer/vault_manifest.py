#!/usr/bin/env python3
import argparse, hashlib, json, re
from pathlib import Path
from datetime import datetime
IGNORE={'.git','node_modules','__pycache__','.venv','venv'}
def ign(p): return bool(set(p.parts)&IGNORE)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''): h.update(c)
    return h.hexdigest()
def cat(rel):
    s='/'.join(x.lower() for x in rel.parts)
    for k in ['manga','anime','light','novel','seiyu','studio','game','jeux','source','template','personnage','éditeur','editeur']:
        if k in s: return k
    return rel.parts[0].lower() if len(rel.parts)>1 else 'root'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--vault',default='.'); ap.add_argument('--out',default='.tricorderkit/index/manifest.jsonl'); a=ap.parse_args(); root=Path(a.vault).resolve(); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as w:
        for p in root.rglob('*'):
            if not p.is_file(): continue
            rel=p.relative_to(root)
            if ign(rel) or str(rel).startswith('.tricorderkit/cache/'): continue
            obj={'path':str(rel).replace('\\','/'),'suffix':p.suffix.lower(),'bytes':p.stat().st_size,'mtime':datetime.utcfromtimestamp(p.stat().st_mtime).isoformat()+'Z','sha256':sha(p),'category_guess':cat(rel)}
            if p.suffix.lower()=='.md':
                txt=p.read_text(encoding='utf-8',errors='ignore')[:20000]
                obj['wiki_links_count']=len(re.findall(r'\[\[[^\]]+\]\]',txt)); obj['tags']=sorted(set(re.findall(r'(?<!\w)#([A-Za-z0-9_\-/À-ÿ]+)',txt)))[:30]; obj['has_frontmatter']=txt.startswith('---')
            w.write(json.dumps(obj,ensure_ascii=False)+'\n')
    print('Wrote',out)
if __name__=='__main__': main()
