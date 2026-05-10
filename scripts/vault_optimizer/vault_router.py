#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from collections import Counter
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--vault',default='.'); ap.add_argument('--manifest',default='.tricorderkit/index/manifest.jsonl'); ap.add_argument('--out',default='.tricorderkit/config/router.generated.json'); a=ap.parse_args()
    cats=Counter(); large=[]; total=0; mp=Path(a.manifest)
    if mp.exists():
        for line in mp.read_text(encoding='utf-8').splitlines():
            if line.strip():
                o=json.loads(line); total+=1; cats[o.get('category_guess','unknown')]+=1
                if o.get('bytes',0)>80000: large.append(o['path'])
    router={'version':'0.1','strategy':'manifest_first_cli_batch_mcp_structured_sync','total_indexed_files':total,'category_counts':dict(cats),'large_files':large[:100],'routes':{'global_analysis':'CLI:vault_analyzer','file_inventory':'manifest.jsonl','specific_lookup':'Grep/Read targeted files','batch_extract':'CLI','structured_sync':'MCP','large_file_summary':'CLI:vault_summarizer','mass_edit':'dry-run CLI then apply','audit':'CLI:vault_delta + targeted Read'}}
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(router,ensure_ascii=False,indent=2),encoding='utf-8'); print('Wrote',out)
if __name__=='__main__': main()
