// The same checked interpretation feeds the application and each company export.
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {frame,header} from './workbook_style.mjs';

export function addFundingSheet(wb,root,ticker){
 const model=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
  'import json,sys,funding_conclusions as f;r=f.load(sys.argv[1]);assert r is not None;print(json.dumps(r))',ticker],{cwd:root,encoding:'utf8'}));
 const sheet=wb.worksheets.add('Funding conclusion');
 sheet.showGridLines=false;
 sheet.getRange('A1:B18').format.font.name='Arial';sheet.getRange('A1:B18').format.font.size=10;
 sheet.getRange('A1:A18').format.columnWidth=26;
 sheet.getRange('B1:B18').format.columnWidth=108;
 sheet.getRange('A1:B18').format.verticalAlignment='top';
 sheet.getRange('A1:B18').format.wrapText=true;
 sheet.getRange('A2').values=[[model.company+' funding conclusion']];
 sheet.getRange('A2').format.font.bold=true;sheet.getRange('A2').format.font.size=14;
 sheet.getRange('A2').format.wrapText=false;sheet.getRange('A2:B2').format.rowHeight=26;
 sheet.getRange('A3').values=[['Balance sheet '+model.period_end+'. Interpretation checked '+model.reviewed+'. Source dates remain historical.']];
 sheet.getRange('A3').format.wrapText=false;sheet.getRange('A3:B3').format.rowHeight=24;
 sheet.getRange('A5:B5').values=[['Question','Checked interpretation']];header(sheet,'A5:B5');
 sheet.getRange('A6:B10').values=[['Conclusion',model.conclusion],...model.rows.map(([label,text])=>[label,text])];
 sheet.getRange('A6:A10').format.font.bold=true;
 for(let row=6;row<=10;row++)sheet.getRange(`A${row}:B${row}`).format.rowHeight=row===6?55:76;
 frame(sheet,'A5:B10');
 sheet.getRange('A12:B12').values=[['Historical interest coverage','Multiple; historical accrual earnings / interest, not repayment coverage']];
 header(sheet,'A12:B12');sheet.getRange('A12:B12').format.rowHeight=32;
 sheet.getRange('A13').values=[['TTM coverage (x)']];
 sheet.getRange('B13').setNumberFormat('0.00"x"');
 sheet.getRange('A13:B13').format.font.italic=true;sheet.getRange('B13').format.font.color='#008000';
 sheet.getRange('A14:B14').values=[['Company-specific basis',model.coverage_basis]];
 sheet.getRange('A15:B15').values=[['Interpretation across companies',model.comparison]];
 sheet.getRange('A14:B14').format.rowHeight=72;sheet.getRange('A15:B15').format.rowHeight=88;
 frame(sheet,'A12:B15');
 sheet.getRange('A17:B17').values=[['Future funding coverage','Unavailable: payment timing, accessible resources and future cash generation are not jointly established.']];
 sheet.getRange('A17:B17').format.rowHeight=42;sheet.getRange('A17').format.font.bold=true;
 sheet.getRange('A18:B18').values=[['Source interpretation','Narrative reflects the checked source snapshot. Editing workbook inputs updates calculations but requires a new review of the narrative.']];
 sheet.getRange('A18:B18').format.rowHeight=42;
 // Filing provenance stays in the existing Data area. These are textual source records,
 // separate from each workbook's unchanged numerical inputs and calculations.
 return {sheet,model};
}

export async function finishFundingSheet(wb,root,ticker,funding){
 const {sheet,model}=funding;
 const ref=model.coverage_formula.slice(1);
 sheet.getRange('B13').formulas=[[`=IF(ISNUMBER(${ref}),${ref},NA())`]];
 wb.recalculate();
 if(Math.abs(sheet.getRange('B13').values[0][0]-model.coverage)>1e-12)throw new Error('Funding coverage link differs from checked model');
 // The output is a link, not another calculation. Editing the owning result must update it.
 const match=model.coverage_formula.match(/^='(.+)'!(.+)$/),owner=wb.worksheets.getItem(match[1]).getRange(match[2]);
 const formula=owner.formulas;
 owner.values=[[null]];wb.recalculate();
 if(typeof sheet.getRange('B13').values[0][0]==='number')throw new Error('Missing source became summary coverage');
 owner.formulas=formula;wb.recalculate();
 const data=wb.worksheets.getItem('Data'),start=data.getUsedRange().values.length+3;
 const records=[];
 for(const [topic,,sources] of [...model.rows,['Historical coverage',null,model.coverage_sources]])for(const s of sources){
  records.push([topic,s.label,s.accession,s.location,s.url]);
 }
 const urlColumn={LLY:'L',ORCL:'M',VST:'N'}[ticker];
 data.getRange(`A${start}:D${start+records.length}`).values=[['Funding conclusion evidence','Filing / filed date','Accession','Location'],...records.map(r=>r.slice(0,4))];
 data.getRange(`${urlColumn}${start}:${urlColumn}${start+records.length}`).values=[['SEC source'],...records.map(r=>[r[4]])];
 for(const area of [`A${start}:D${start+records.length}`,`${urlColumn}${start}:${urlColumn}${start+records.length}`]){
  data.getRange(area).format.font.name='Arial';data.getRange(area).format.font.size=10;
  data.getRange(area).format.wrapText=true;data.getRange(area).format.verticalAlignment='top';
  data.getRange(area).format.rowHeight=72;frame(data,area);
 }
 header(data,`A${start}:D${start}`);header(data,`${urlColumn}${start}`);
 wb.recalculate();
 console.log((await wb.inspect({kind:'region',sheetId:'Funding conclusion',range:'A12:B17',maxChars:1800})).ndjson);
 for(const [range,name] of [['A2:B10','conclusion'],['A12:B18','basis'],[`A${start}:D${start+records.length}`,'evidence'],[`${urlColumn}${start}:${urlColumn}${start+records.length}`,'source-links']]){
  const png=await wb.render({sheetName:['evidence','source-links'].includes(name)?'Data':'Funding conclusion',range,scale:1.4,format:'png'});
  await fs.writeFile(path.join(process.cwd(),`${ticker}-funding-${name}.png`),new Uint8Array(await png.arrayBuffer()));
 }
 return {funding_sha256:JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
  'import json,funding_conclusions as f;print(json.dumps(f.fingerprint()))'],{cwd:root,encoding:'utf8'}))};
}
