"""One read-only acceptance audit covers models, source metadata and saved exports."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit_release1',ROOT/'tests/offline/audit_release1.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class ReleaseReconciliation(unittest.TestCase):
    def test_checked_release_reconciles_without_network_or_ai(self):
        results=audit.audit()
        self.assertEqual([r['ticker'] for r in results],['LLY','ORCL','VST'])
        self.assertEqual([r['sheets'] for r in results],[8,10,10])
        self.assertTrue(all(r['metrics']==10 and r['core_charts']==2 and r['future_funding_coverage']=='Unavailable' for r in results))

    def test_wrong_company_download_is_rejected(self):
        wrong=(ROOT/'samples/oracle_liquidity.xlsx').read_bytes()
        with self.assertRaisesRegex(ValueError,'LLY: actual download differs'):
            audit.audit({'LLY':wrong})

    def test_source_links_must_match_entity_accession_and_secure_sec_host(self):
        url='https://www.sec.gov/Archives/edgar/data/59478/000005947826000081/lly-20260630.htm'
        audit.source_url(url,'0000059478-26-000081','LLY')
        for changed in [url.replace('59478/','1341439/'),url.replace('000081','000013'),url.replace('https:','http:'),url.replace('www.sec.gov','example.com')]:
            with self.subTest(url=changed),self.assertRaisesRegex(ValueError,'source URL'):
                audit.source_url(changed,'0000059478-26-000081','LLY')

    def test_app_exposes_annual_and_lease_source_selection(self):
        for snapshot in json.loads((ROOT/'samples/liquidity_pilots.json').read_text())['snapshots']:
            text=audit.company_review.evidence_html(snapshot)
            history=audit.company_history.build(snapshot)
            self.assertIn('Annual history source inputs',text)
            self.assertIn(history['annual_facts'][0]['accession'],text)
            self.assertIn('Lease source inputs',text)
            self.assertIn('Exact prefixed tag; exact stated instant; USD; no dimensions; agreeing duplicates.',text)
            self.assertIn('us-gaap:OperatingLeaseLiabilityCurrent',text)
