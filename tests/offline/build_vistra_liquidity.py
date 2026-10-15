"""Rebuild only this checked Vistra review; raw documents stay outside the public repository."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import vistra_liquidity as vl

raw=ROOT.parent/'data/raw/sec/VST'
review=vl.build(raw/'vistra-20260630.htm',raw/'vistra-20251231.htm')
if review['status']!='Checked' or any(review[k] is None for k in ['cash','capacity','debt','annual']):
    raise ValueError('Incomplete Vistra reconciliation: '+review['detail'])
vl.SAMPLE.write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print({k:review[k] for k in ['cash','capacity','debt','annual']})
