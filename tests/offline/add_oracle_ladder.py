"""Attach the Artifact Tool-authored ladder without rewriting existing workbook content."""
from io import BytesIO
from pathlib import Path
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scenario_export import chart_cache
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('x',NS);ET.register_namespace('r',REL)


def apply(folder):
    path=ROOT/'samples/oracle_liquidity.xlsx';source=zipfile.ZipFile(path)
    authored=zipfile.ZipFile(folder/'oracle-ladder.xlsx')
    names=source.namelist()
    chart_number=max(int(re.search(r'chart(\d+)',p)[1]) for p in names if re.fullmatch(r'xl/drawings/charts/chart\d+\.xml',p))+1
    drawing_number=max(int(re.search(r'drawing(\d+)',p)[1]) for p in names if re.fullmatch(r'xl/drawings/drawing\d+\.xml',p))+1
    chart=f'xl/drawings/charts/chart{chart_number}.xml';drawing=f'xl/drawings/drawing{drawing_number}.xml'
    draw_rels=drawing.replace('drawings/','drawings/_rels/')+'.rels'
    replacements={chart:authored.read('xl/drawings/charts/chart1.xml'),drawing:authored.read('xl/drawings/drawing1.xml')}
    cns='http://schemas.openxmlformats.org/drawingml/2006/chart'
    chart_xml=ET.fromstring(replacements[chart])
    original_sheet=ET.fromstring(source.read('xl/worksheets/sheet8.xml'))
    cells={c.get('r'):c for c in original_sheet.findall(f'.//{{{NS}}}c')}
    ser=chart_xml.find(f'.//{{{cns}}}ser')
    chart_cache(ser.find(f'{{{cns}}}cat/{{{cns}}}strRef/{{{cns}}}strCache'),
                [cells[f'A{r}'].find(f'{{{NS}}}v').text for r in range(49,55)])
    chart_cache(ser.find(f'{{{cns}}}val/{{{cns}}}numRef/{{{cns}}}numCache'),
                [float(cells[f'C{r}'].find(f'{{{NS}}}v').text) for r in range(49,55)])
    replacements[chart]=ET.tostring(chart_xml,encoding='utf-8',xml_declaration=True)
    relations=ET.fromstring(authored.read('xl/drawings/_rels/drawing1.xml.rels'))
    for rel in relations:rel.set('Target',f'charts/chart{chart_number}.xml')
    replacements[draw_rels]=ET.tostring(relations,encoding='utf-8',xml_declaration=True)
    sheet_name='xl/worksheets/sheet8.xml';sheet=ET.fromstring(source.read(sheet_name))
    if sheet.find(f'{{{NS}}}drawing') is not None:raise ValueError('Payment dates already has a drawing')
    rp='xl/worksheets/_rels/sheet8.xml.rels'
    rels=ET.fromstring(source.read(rp)) if rp in names else ET.Element('Relationships',xmlns=PKG)
    rid='rIdPrincipalLadder'
    ET.SubElement(rels,f'{{{PKG}}}Relationship',Id=rid,Type=REL+'/drawing',Target=f'../drawings/drawing{drawing_number}.xml')
    ET.SubElement(sheet,f'{{{NS}}}drawing',{f'{{{REL}}}id':rid})
    replacements[sheet_name]=ET.tostring(sheet,encoding='utf-8',xml_declaration=True)
    replacements[rp]=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    ct=ET.fromstring(source.read('[Content_Types].xml'))
    authored_types=ET.fromstring(authored.read('[Content_Types].xml'))
    for part,original in ((chart,'/xl/drawings/charts/chart1.xml'),(drawing,'/xl/drawings/drawing1.xml')):
        mime=next(e.get('ContentType') for e in authored_types if e.get('PartName')==original)
        ET.SubElement(ct,f'{{{CT}}}Override',PartName='/'+part,ContentType=mime)
    replacements['[Content_Types].xml']=ET.tostring(ct,encoding='utf-8',xml_declaration=True)
    output=BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as dest:
        for info in source.infolist():dest.writestr(info,replacements.get(info.filename,source.read(info.filename)))
        for p in replacements.keys()-set(names):dest.writestr(p,replacements[p])
    path.write_bytes(output.getvalue())
    m=path.with_suffix('.manifest.json');data=json.loads(m.read_text());data['workbook_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    m.write_bytes((json.dumps(data,indent=2)+'\n').encode())


if __name__=='__main__':apply(Path(sys.argv[1]))
