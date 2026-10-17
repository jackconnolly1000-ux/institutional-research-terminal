import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {frame,header} from './workbook_style.mjs';

export function addHistorySheet(wb,root,ticker){
 const model=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
  'import json,sys,company_history as h;from pathlib import Path;s=next(s for s in json.loads(Path("samples/liquidity_pilots.json").read_text())["snapshots"] if s["ticker"]==sys.argv[1]);print(json.dumps(h.build(s)))',ticker],{cwd:root,encoding:'utf8'}));
 return {model,sheet:wb.worksheets.add('History')};
}

export async function finishHistorySheet(wb,root,ticker,{model,sheet}){
 const data=wb.worksheets.getItem('Data'),about=wb.worksheets.getItem('About');
 const USD='#,##0,,;(#,##0,,);"-"',date=s=>s?new Date(s+'T00:00:00Z'):null;
 const start=data.getUsedRange().values.length+3,records=[];
 function ref(f){
  const n=start+records.length+1;
  records.push(ticker==='LLY'?[f.label,f.value,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,f.tag,f.context_id||null,f.scale??null,f.decimals??null,f.source_url,f.location||'Annual cash-flow statement',f.detail||'',f.source_sha256||'']:
   [f.label,f.value,f.label,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,f.tag,f.context_id||null,
    ...(ticker==='VST'?[JSON.stringify(f.dimensions||[]),f.scale??null,f.decimals??null]:[f.scale??null,f.decimals??null]),f.source_url,f.location||'Annual cash-flow statement',f.selection_rule||'',...(ticker==='VST'?[]:[JSON.stringify(f.dimensions||[])]),f.source_sha256||'',f.unit]);
  return `IF(ISNUMBER('Data'!B${n}),'Data'!B${n},NA())`;
 }
 const facts=model.annual_facts.map(ref),ocf=ref(model.annual_flows[0]),capex=ref(model.annual_flows[1]);
 const annual={cash:'='+facts[0],gross_debt:ticker==='VST'?null:'='+facts.slice(3).join('+'),net_debt:'=B7-B6',
  current_ratio:`=IF(${facts[2]}>0,${facts[1]}/${facts[2]},NA())`,operating_cash_flow:'='+ocf,capital_spending:'='+capex,
  free_cash_flow:'=B10-B11',ocf_to_debt:'=IF(B7>0,B10/B7,NA())',fcf_to_debt:'=IF(B7>0,B12/B7,NA())'};
 const [owner,op,interest,checks]=ticker==='LLY'?['Debt and liquidity','B40','B46','AND(B44=0)']:ticker==='ORCL'?['Cash analysis','B45','B46',null]:['Cash review','B56','B57','B65=0'];
 const inc=`'${owner}'!${op}`,expense=`'${owner}'!${interest}`;
 annual.interest_coverage=`=IF(AND(${expense}>0${checks?','+(ticker==='LLY'?"'Debt and liquidity'!B44=0":"'Cash review'!B65=0"):''}),${inc}/${expense},NA())`;
 const last=start+records.length,cols=ticker==='LLY'?'O':'R';
 data.getRange(`A${start}:${cols}${start}`).values=data.getRange(`A1:${cols}1`).values;
 data.getRange(`A${start+1}:${cols}${last}`).values=records;
 const df=data.getRange(`A${start}:${cols}${last}`).format;df.font.name='Arial';df.font.size=10;df.wrapText=true;df.rowHeight=70;df.verticalAlignment='top';
 data.getRange(`B${start+1}:B${last}`).setNumberFormat(USD);data.getRange(`B${start+1}:B${last}`).format.font.color='#0000FF';
 for(const c of ticker==='LLY'?['C','D','F']:['D','E','G'])data.getRange(`${c}${start+1}:${c}${last}`).setNumberFormat('mmm d, yyyy');
 frame(data,`A${start}:${cols}${last}`);header(data,`A${start}:${cols}${start}`);
 sheet.showGridLines=false;sheet.getRange('A2').values=[[model.company+' — dated history']];
 sheet.getRange('A3').values=[['USD millions unless x or %. Fiscal year and later TTM both span twelve months and overlap.']];
 sheet.getRange('A5:D5').values=[['Measure','As of / FY ended '+model.annual_end,'As of / TTM ended '+model.period_end,'Basis / limits']];
 for(const [i,r] of model.rows.entries()){
  const basis=r.history_basis;
  const n=i+6;sheet.getRange(`A${n}:D${n}`).values=[[r.label,r.annual_value===null?'Unavailable':null,null,r.annual_detail||basis]];
  if(r.annual_value!==null)sheet.getRange(`B${n}`).formulas=[[annual[r.key]]];
  sheet.getRange(`C${n}`).formulas=[[`='Debt and liquidity'!B${n}`]];
  sheet.getRange(`B${n}:C${n}`).setNumberFormat(r.unit==='ratio'?'0.00"x"':r.unit==='fraction'?'0.0%':USD);
  sheet.getRange(`B${n}`).format.font.color=(annual[r.key]||'').includes("'Data'!")||r.key==='interest_coverage'?'#008000':'#000000';sheet.getRange(`C${n}`).format.font.color='#008000';
  sheet.getRange(`A${n}:D${n}`).format.rowHeight=Math.max(45,Math.ceil(String(r.annual_detail||basis).length/70)*13+10);
 }
 sheet.getRange('A17').values=[['Period definitions']];sheet.getRange('D17').values=[[model.note]];
 sheet.getRange('A18').values=[['Fiscal-year flows']];sheet.getRange('D18').values=[[model.annual_start+' to '+model.annual_end]];
 sheet.getRange('A19').values=[['Later TTM flows']];sheet.getRange('D19').values=[[model.period_start+' to '+model.period_end]];
 sheet.getRange('A1:D19').format.font.name='Arial';sheet.getRange('A1:D19').format.font.size=10;sheet.getRange('A1:D19').format.wrapText=true;sheet.getRange('A1:D19').format.verticalAlignment='top';
 [43,29,29,85].forEach((w,i)=>sheet.getRangeByIndexes(0,i,19,1).format.columnWidth=w);
 sheet.getRange('A2').format.font.bold=true;sheet.getRange('A2').format.font.size=14;sheet.getRange('A2:A3').format.wrapText=false;sheet.getRange('A5:D5').format.rowHeight=32;
 sheet.getRange('A17:D17').format.rowHeight=70;frame(sheet,'A5:D15');header(sheet,'A5:D5');
 const n=about.getUsedRange().values.length+1;about.getRange(`A${n}:C${n}`).values=[['History','Two dated observations per company. Fiscal-year and TTM flows are overlapping twelve-month windows. Unsupported older Vistra borrowing and dependent ratios remain Unavailable.','https://github.com/jackconnolly1000-ux/sec-filing-research-terminal/blob/main/docs/company_history.md']];
 const af=about.getRange(`A${n}:C${n}`).format;af.font.name='Arial';af.font.size=10;af.wrapText=true;af.rowHeight=70;frame(about,`A${n}:C${n}`);
 wb.recalculate();
 for(const [i,r] of model.rows.entries())for(const [col,want] of [['B',r.annual_value],['C',r.value]]){
  const actual=sheet.getRange(`${col}${i+6}`).values[0][0];if(want===null?actual!=='Unavailable':typeof actual!=='number'||Math.abs(actual-want)>1e-8)throw new Error('History mismatch '+r.key);
 }
 for(const [sheetName,range,name] of [['History','A2:D19','table'],['Data',`A${start}:H${last}`,'inputs'],['Data',`${ticker==='LLY'?'L':'M'}${start}:${cols}${last}`,'sources'],['About',`A${n}:C${n}`,'about']]){
  const png=await wb.render({sheetName,range,scale:1.1,format:'png'});await fs.writeFile(path.join(process.cwd(),`${ticker}-history-${name}.png`),new Uint8Array(await png.arrayBuffer()));
 }
 return {history_sha256:JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c','import json,company_history as h;print(json.dumps(h.fingerprint()))'],{cwd:root,encoding:'utf8'}))};
}
