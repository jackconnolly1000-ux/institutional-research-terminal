// Build only Lilly's checked review. No network or application dependency is required.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
import {frame,header,subtotal} from './workbook_style.mjs';
const root=process.argv[2];
const source=await fs.readFile(path.join(root,'samples/liquidity_pilots.json'));
const snapshot=JSON.parse(source).snapshots.find(s=>s.ticker==='LLY');
if(snapshot.metrics.cash.accession!=='0000059478-26-000081')throw new Error('Lilly disclosure notes require the checked June filing');
const wb=Workbook.create(),main=wb.worksheets.add('Debt and liquidity');
const data=wb.worksheets.add('Data'),about=wb.worksheets.add('About');
const USD='#,##0,,;(#,##0,,);"-"',date=s=>s?new Date(s+'T00:00:00Z'):null;
const inputs=[],index=new Map();
function leaf(f){
 const key=[f.tag,f.period_start||'',f.period_end,f.accession].join('|');
 if(!index.has(key)){
  const row=inputs.length+2;index.set(key,row);
  inputs.push([f.label,f.value,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,
   f.tag,f.context_id||null,f.scale??null,f.decimals??null,f.source_url||snapshot.source_url,
   f.selection_rule||'',f.detail||'',(f.notes||[]).join(' ')]);
 }
 const cell=`'Data'!B${index.get(key)}`;
 return `IF(ISNUMBER(${cell}),${cell},NA())`;
}
const m=snapshot.metrics;
const formulas={cash:'='+leaf(m.cash),gross_debt:'='+m.gross_debt.inputs.map(leaf).join('+'),
 current_ratio:`=IF(${leaf(m.current_ratio.inputs.current_liabilities)}>0,${leaf(m.current_ratio.inputs.current_assets)}/${leaf(m.current_ratio.inputs.current_liabilities)},NA())`};
for(const key of ['operating_cash_flow','capital_spending']){
 formulas[key]='='+m[key].inputs.map((f,i)=>(i?' + ':'')+`(${f.coefficient}*${leaf(f)})`).join('');
}
Object.assign(formulas,{net_debt:'=B7-B6',free_cash_flow:'=B10-B11',
 ocf_to_debt:'=IF(B7>0,B10/B7,NA())',fcf_to_debt:'=IF(B7>0,B12/B7,NA())'});
data.getRange(`A1:O${inputs.length+1}`).values=[['Input','USD millions','Period start','Period end','Form','Filed','Accession','Tag','Context','Scale','Decimals','Source','Selection rule','Unavailable reason','Notes'],...inputs];
data.getRange(`B2:B${inputs.length+1}`).format.font.color='#0000FF';
data.getRange(`B2:B${inputs.length+1}`).setNumberFormat(USD);
for(const col of ['C','D','F'])data.getRange(`${col}2:${col}${inputs.length+1}`).setNumberFormat('mmm d, yyyy');
main.getRange('A2').values=[['Eli Lilly and Company']];
main.getRange('A3').values=[['Balance sheet June 30, 2026. TTM July 2025–June 2026. USD millions unless ratio or %.']];
main.getRange('A5:D5').values=[['Measure','Value','Period end','Basis / limitation']];
const order=['cash','gross_debt','net_debt','current_ratio','operating_cash_flow','capital_spending','free_cash_flow','ocf_to_debt','fcf_to_debt'];
for(const [i,key] of order.entries()){
 const n=i+6,metric=m[key];
 main.getRange(`A${n}:D${n}`).values=[[metric.label,null,date(metric.period_end),
  key.includes('to_debt')?'Historical TTM flow / period-end debt. Not repayment coverage.':
   [...(metric.notes||[]),...(metric.caveats||[]),...(metric.not_added?['Excluded: '+metric.not_added]:[])].join(' ')||metric.detail||'']];
 main.getRange(`B${n}`).formulas=[[formulas[key]]];
 main.getRange(`B${n}`).format.font.color=formulas[key].includes("'Data'!")?'#008000':'#000000';
}
main.getRange('B6:B14').setNumberFormat(USD);main.getRange('B9').setNumberFormat('0.00"x"');main.getRange('B13:B14').setNumberFormat('0.0%');
main.getRange('C6:C14').setNumberFormat('mmm d, yyyy');
main.getRange('A17').values=[['Selected obligations, separate from borrowing']];
main.getRange('A18:C18').values=[['Item','Disclosed amount / timing','Basis']];
const disclosures=[['Pending AtaiBeckley acquisition','Approximately $2.8B','Potential payment at closing, subject to closing conditions. Not recognized as borrowing.','10-Q MD&A, p. 31'],
 ['Venture fund commitments','Approximately $806M','Expected to be paid over up to ten years. Not recognized as borrowing.','10-Q MD&A, p. 31; Note 8']];
const disclosureHeader=inputs.length+4;
data.getRange(`A${disclosureHeader}:I${disclosureHeader+2}`).values=[['Disclosure','Amount as disclosed','As of','Form','Filed','Accession','Source','Filing location','Conditions'],
 ...disclosures.map(d=>[d[0],d[1],date('2026-06-30'),'10-Q',date('2026-08-05'),snapshot.metrics.cash.accession,snapshot.source_url,d[3],d[2]])];
