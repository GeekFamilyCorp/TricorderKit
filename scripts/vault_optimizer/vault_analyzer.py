#!/usr/bin/env python3
import argparse, os, re
from pathlib import Path
from collections import Counter
from datetime import datetime
IGNORE={'.git','.obsidian','node_modules','__pycache__','.venv','venv'}
def ign(p): return bool(set(p.parts)&IGNORE)
def sample(p,n=12000):
    try: return p.read_text(encoding='utf-8',errors='ignore')[:n]
    except Exception: return ''
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--vault',default='.'); ap.add_argument('--out',default='.tricorderkit/reports/initial_analysis.md'); a=ap.parse_args(); root=Path(a.vault).resolve()
    folders=Counter(); tags=Counter(); keys=Counter(); large=[]; templates=[]; empty=[]; mds=[]; total=0
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if ign(rel): continue
        if p.is_dir():
            try:
                if not any(p.iterdir()): empty.append(str(rel))
            except Exception: pass
            continue
        total+=1; folders[str(rel.parent).split(os.sep)[0]]+=1
        if p.suffix.lower()=='.md':
            mds.append(p); size=p.stat().st_size
            if size>80000: large.append((str(rel),size))
            if 'template' in str(rel).lower() or 'modèle' in str(rel).lower(): templates.append(str(rel))
            txt=sample(p)
            for t in re.findall(r'(?<!\w)#([A-Za-z0-9_\-/À-ÿ]+)',txt): tags[t]+=1
            fm=txt[3:txt.find('\n---',3)] if txt.startswith('---') and txt.find('\n---',3)!=-1 else ''
            for k in re.findall(r'^([A-Za-z0-9_\-]+):',fm,flags=re.M): keys[k]+=1
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Initial Vault Analysis','',f'- generated_at: {datetime.utcnow().isoformat()}Z',f'- root: `{root}`',f'- total_files: {total}',f'- markdown_files: {len(mds)}',f'- empty_dirs: {len(empty)}','']
    lines+=['## Top folders','| Folder | Files |','|---|---:|']+[f'| `{k}` | {v} |' for k,v in folders.most_common(30)]
    lines+=['','## Templates detected']+([f'- `{x}`' for x in templates[:80]] or ['- none detected'])
    lines+=['','## Large Markdown files']+([f'- `{f}` — {s} bytes' for f,s in sorted(large,key=lambda x:-x[1])[:50]] or ['- none above threshold'])
    lines+=['','## Top frontmatter keys']+[f'- `{k}`: {v}' for k,v in keys.most_common(40)]
    lines+=['','## Top tags']+[f'- `#{k}`: {v}' for k,v in tags.most_common(40)]
    lines+=['','## Empty directories']+([f'- `{d}`' for d in empty[:100]] or ['- none detected'])
    out.write_text('\n'.join(lines),encoding='utf-8'); print('Wrote',out)
if __name__=='__main__': main()
