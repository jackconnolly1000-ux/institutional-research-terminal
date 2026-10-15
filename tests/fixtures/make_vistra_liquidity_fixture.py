"""Keep every occurrence of checked tags and the real contexts/units, without altering facts."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import filing_xbrl as fx
import vistra_liquidity as vl

XHTML='http://www.w3.org/1999/xhtml'
for prefix,uri in {'':XHTML,**fx.NS}.items(): ET.register_namespace(prefix,uri)
for period in ['quarter','annual']:
    root=ET.parse(ROOT.parent/'data/raw/sec/VST'/vl.PERIODS[period]['document']).getroot()
    tags=({t for _,t,_ in vl.FLOWS.values()} | {t for _,t,_ in vl.INSTANTS.values()}
          | {t for _,t,_ in vl.DIMENSIONED.values()} | {'vistra:InvestmentCompanyInitialCommitmentCapital',
             'vistra:InvestmentCompanyAdditionalCommitmentCapital','us-gaap:BusinessCombinationConsiderationTransferred1'}
          if period=='quarter' else {'us-gaap:'+t for t in vl.ANNUAL_TAGS} |
             {vl.INSTANTS['debt_costs'][1],vl.INSTANTS['lt_carrying'][1]})
    facts=[e for e in root.iter('{'+fx.IX+'}nonFraction') if e.get('name') in tags]
    contexts={e.get('contextRef') for e in facts}; units={e.get('unitRef') for e in facts}
    html=ET.Element('{'+XHTML+'}html'); body=ET.SubElement(html,'{'+XHTML+'}body')
    resources=ET.SubElement(ET.SubElement(body,'{'+fx.IX+'}header'),'{'+fx.IX+'}resources')
    resources.extend(e for e in root.iter('{'+fx.XBRLI+'}context') if e.get('id') in contexts)
    resources.extend(e for e in root.iter('{'+fx.XBRLI+'}unit') if e.get('id') in units)
    for fact in facts:
        fact.tail=None
        ET.SubElement(body,'{'+XHTML+'}p').append(fact)
    output=Path(__file__).parent/f'VST_liquidity_{period}.htm'
    ET.ElementTree(html).write(output,encoding='utf-8',xml_declaration=True)
    print(output.name,len(facts),'facts',output.stat().st_size,'bytes')
