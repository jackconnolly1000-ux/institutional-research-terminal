"""Dated Lilly financing evidence; initial issuance is never current outstanding debt."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import lly_liquidity as liquidity

SAMPLE = Path(__file__).parent / "samples/lly_financing.json"
# Reviewed source fingerprints. No personal paths, network calls or AI calls.
SOURCES = {'offering': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580d8k.htm',
              'saved': '0001193125-26-232707-d148580d8k.htm',
              'bytes': 53396,
              'sha256': 'e88aeee8cddfc4b3459ec97cd166010b955ae2d8e5bcc2e59913f995c2e233f9',
              'form': '8-K',
              'filed': '2026-05-20',
              'accession': '0001193125-26-232707',
              'document': 'd148580d8k.htm'},
 'prospectus': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526213175/d81251d424b2.htm',
                'saved': '0001193125-26-213175-d81251d424b2.htm',
                'bytes': 542223,
                'sha256': 'de79f3278d00b382be1d30c66a3c77c7d5623a900ed2fea60da832e3bf17f7f6',
                'form': '424B2',
                'filed': '2026-05-08',
                'accession': '0001193125-26-213175',
                'document': 'd81251d424b2.htm'},
 'preliminary': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526207625/d81251d424b2.htm',
                 'saved': '0001193125-26-207625-d81251d424b2.htm',
                 'bytes': 538875,
                 'sha256': '9106e213563fb34f0163cee21ff709f371ce8db21113061ce967c211b2d1c4df',
                 'form': '424B2',
                 'filed': '2026-05-06',
                 'accession': '0001193125-26-207625',
                 'document': 'd81251d424b2.htm'},
 'pricing': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526209416/d110421dfwp.htm',
             'saved': '0001193125-26-209416-d110421dfwp.htm',
             'bytes': 60426,
             'sha256': '1343ccc799bfd2ed5475ae7a7500a4a18316f576a551c9c445a30cf62464ec2d',
             'form': 'FWP',
             'filed': '2026-05-06',
             'accession': '0001193125-26-209416',
             'document': 'd110421dfwp.htm'},
 'underwriting': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580dex11.htm',
                  'saved': '0001193125-26-232707-d148580dex11.htm',
                  'bytes': 287389,
                  'sha256': 'bd311e48edefc579fb4194d72d6a8b34a04c2e24ee786e5f70fceaee17576296',
                  'form': '8-K Ex. 1.1',
                  'filed': '2026-05-20',
                  'accession': '0001193125-26-232707',
                  'document': 'd148580dex11.htm'},
 'fixed': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580dex43.htm',
           'saved': '0001193125-26-232707-d148580dex43.htm',
           'bytes': 250270,
           'sha256': '23483435eff9194a1858f9a71159cb4d3d661db65eff0ff4d950bb7f4e783b97',
           'form': '8-K Ex. 4.3',
           'filed': '2026-05-20',
           'accession': '0001193125-26-232707',
           'document': 'd148580dex43.htm'},
 'floating': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580dex44.htm',
              'saved': '0001193125-26-232707-d148580dex44.htm',
              'bytes': 155056,
              'sha256': 'abe96195bc60dfbb1bbdb90af64d2e548b2b743cfe34901cdf512542c9c576b9',
              'form': '8-K Ex. 4.4',
              'filed': '2026-05-20',
              'accession': '0001193125-26-232707',
              'document': 'd148580dex44.htm'},
 'indenture': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000005947813000010/exhibit41-indenturedatedfe.htm',
               'saved': '0000059478-13-000010-exhibit41-indenturedatedfe.htm',
               'bytes': 569944,
               'sha256': '59ecb5b9b9ee7b591d4a491324bf5dc6917598f7953e58742279c49f5588b7cb',
               'form': 'S-3 Ex. 4.1',
               'filed': '2013-03-01',
               'accession': '0000059478-13-000010',
               'document': 'exhibit41-indenturedatedfe.htm'},
 'march': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000005947826000045/lly-20260331.htm',
           'saved': '0000059478-26-000045-lly-20260331.htm',
           'bytes': 885191,
           'sha256': 'd862763adc3926432e8f2f3782ee5fd3a2a25eaf07d7e9fba1f6b8a34bba10e1',
           'form': '10-Q',
           'filed': '2026-04-30',
           'accession': '0000059478-26-000045',
           'document': 'lly-20260331.htm'},
 'renewal_2025': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000005947825000254/lly-20250930.htm',
                  'saved': '0000059478-25-000254-lly-20250930.htm',
                  'bytes': 1778719,
                  'sha256': '42c059a665504223ca36aa4ac3ffa46769192a462c5865ee6e82d6b273043742',
                  'form': '10-Q',
                  'filed': '2025-10-30',
                  'accession': '0000059478-25-000254',
                  'document': 'lly-20250930.htm'},
 'shelf': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000119312525029608/d933321ds3asr.htm',
           'saved': '0001193125-25-029608-d933321ds3asr.htm',
           'bytes': 308107,
           'sha256': '8316a4b197cd2949253219f30c103e6541af69c5473bb30ac3764b7e8350f1dd',
           'form': 'S-3ASR',
           'filed': '2025-02-19',
           'accession': '0001193125-25-029608',
           'document': 'd933321ds3asr.htm'},
 'delisting': {'url': 'https://www.sec.gov/Archives/edgar/data/59478/000087666126000494/xslF25X02/primary_doc.xml',
               'saved': '0000876661-26-000494-primary_doc.xml',
               'bytes': 10262,
               'sha256': '89dccdfc4c4c5dbf808ef06d05ed9f8f875e2c3dd8e9d529620aba59790f2692',
               'form': '25-NSE',
               'filed': '2026-06-02',
               'accession': '0000876661-26-000494',
               'document': 'primary_doc.xml'}}
INVENTORY = {'source_url': 'https://data.sec.gov/submissions/CIK0000059478.json',
 'document': 'CIK0000059478-20261015.json',
 'sha256': 'c271d2468744874b2c34fa4beec68b10d9dc9547910833d521ddbc22031c9269',
 'cutoff': '2026-10-15',
 'oldest': '2021-12-16',
 'latest': '2026-10-15',
 'count': 1001,
 'eligible': [{'filingDate': '2026-08-05',
               'reportDate': '2026-06-30',
               'form': '10-Q',
               'accessionNumber': '0000059478-26-000081',
               'primaryDocument': 'lly-20260630.htm',
               'items': ''},
              {'filingDate': '2026-08-05',
               'reportDate': '2026-08-05',
               'form': '8-K',
               'accessionNumber': '0000059478-26-000077',
               'primaryDocument': 'lly-20260805.htm',
               'items': '2.02,9.01'},
              {'filingDate': '2026-06-02',
               'reportDate': '',
               'form': '25-NSE',
               'accessionNumber': '0000876661-26-000494',
               'primaryDocument': 'xslF25X02/primary_doc.xml',
               'items': ''},
              {'filingDate': '2026-05-20',
               'reportDate': '2026-05-20',
               'form': '8-K',
               'accessionNumber': '0001193125-26-232707',
               'primaryDocument': 'd148580d8k.htm',
               'items': '8.01,9.01'},
              {'filingDate': '2026-05-08',
               'reportDate': '',
               'form': '424B2',
               'accessionNumber': '0001193125-26-213175',
               'primaryDocument': 'd81251d424b2.htm',
               'items': ''},
              {'filingDate': '2026-05-07',
               'reportDate': '2026-05-04',
               'form': '8-K',
               'accessionNumber': '0000059478-26-000048',
               'primaryDocument': 'lly-20260504.htm',
               'items': '5.07'},
              {'filingDate': '2026-05-06',
               'reportDate': '',
               'form': 'FWP',
               'accessionNumber': '0001193125-26-209416',
               'primaryDocument': 'd110421dfwp.htm',
               'items': ''},
              {'filingDate': '2026-05-06',
               'reportDate': '',
               'form': '424B2',
               'accessionNumber': '0001193125-26-207625',
               'primaryDocument': 'd81251d424b2.htm',
               'items': ''},
              {'filingDate': '2026-04-30',
               'reportDate': '2026-03-31',
               'form': '10-Q',
               'accessionNumber': '0000059478-26-000045',
               'primaryDocument': 'lly-20260331.htm',
               'items': ''},
              {'filingDate': '2026-04-30',
               'reportDate': '2026-04-30',
               'form': '8-K',
               'accessionNumber': '0000059478-26-000043',
               'primaryDocument': 'lly-20260430.htm',
               'items': '2.02,9.01'},
              {'filingDate': '2026-02-12',
               'reportDate': '2025-12-31',
               'form': '10-K',
               'accessionNumber': '0000059478-26-000013',
               'primaryDocument': 'lly-20251231.htm',
               'items': ''},
              {'filingDate': '2026-02-04',
               'reportDate': '2026-02-04',
               'form': '8-K',
               'accessionNumber': '0000059478-26-000008',
               'primaryDocument': 'lly-20260204.htm',
               'items': '2.02,9.01'}]}


def _review():
    rows = []
    series = [
        ("Floating 2028", 750_000_000, "2028-05-20", None, 0.00350, "floating"),
        ("Floating 2029", 500_000_000, "2029-05-20", None, 0.00460, "floating"),
        ("Fixed 2029", 750_000_000, "2029-05-20", 0.04150, None, "fixed"),
        ("Fixed 2031", 1_500_000_000, "2031-05-20", 0.04375, None, "fixed"),
        ("Fixed 2033", 1_250_000_000, "2033-05-20", 0.04650, None, "fixed"),
        ("Fixed 2036", 1_500_000_000, "2036-05-20", 0.04850, None, "fixed"),
        ("Fixed 2056", 1_750_000_000, "2056-05-20", 0.05600, None, "fixed"),
        ("Fixed 2066", 1_000_000_000, "2066-05-20", 0.05700, None, "fixed"),
    ]
    for i, (label, principal, maturity, coupon, margin, source) in enumerate(series):
        rows.append(dict(key="may_notes_" + str(i), label=label, initial_principal=principal,
                         stated_maturity=maturity, coupon=coupon, sofr_margin=margin,
                         current_outstanding=None, source=source, location="Certificate clauses (iii)–(v); note forms",
                         issued="2026-05-20", basis="Initial issue principal, not June outstanding balance",
                         source_kind="Reviewed contract text", tag=None,
                         detail="Stated maturity subject to applicable business-day, redemption and default provisions. "
                         "Not added to June debt or the December carrying-amount table."))
    return dict(status="Checked", ticker="LLY", anchor=liquidity.END,
                anchor_accession=liquidity.SOURCES["quarter"]["accession"], checked_as_of="2026-10-15",
                sources=deepcopy(SOURCES), inventory=deepcopy(INVENTORY), rows=rows,
                initial_principal_total=sum(r["initial_principal"] for r in rows),
                reported_issue_total=9_000_000_000, drawable=None, coverage=None,
                conclusion="May's completed $9B offering establishes eight series' stated maturities. "
                "These are initial issue amounts, not a complete June or October outstanding-principal schedule. "
                "No 2026 facility renewal or updated drawable amount was identified through October 15.",
                inventory_detail="SEC submissions contain 1,001 filings, October 15, 2026 back to December 16, 2021; "
                "older pages end before the review period. All 2026 form rows were screened, prioritizing periodic reports, "
                "amendments, 8-Ks, shelf/prospectus/pricing filings and debt delisting. "
                "After June 30, the only 8-K is the saved August 5 earnings report; no later periodic report or "
                "amendment, 424B2 or FWP is listed. Ownership filings are not corporate financing capacity.",
                credit_detail="The retrieved September 2025 10-Q describes the August 2025 renewal to $6B "
                "and extension of the $4B facility to December 2029. This is historical, not an August 2026 renewal. "
                "The annual and March/June reports and reviewed exhibit lists establish no current credit agreement "
                "or post-August 2026 renewal. No relevant bank agreement was identified in the reviewed SEC filing "
                "and exhibit references. Draw conditions, current usage, covenant headroom and actual drawable capacity remain Unavailable.",
                coupon_conflict="The May 20 8-K's interest paragraph says 4.650% for the fixed 2029 notes, "
                "while its series title, final prospectus and Exhibit 4.3 clauses (i)/(v) agree on 4.150%. "
                "This review uses the corroborated contract rate, 4.150%, and retains the conflicting statement here.",
                redemption_detail="The May terms require 101% special redemption of specified series if the Centessa "
                "acquisition fails under the stated conditions. The terms cease to apply upon consummation; the June "
                "10-Q Note 4 records acquisition on June 24, 2026. This resolved acquisition-failure condition is not "
                "presented as a future 101% cash bill. Optional redemptions and default acceleration remain possible; none is assumed.",
                date_detail="Dates are stated contractual maturities, not calendar-adjusted payment forecasts. "
                "Indenture §1.11 and note-specific business-day provisions apply. Future interest amounts, "
                "floating-rate resets, actual early redemptions and cash available at maturity are not modeled.",
                delisting_detail="The June 2 Form 25 removes the 1.625% notes due 2026 from listing. "
                "It does not establish an instrument-level cash repayment amount and is not used to allocate H1 repayments.")


def build(folder: Path):
    """Only the reviewed fingerprints may reproduce these manually checked contract findings."""
    files = [(s["saved"], s["sha256"]) for s in SOURCES.values()]
    files += [(s["document"], s["sha256"]) for s in liquidity.SOURCES.values()]
    files += [(INVENTORY["document"], INVENTORY["sha256"])]
    for name, expected in files:
        p = folder / name
        if not p.is_file():
            return dict(status="Unavailable", detail="Missing reviewed source: " + name)
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            return dict(status="Unavailable", detail="Changed source requires review: " + name)
    return _review()


def load():
    try:
        saved = json.loads(SAMPLE.read_text())
        if saved == _review():
            return saved
    except (OSError, ValueError):
        pass
    return dict(status="Unavailable", detail="The saved Lilly financing audit does not match the reviewed evidence.")


def for_snapshot(snapshot):
    if snapshot.get("ticker") != "LLY":
        return None
    anchor = snapshot.get("metrics", {}).get("cash", {})
    if anchor.get("accession") != liquidity.SOURCES["quarter"]["accession"] or anchor.get("period_end") != liquidity.END:
        return dict(status="Unavailable", detail="Financing review covers the checked June 30 Lilly snapshot only.")
    return load()
