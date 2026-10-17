// Run a copy from an OS temporary directory with the Codex Artifact Tool runtime.
// Existing company parts are preserved by apply_export_layout.py; this authors layout only.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {Workbook,FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
import {frame,header} from './workbook_style.mjs';
const root=process.argv[2],out=process.argv[3]||process.cwd();
const py=process.env.CODEX_PRIMARY_RUNTIME_PYTHON;
const run=code=>JSON.parse(execFileSync(py,['-c',code],{cwd:root,encoding:'utf8'}));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.mkdir(out,{recursive:true});
const ranges={};
for(const stem of (process.env.SCENARIO_ONLY?[]:['lly','oracle','vistra'])){
 const base=`${root}/samples/${stem}_liquidity.xlsx`;
 const records=JSON.parse(execFileSync(py,[`${root}/tests/offline/export_layout_records.py`,base],{cwd:root,encoding:'utf8'}));
 const wb=Workbook.create();
 ranges[stem]=[];
 for(const [name,item] of Object.entries(records)){
  const s=wb.worksheets.add(name),rows=item.rows,cols=item.cols;
  s.getRangeByIndexes(0,0,rows,cols).format.font.name='Arial';s.getRangeByIndexes(0,0,rows,cols).format.font.size=10;
  s.getRangeByIndexes(0,0,rows,cols).format.wrapText=true;
  for(const [ref,value,color,fmt,bold,italic] of item.cells){const cell=s.getRange(ref);cell.values=[[value]];cell.format.font.color='#'+color;cell.format.font.bold=!!bold;cell.format.font.italic=!!italic;if(typeof value==='number')cell.setNumberFormat(fmt);}
  for(const [row,h] of Object.entries(item.heights))s.getRangeByIndexes(Number(row)-1,0,1,cols).format.rowHeight=h;
  for(const [col,width] of Object.entries(item.widths))s.getRange(`${col}1:${col}${rows}`).format.columnWidth=width;
  // Keep the established blocks. Add faint separators only across populated data columns.
  const n=name==='Core charts'?4:cols;
  const last=s.getRangeByIndexes(0,0,rows,n);
  last.format.borders={insideVertical:{style:'thin',color:'#E1E5EA'}};
  s.showGridLines=false;
  wb.recalculate();
  ranges[stem].push([name,rows,n]);
  const png=await wb.render({sheetName:name,range:s.getRangeByIndexes(0,0,Math.min(rows,12),n).address.split('!').pop(),scale:1});
  await fs.writeFile(`${out}/${stem}-${name.replaceAll(' ','_')}.png`,new Uint8Array(await png.arrayBuffer()));
 }
 await(await SpreadsheetFile.exportXlsx(wb)).save(`${out}/${stem}-layout.xlsx`);
}
// The optional summary owns no detailed Oracle schedules; those remain in its primary workbook.
if(!process.env.SCENARIO_ONLY){
const original=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/samples/liquidity_pilots.xlsx`));
const combined=Workbook.create();
for(const name of ['Debt and liquidity','Liquidity inputs','About'])combined.worksheets.add(name);
for(const name of ['Debt and liquidity','Liquidity inputs','About']){
 const old=original.worksheets.getItem(name),s=combined.worksheets.getItem(name),r=old.getUsedRange();
 s.getRange('A1').write(r.values);
 const formulas=r.formulas;
 for(let i=0;i<formulas.length;i++)for(let j=0;j<formulas[i].length;j++)if(formulas[i][j])s.getCell(i,j).formulas=[[formulas[i][j]]];
 const rows=r.values.length,cols=Math.max(...r.values.map(x=>x.length));
 s.showGridLines=false;
 const f=s.getRangeByIndexes(0,0,rows,cols).format;
 f.font.name='Arial';f.font.size=10;f.wrapText=true;f.verticalAlignment='top';
 const widths=name==='About'?[30,110]:name==='Debt and liquidity'?[10,36,20,28,18,55,18,80]:[10,33,48,20,18,14,18,30,65,60,90,65,26,12,12,18,18,16];
 widths.forEach((w,i)=>s.getRangeByIndexes(0,i,rows,1).format.columnWidth=w);
 s.getRangeByIndexes(0,0,rows,cols).format.rowHeight=name==='About'?65:48;
 frame(s,s.getRangeByIndexes(0,0,rows,cols).address.split('!').pop());
 header(s,s.getRangeByIndexes(0,0,1,cols).address.split('!').pop());s.freezePanes.freezeRows(1);
 if(name==='Liquidity inputs'){s.getRange(`D2:D${rows}`).setNumberFormat('#,##0,,;(#,##0,,);"-"');s.getRange(`D2:D${rows}`).format.font.color='#0000FF';}
 if(name==='Debt and liquidity')for(let i=1;i<rows;i++){
  s.getCell(i,2).setNumberFormat(r.values[i][3].startsWith('USD')?'#,##0,,;(#,##0,,);"-"':r.values[i][3].startsWith('fraction')?'0.0%':'0.00"x"');
  s.getCell(i,2).format.font.color=formulas[i][2]?.includes('Liquidity inputs')?'#008000':'#000000';
 }
}
const about=combined.worksheets.getItem('About');
about.getRange('A7:B9').values=[['Scope and dates','Core metric summary only. LLY/VST: June 30, 2026; ORCL: August 31, 2026. Fiscal calendars and capital-spending definitions differ. This is not a peer ranking or a complete obligations review.'],['Full reviews','Use the primary LLY, ORCL and VST downloads for funding conclusions, leases, interest coverage, history, charts and company-specific obligations.'],['Source links','Source URLs are retained in Liquidity inputs. Select a URL to open its filing.']];
about.getRange('A7:B9').format.rowHeight=68;frame(about,'A1:B9');
combined.recalculate();
await(await SpreadsheetFile.exportXlsx(combined)).save(`${out}/combined.xlsx`);
for(const name of ['Debt and liquidity','Liquidity inputs','About']){
 const s=combined.worksheets.getItem(name),r=s.getUsedRange();
 const img=await combined.render({sheetName:name,range:s.getRangeByIndexes(0,0,Math.min(r.values.length,12),r.values[0].length).address.split('!').pop(),scale:1});
 await fs.writeFile(`${out}/combined-${name.replaceAll(' ','_')}.png`,new Uint8Array(await img.arrayBuffer()));
}
}
const data=run("import json,scenario_export as e,liquidity_simulation as l; i=l.oracle_inputs();ds=l.oracle_decisions();rs=[(l.simulate(i,d),d) for d in ds];ms=[(d,r,l.monthly_path(i,d)) for r,d in rs];print(json.dumps(e.tables(i,rs,10000,2026,l.compare_correlations(i,ds[0]),[(d,l.outside_use_effects(i,l.oracle_uses_outside_model(),d)) for d in ds],l.oracle_uses_outside_model(),ms),default=str))");
const w=Workbook.create(),meta={sheets:{}};
for(const name of Object.keys(data))w.worksheets.add(name);
const ratios={'Results':{10:'0.0%'},'Correlation':{2:'+0.0;-0.0;0.0',3:'+0.00;-0.00;0.00',7:'0.0%'},'Outside-use effects':{6:'0.0%'},'Monthly path':{3:'0.0%',4:'0.0%',9:'0.0%',10:'0.0%'},'Monthly path by month':{7:'0.0%'}};
let id=0;
for(const [name,rows] of Object.entries(data)){
 const s=w.worksheets.getItem(name),n=rows.length,c=Math.max(...rows.map(r=>r.length));
 const padded=rows.map(r=>Array.from({length:c},(_,i)=>r[i]??null));
 s.getRange('A1').write(padded.map(row=>row.map(v=>v&&typeof v==='object'?v.value:v)));s.showGridLines=false;
 const f=s.getRangeByIndexes(0,0,n,c).format;f.font.name='Arial';f.font.size=10;f.wrapText=true;f.verticalAlignment='top';
 const widths=name==='About'?[30,120]:name==='Scenario'?[39,40,24,24,24,105]:name==='Data'?[45,30,26,19,19,16,19,32,105,75,40,100]:name==='Uses not modelled'?[49,38,25,105,100,58]:name==='Results'?[48,24,24,27,26,26,28,24,27,30,38]:name==='Monthly path'?[48,27,30,32,28,29,32,40,30,30]:name==='Monthly path by month'?[48,19,20,28,28,30,30]:name==='Outside-use effects'?[48,56,28,30,29,30,35]:[48,26,26,28,28,28,30];
 widths.forEach((width,k)=>s.getRangeByIndexes(0,k,n,1).format.columnWidth=width);
 for(let r=0;r<n;r++){
  const maxLines=Math.max(...padded[r].map((v,k)=>typeof v==='string'?Math.ceil(v.length/(widths[k]*.95)):1));
  s.getRangeByIndexes(r,0,1,c).format.rowHeight=Math.max(32,Math.min(250,maxLines*14+12));
  for(let k=0;k<c;k++){
   const cell=s.getCell(r,k),v=padded[r][k];
   if(v&&typeof v==='object'&&v.formula){cell.formulas=[[v.formula]];cell.setNumberFormat('#,##0,,;(#,##0,,);"-"');cell.format.font.color='#008000';}
   if(typeof v==='number'){
    const rho=name==='Scenario'&&r===11;
    cell.setNumberFormat(rho?'+0.0;-0.0;0.0':ratios[name]?.[k+1]||'#,##0,,;(#,##0,,);"-"');
    cell.format.font.color=['Scenario','Data'].includes(name)?'#0000FF':'#000000';
   }
   if(name==='Monthly path by month'&&k===2&&r>0){cell.values=[[new Date(v+'T00:00:00Z')]];cell.setNumberFormat('yyyy-mm-dd');}
   if(name==='Data'&&[3,4,6].includes(k)&&r>0&&v){cell.values=[[new Date(v+'T00:00:00Z')]];cell.setNumberFormat('yyyy-mm-dd');}
  }
 }
 const first=name==='Scenario'?5:1;
 frame(s,s.getRangeByIndexes(first-1,0,n-first+1,c).address.split('!').pop());
 header(s,s.getRangeByIndexes(first-1,0,1,c).address.split('!').pop());
 s.freezePanes.freezeRows(first);
 if(name==='Scenario'){
  s.getRange('A1:F3').format.wrapText=false;s.getRange('A1').format.font.bold=true;
  s.getRange('A2').format.font.color='#775B20';s.getRange('A1:F3').format.rowHeight=25;
 }
 meta.sheets[name]={path:`xl/worksheets/sheet${++id}.xml`,rows:n,cols:c};
}
w.recalculate();
for(const [name,info] of Object.entries(meta.sheets)){
 const s=w.worksheets.getItem(name);
 for(let start=0;start<info.rows;start+=15){
  const img=await w.render({sheetName:name,range:s.getRangeByIndexes(start,0,Math.min(info.rows-start,15),info.cols).address.split('!').pop(),scale:1});
  await fs.writeFile(`${out}/scenario-${name.replaceAll(' ','_')}-${start}.png`,new Uint8Array(await img.arrayBuffer()));
 }
}
const dest=`${root}/samples/scenario_template.xlsx`;
await(await SpreadsheetFile.exportXlsx(w)).save(dest);
meta.sha256=digest(await fs.readFile(dest));
await fs.writeFile(dest.replace('.xlsx','.manifest.json'),JSON.stringify(meta,null,2)+'\n');
if(!process.env.SCENARIO_ONLY)await fs.writeFile(`${out}/layout-ranges.json`,JSON.stringify(ranges));
console.log('Layouts rendered; template and combined workbook authored.');
