"""Keep actual SEC index rows unchanged after validating the reviewed full snapshot."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import oracle_revolver as revolver

if __name__=='__main__':
    source=ROOT.parent/'data/raw/sec/ORCL'/revolver.INDEX['document']
    content=source.read_bytes()
    if hashlib.sha256(content).hexdigest()!=revolver.INDEX['sha256']:
        raise SystemExit('Saved index changed; review before rebuilding')
    full=json.loads(content);recent=full['filings']['recent']
    keep=[i for i,d in enumerate(recent['filingDate']) if revolver.INDEX['since']<=d<=revolver.INDEX['through']]
    keep.append(next(i for i,d in enumerate(recent['filingDate']) if d<revolver.INDEX['since']))
    fixture={'cik':full['cik'],'filings':{'recent':{k:[v[i] for i in keep] for k,v in recent.items()},'files':[]}}
    if revolver.index_candidates(fixture)!=revolver.expected_candidates():
        raise SystemExit('Trimmed index changed the candidate set')
    Path(__file__).with_name('ORCL_20261015_submissions.json').write_text(json.dumps(fixture,indent=2)+'\n')
    print('Retained',len(keep),'unchanged real rows')
