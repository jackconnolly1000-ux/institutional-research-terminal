"""Regression checks for the confirmed date, scope and source-location contradictions."""
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from openpyxl import load_workbook
import company_review as cr
import funding_conclusions as fc
import oracle_revolver as revolver


class ReviewClarity(unittest.TestCase):
    def setUp(self):
        self.snapshots=json.loads((fc.FOLDER/'liquidity_pilots.json').read_text())['snapshots']

    def test_headlines_name_ttm_and_review_dates_are_explicit(self):
        for snapshot in self.snapshots:
            rendered=html.unescape(cr.render(snapshot))
            self.assertTrue(cr.headline(snapshot).startswith('TTM '))
            self.assertIn('Balance-sheet facts checked '+snapshot['checked_as_of'],rendered)
            self.assertNotIn('Saved review, Oct 14',rendered)
            self.assertIn('Interpretation checked 2026-10-16',rendered)
            self.assertIn('Funding conclusion for '+snapshot['ticker'],rendered)

    def test_oracle_scope_carries_the_verified_index_check(self):
        shown=html.unescape(cr.render(self.snapshots[1]))
        self.assertIn('SEC financing-candidate index check covers August 31 through October 15, 2026',shown)
        self.assertNotIn('does not establish complete coverage of later',shown)
        self.assertIn(revolver.INDEX['source_url'],shown)
        self.assertEqual([c['accession'] for c in revolver.load()['inventory']['candidates']],
                         ['0001193125-26-389753','0001193125-26-387905'])

    def test_coverage_source_locations_include_statement_and_interest_pages(self):
        expected={'LLY':['p. 5','p. 23','p. 57','p. 77'],
                  'ORCL':['p. 2','p. 12','p. 65','p. 88'],
                  'VST':['p. 1','p. 28','p. 79','p. 121']}
        for ticker,pages in expected.items():
            locations=' '.join(s['location'] for s in fc.load(ticker)['coverage_sources'])
            for page in pages:self.assertIn(page,locations)

    def test_excel_scope_and_documentation_links_match_review(self):
        for stem in ['lly','oracle','vistra']:
            wb=load_workbook(fc.FOLDER/f'{stem}_liquidity.xlsx',data_only=True)
            about=wb['About']
            self.assertIn('October 16',about['B2'].value)
            sources=[r[2].value for r in about if len(r)>2 and isinstance(r[2].value,str)]
            self.assertFalse(any(s.startswith('docs/') for s in sources))
            self.assertTrue(any('/blob/main/docs/' in s for s in sources))
            if stem=='lly':
                self.assertNotIn('Not a complete SEC filing inventory',wb['Repayment review']['D50'].value)
                self.assertIn('October 15',wb['Repayment review']['D50'].value)
            if stem=='oracle':
                self.assertEqual(wb['Repayment review']['A13'].value,'Shared cash pool')
                self.assertIn('not added again',wb['Repayment review']['D13'].value)
                self.assertIn('October 15',about['B13'].value)
                self.assertGreaterEqual(wb['Repayment review'].row_dimensions[13].height,40)

    def test_lilly_alternate_folder_must_have_the_checked_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            for name in [*fc.FILES['LLY'],'lly_liquidity.xlsx','lly_liquidity.manifest.json']:
                shutil.copy(fc.FOLDER/name,folder/name)
            self.assertIsNotNone(cr.saved_workbook(self.snapshots,folder,ticker='LLY'))
            path=folder/'lly_liquidity.json';path.write_bytes(path.read_bytes()+b'\n')
            manifest=json.loads((folder/'lly_liquidity.manifest.json').read_text())
            manifest['sources']['lly_liquidity.json']=hashlib.sha256(path.read_bytes()).hexdigest()
            (folder/'lly_liquidity.manifest.json').write_text(json.dumps(manifest))
            self.assertIsNone(cr.saved_workbook(self.snapshots,folder,ticker='LLY'))


if __name__=='__main__':unittest.main()