for(let i=0;i<2;i++){
 const r=disclosureHeader+i+1,n=i+19;
 main.getRange(`A${n}:C${n}`).formulas=[[`='Data'!A${r}`,`='Data'!B${r}`,`='Data'!I${r}`]];
 main.getRange(`A${n}:C${n}`).format.font.color='#008000';
}
main.getRange('A23').values=[['Remaining gaps']];
main.getRange('A24').values=[['June lease liabilities, full maturity review and interest coverage are Unavailable.']];
main.getRange('A25').values=[['Contingencies, tax, collaboration and investment notes require further review.']];
main.getRange('A26').values=[['Sources and selection rules are in Data. No later financing findings are loaded in this review.']];
about.getRange('A1:C6').values=[['Topic','Explanation','Source'],
 ['Scope','Lilly only. Checked snapshot October 14, 2026. Financial statements dated June 30, 2026. Not investment advice.',snapshot.source_url],
 ['Colors','Arial 10. Full USD displayed in millions. Blue reported inputs, green cross-sheet links, black same-sheet calculations. Zero is a dash. Missing inputs are not zero.',null],
 ['Cash generation','Fiscal year + current YTD − prior YTD. Capital spending uses Lilly’s checked other-PP&E tag. FCF excludes acquisitions, dividends and other cash uses.','docs/pilot_cashflow_reconciliation.md'],
 ['Borrowing','Balance-sheet current and noncurrent borrowing are added once. Fair-value table carrying amounts are not added again.','docs/pilot_evidence_lly.md'],
 ['Selected commitments','Descriptions and amount wording retain the June 30 filing basis. They are not added to debt or to each other.',snapshot.source_url]];
for(const s of [main,data,about]){
 s.showGridLines=false;const u=s.getUsedRange();u.format.font.name='Arial';u.format.font.size=10;
 u.format.verticalAlignment='top';u.format.rowHeight=30;u.format.wrapText=true;
}
main.getRange('A2').format.font.bold=true;main.getRange('A2').format.font.size=14;
for(const [col,width] of [['A',42],['B',29],['C',26],['D',73]])main.getRange(`${col}1:${col}26`).format.columnWidth=width;
main.getRange('A6:D14').format.rowHeight=46;main.getRange('A19:C20').format.rowHeight=62;
for(let n=6;n<=14;n++)main.getRange(`A${n}:D${n}`).format.rowHeight=Math.max(46,Math.ceil(String(main.getRange(`D${n}`).values[0][0]).length/73)*14+12);
main.getRange('A3').format.wrapText=false;main.getRange('A24:A26').format.wrapText=false;
for(const a of ['A5:D14','A18:C20'])frame(main,a);
header(main,'A5:D5');header(main,'A18:C18');
for(const n of [7,8,12])subtotal(main,`A${n}:D${n}`);
main.getRange('D6:D14').format.font.bold=false;
const widths=[45,22,20,20,14,20,33,68,20,12,12,75,75,60,90];
widths.forEach((w,i)=>data.getRangeByIndexes(0,i,inputs.length+1,1).format.columnWidth=w);
data.getUsedRange().format.rowHeight=65;data.getRange('A1:O1').format.rowHeight=32;
frame(data,`A1:O${inputs.length+1}`);header(data,'A1:O1');data.freezePanes.freezeRows(1);
frame(data,`A${disclosureHeader}:I${disclosureHeader+2}`);header(data,`A${disclosureHeader}:I${disclosureHeader}`);
data.getRange(`A${disclosureHeader}:I${disclosureHeader+2}`).format.rowHeight=80;
for(const col of ['C','E'])data.getRange(`${col}${disclosureHeader+1}:${col}${disclosureHeader+2}`).setNumberFormat('mmm d, yyyy');
about.getRange('A1:A6').format.columnWidth=28;about.getRange('B1:B6').format.columnWidth=100;about.getRange('C1:C6').format.columnWidth=75;
about.getUsedRange().format.rowHeight=70;about.getRange('A1:C1').format.rowHeight=30;frame(about,'A1:C6');header(about,'A1:C1');
wb.recalculate();
for(const [i,key] of order.entries())if(main.getRange(`B${i+6}`).values[0][0]!==m[key].value)throw new Error('LLY value mismatch '+key);
// A missing source must remain unavailable, including in linked calculations.
const cashCell=data.getRange('B2'),original=cashCell.values;cashCell.values=[[null]];wb.recalculate();
if(typeof main.getRange('B8').values[0][0]==='number')throw new Error('Missing cash became zero');
cashCell.values=original;wb.recalculate();
const out=path.join(root,'samples/lly_liquidity.xlsx');await(await SpreadsheetFile.exportXlsx(wb)).save(out);
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.writeFile(out.replace('.xlsx','.manifest.json'),JSON.stringify({sources:{'liquidity_pilots.json':digest(source)},workbook_sha256:digest(await fs.readFile(out))},null,2)+'\n');
for(const [sheet,range,file] of [['Debt and liquidity','A2:D14','review'],['Debt and liquidity','A17:D26','obligations'],['Data','A1:G6','inputs'],['Data','H1:O6','provenance'],['Data',`A${disclosureHeader}:I${disclosureHeader+2}`,'disclosures'],['About','A1:C6','about']]){
 const img=await wb.render({sheetName:sheet,range,scale:1.1,format:'png'});await fs.writeFile(`lly-${file}.png`,new Uint8Array(await img.arrayBuffer()));
}
await fs.rm(out+'.inspect.ndjson',{force:true});
console.log('Lilly: all nine metrics reconcile; source and missing-value checks passed.');
