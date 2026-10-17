// Reuse the checked snapshot for each company's core metrics and source-linked calculations.
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {frame,header,subtotal} from './workbook_style.mjs';

export function addRatioSheet(wb,root,ticker){
 const snapshot=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
  'import json,sys,ratio_review as r;from pathlib import Path;s=next(s for s in json.loads(Path("samples/liquidity_pilots.json").read_text())["snapshots"] if s["ticker"]==sys.argv[1]);print(json.dumps({"snapshot":s,"review":r.build(s)}))',ticker],{cwd:root,encoding:'utf8'}));
 return {...snapshot,sheet:ticker==='LLY'?null:wb.worksheets.add('Debt and liquidity')};
}

export async function finishRatioSheet(wb,root,ticker,state){
 const sheet=state.sheet||wb.worksheets.getItem('Debt and liquidity'),data=wb.worksheets.getItem('Data');
 const {snapshot,review}=state,m=snapshot.metrics,USD='#,##0,,;(#,##0,,);"-"',date=s=>s?new Date(s+'T00:00:00Z'):null;
 const start=data.getUsedRange().values.length+3,records=[],index=new Map();
 // Lilly's existing input block has these same facts. Keep its rows and all references intact.
 let llyRow=2;
 function leaf(f){
  const key=[f.tag,f.period_start||'',f.period_end,f.accession].join('|');
  if(!index.has(key)){
   const n=ticker==='LLY'?llyRow++:start+records.length+1;
   index.set(key,n);
   if(ticker!=='LLY')records.push(['Ratio input: '+f.label,f.value,f.label,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,
    f.tag,f.context_id||null,...(ticker==='VST'?[JSON.stringify(f.dimensions||[]),f.scale??null,f.decimals??null]:[f.scale??null,f.decimals??null]),
    f.source_url||snapshot.source_url,'Checked balance sheet / cash-flow statement',f.selection_rule||f.detail||'',
    ...(ticker==='VST'?[]:[JSON.stringify(f.dimensions||[])]),f.source_sha256||null,f.unit]);
  }
  const c=`'Data'!B${index.get(key)}`;return `IF(ISNUMBER(${c}),${c},NA())`;
 }
 const cash=leaf(m.cash),parts=m.gross_debt.inputs.map(leaf),cl=leaf(m.current_ratio.inputs.current_liabilities),ca=leaf(m.current_ratio.inputs.current_assets);
 const formulas={cash:'='+cash,gross_debt:`=IF(AND(${parts.map(x=>x+'>=0').join(',')}),${parts.join('+')},NA())`,
  net_debt:'=B7-B6',current_ratio:`=IF(${cl}>0,${ca}/${cl},NA())`,free_cash_flow:'=B10-B11',
  ocf_to_debt:'=IF(B7>0,B10/B7,NA())',fcf_to_debt:'=IF(B7>0,B12/B7,NA())',
  interest_coverage:ticker==='LLY'?'=B50':review.coverage_cell};
 for(const key of ['operating_cash_flow','capital_spending'])formulas[key]='='+m[key].inputs.map(f=>`(${f.coefficient}*${leaf(f)})`).join('+');
 if(ticker!=='LLY'){
  const end=start+records.length;
  data.getRange(`A${start}:R${start}`).values=data.getRange('A1:R1').values;
  data.getRange(`A${start+1}:R${end}`).values=records;
  const fmt=data.getRange(`A${start}:R${end}`).format;fmt.font.name='Arial';fmt.font.size=10;fmt.wrapText=true;fmt.verticalAlignment='top';fmt.rowHeight=86;
  data.getRange(`B${start+1}:B${end}`).setNumberFormat(USD);data.getRange(`B${start+1}:B${end}`).format.font.color='#0000FF';
  for(const col of ['D','E','G'])data.getRange(`${col}${start+1}:${col}${end}`).setNumberFormat('mmm d, yyyy');
  frame(data,`A${start}:R${end}`);header(data,`A${start}:R${start}`);
  sheet.showGridLines=false;sheet.getRange('A2').values=[[review.company]];
  sheet.getRange('A3').values=[['Balance sheet '+review.period_end+'. TTM '+review.period_start+' to '+review.period_end+'. USD millions unless x or %.']];
  sheet.getRange('A2:A3').format.wrapText=false;
  sheet.getRange('A2').format.font.bold=true;sheet.getRange('A2').format.font.size=14;
 }
 sheet.getRange('A5:D5').values=[['Measure','Value (USD millions / x / %)','Period end','Formula / basis / limitation']];
 for(const [i,r] of review.rows.entries()){
  const n=i+6;
  const note=r.basis+(r.key==='interest_coverage'?' See the detailed interest build for composition and limitations.':r.detail?' '+r.detail:'');
  sheet.getRange(`A${n}:D${n}`).values=[[r.label,null,date(r.period_end),note]];
  if(r.value===null)sheet.getRange(`B${n}`).values=[['Unavailable']];
  else sheet.getRange(`B${n}`).formulas=[[formulas[r.key]]];
  sheet.getRange(`B${n}`).setNumberFormat(r.unit==='ratio'?'0.00"x"':r.unit==='fraction'?'0.0%':USD);
  sheet.getRange(`B${n}`).format.font.color=formulas[r.key].includes("'Data'!")||ticker!=='LLY'&&r.key==='interest_coverage'?'#008000':'#000000';
  sheet.getRange(`A${n}:D${n}`).format.rowHeight=Math.max(50,Math.ceil(note.length/70)*13+14);
 }
 const table=sheet.getRange('A5:D15');table.format.font.name='Arial';table.format.font.size=10;table.format.wrapText=true;table.format.verticalAlignment='top';
 [42,29,23,78].forEach((w,i)=>sheet.getRangeByIndexes(0,i,15,1).format.columnWidth=w);
 sheet.getRange('C6:C15').setNumberFormat('mmm d, yyyy');frame(sheet,'A5:D15');header(sheet,'A5:D5');
 for(const n of [7,8,12])subtotal(sheet,`A${n}:D${n}`);
 sheet.getRange('D6:D15').format.font.bold=false;
 if(ticker!=='LLY'){
  const notes=[['Periods','All cash-flow and interest ratios use the TTM above. FY + current YTD − prior YTD. Balance-sheet denominators use the period end, not average debt.'],
   ['Historical interest basis',review.rows[9].basis+' '+review.rows[9].detail],
   ['Recalculation','The historical interest ratio links to its existing detailed build. Editing source inputs updates formulas; the checked narrative requires a new review.'],
   ['Interpretation','Negative FCF and negative net debt are retained. Historical ratios do not establish future cash available, covenant compliance or funding coverage. Different company bases are not a ranking.']];
  sheet.getRange('A17:B21').values=[['Method','Explanation'],...notes];
  sheet.getRange('A17:D21').format.font.name='Arial';sheet.getRange('A17:D21').format.font.size=10;
  sheet.getRange('A17:D21').format.wrapText=true;sheet.getRange('A17:D21').format.verticalAlignment='top';
  // Put long notes in the existing wide basis column rather than a narrow value column.
  for(let i=0;i<notes.length;i++){sheet.getRange(`B${18+i}`).values=[[null]];sheet.getRange(`D${18+i}`).values=[[notes[i][1]]];}
  sheet.getRange('B17').values=[[null]];sheet.getRange('D17').values=[['Explanation']];
  [60,145,60,72].forEach((h,i)=>sheet.getRange(`A${18+i}:D${18+i}`).format.rowHeight=h);
  frame(sheet,'A17:D21');header(sheet,'A17:D17');
 }
 wb.recalculate();
 for(const [i,r] of review.rows.entries()){
  const actual=sheet.getRange(`B${i+6}`).values[0][0];
  if(r.value!==null&&(typeof actual!=='number'||Math.abs(actual-r.value)>Math.max(1e-12,Math.abs(r.value)*1e-12)))throw new Error(ticker+' ratio mismatch '+r.key);
 }
 // Exercise missing vs zero, negative net debt, invalid debt and the positive-denominator rule.
 const cashCell=data.getRange(`B${index.values().next().value}`),saved=cashCell.values;
 for(const [input,want] of [[null,null],[0,m.gross_debt.value],[m.gross_debt.value+1,-1]]){
  cashCell.values=[[input]];wb.recalculate();const value=sheet.getRange('B8').values[0][0];
  if(want===null?typeof value==='number':value!==want)throw new Error('Cash/net-debt boundary failed');
 }
 cashCell.values=saved;
 const debtCells=m.gross_debt.inputs.map(f=>data.getRange(`B${index.get([f.tag,f.period_start||'',f.period_end,f.accession].join('|'))}`));
 const savedDebt=debtCells.map(c=>c.values);
 debtCells.forEach(c=>c.values=[[0]]);wb.recalculate();
 if(sheet.getRange('B7').values[0][0]!==0||typeof sheet.getRange('B13').values[0][0]==='number')throw new Error('Zero debt divided');
 debtCells.forEach((c,i)=>c.values=savedDebt[i]);debtCells[0].values=[[-1]];wb.recalculate();
 if(typeof sheet.getRange('B7').values[0][0]==='number')throw new Error('Negative borrowing used');
 debtCells.forEach((c,i)=>c.values=savedDebt[i]);wb.recalculate();
 const liabilities=data.getRange(`B${index.get([m.current_ratio.inputs.current_liabilities.tag,'',review.period_end,m.current_ratio.inputs.current_liabilities.accession].join('|'))}`),savedLiabilities=liabilities.values;
 for(const value of [null,0,-1]){
  liabilities.values=[[value]];wb.recalculate();
  if(typeof sheet.getRange('B9').values[0][0]==='number')throw new Error('Missing or nonpositive current liabilities divided');
 }
 liabilities.values=savedLiabilities;
 const flow=m.operating_cash_flow.inputs[0],ocfCell=data.getRange(`B${index.get([flow.tag,flow.period_start,flow.period_end,flow.accession].join('|'))}`),savedOcf=ocfCell.values;
 ocfCell.values=[[null]];wb.recalculate();
 for(const cell of ['B10','B12','B13','B14'])if(typeof sheet.getRange(cell).values[0][0]==='number')throw new Error('Missing OCF became a cash-flow ratio');
 ocfCell.values=savedOcf;wb.recalculate();
 const about=wb.worksheets.getItem('About'),n=about.getUsedRange().values.length+1;
 about.getRange(`A${n}:C${n}`).values=[['Ratio reconciliation','Debt and liquidity shows current ratio, same-filing net debt, TTM OCF/debt and FCF/debt, and historical interest coverage. Denominator definitions and capital-spending bases differ by company. Values are historical, not future funding coverage.','https://github.com/jackconnolly1000-ux/sec-filing-research-terminal/blob/main/docs/ratio_reconciliation.md']];
 const af=about.getRange(`A${n}:C${n}`).format;af.font.name='Arial';af.font.size=10;af.wrapText=true;af.verticalAlignment='top';af.rowHeight=86;frame(about,`A${n}:C${n}`);
 wb.recalculate();
 console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
 const ranges=[['Debt and liquidity','A2:D15','metrics'],['About',`A${n}:C${n}`,'about']];
 if(ticker==='LLY')ranges.push(['Debt and liquidity','A17:D26','existing-notes'],['Debt and liquidity','A30:D55','existing-coverage']);
 if(ticker!=='LLY')ranges.push(['Debt and liquidity','A17:D21','method'],['Data',`A${start}:H${start+records.length}`,'inputs'],['Data',`I${start}:R${start+records.length}`,'sources']);
 for(const [sheetName,range,name] of ranges){
  const png=await wb.render({sheetName,range,scale:1.2,format:'png'});
  await fs.writeFile(path.join(process.cwd(),`${ticker}-ratios-${name}.png`),new Uint8Array(await png.arrayBuffer()));
 }
 return {ratios_sha256:JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c','import json,ratio_review as r;print(json.dumps(r.fingerprint()))'],{cwd:root,encoding:'utf8'}))};
}
