"""Reproduce the hand-checked financing audit only from its exact saved sources."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import lly_financing as lf
review = lf.build(ROOT.parent / 'data/raw/sec/LLY')
if review['status'] != 'Checked':
    raise SystemExit(review['detail'])
lf.SAMPLE.write_text(json.dumps(review, indent=2) + '\n')
print('Eight series reconcile to $9B initial issue principal; drawable capacity stays Unavailable.')
