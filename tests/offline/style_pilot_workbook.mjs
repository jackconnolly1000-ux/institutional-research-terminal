// Restyle the existing pilot export with Artifact Tool, preserving its formulas and native chart.
// First run accepts a current downloaded workbook; subsequent styling runs use the saved export.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
import {frame, header, subtotal} from './workbook_style.mjs';

const root=process.argv[2], source=process.argv[3]||path.join(root,'samples/liquidity_pilots.xlsx');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(source));
const samples=JSON.parse(await fs.readFile(path.join(root,'samples/liquidity_pilots.json'),'utf8'));
const sheets=[['Debt and liquidity',28,'H',[9,38,21,26,20,62,17,85]],
  ['Liquidity inputs',36,'R',[9,32,53,21,20,14,20,33,68,62,65,65,24,12,12,20,18,14]],
  ['About',7,'B',[33,105]],['Other obligations',10,'I',[9,35,29,20,34,34,34,65,85]],
  ['Oracle maturities',18,'F',[41,20,20,23,29,65]],
  ['Oracle debt inputs',12,'O',[39,22,20,20,20,14,20,33,65,22,12,12,65,45,75]],
  ['Oracle financing',7,'N',[20,20,20,55,22,46,14,20,33,65,25,65,65,95]]];
const before=new Map();
for(const [name,last,col,widths] of sheets){
  const s=wb.worksheets.getItem(name),range=`A1:${col}${last}`;
  before.set(name,JSON.stringify({values:s.getRange(range).values,formulas:s.getRange(range).formulas}));
  s.showGridLines=false;
  const f=s.getRange(range).format;f.font.name='Arial';f.font.size=10;f.wrapText=true;f.verticalAlignment='top';
  widths.forEach((width,i)=>s.getRangeByIndexes(0,i,last,1).format.columnWidth=width);
  // Fit each record to its actual text instead of leaving every row at the tallest record's height.
  const values=s.getRange(range).values;
  for(let row=1;row<last;row++){
    const lines=Math.max(1,...values[row].map((value,col)=>typeof value==='string'
      ? Math.ceil(value.length/(widths[col]*1.1)):1));
    s.getRange(`A${row+1}:${col}${row+1}`).format.rowHeight=Math.max(26,lines*14+8);
  }
  s.getRange(`A1:${col}1`).format.rowHeight=32;
  frame(s,range);header(s,`A1:${col}1`);s.freezePanes.freezeRows(1);
}
const main=wb.worksheets.getItem('Debt and liquidity');
// Separate the company blocks while leaving every financial formula and source row intact.
for(const n of [11,20])main.getRange(`A${n}:H${n}`).format.borders={top:{style:'thin',color:'#BBC3CD'}};
main.getRange('A2:A28').format.font.bold=true;
const raw=wb.worksheets.getItem('Liquidity inputs');
raw.getRange('D2:D36').format.horizontalAlignment='right';
const maturity=wb.worksheets.getItem('Oracle maturities');
for(const n of [8,12,15,17])subtotal(maturity,`A${n}:F${n}`);
maturity.getRange('D10').setNumberFormat('#,##0.00,,;(#,##0.00,,);0.00');
maturity.getRange('D14').setNumberFormat('#,##0.00,,;(#,##0.00,,);0.00');
// The importer does not retain standalone AutoFilter metadata. Native tables retain the
// same filterable records without changing any formula or adding a data row.
for(const [name,last,col,tableName] of [['Oracle maturities',18,'F','OracleMaturities'],
  ['Oracle debt inputs',12,'O','OracleDebtInputs'],['Oracle financing',7,'N','OracleFinancing']]){
  const sheet=wb.worksheets.getItem(name);
  if(!sheet.tables.items.length){
    const table=sheet.tables.add(`A1:${col}${last}`,true,tableName);
    table.style='TableStyleLight1';table.showFilterButton=true;
  }
  sheet.getRange(`A2:${col}${last}`).format.fill='#FFFFFF';
}
for(const [name,last,col] of sheets){
  const s=wb.worksheets.getItem(name),range=`A1:${col}${last}`;
  if(before.get(name)!==JSON.stringify({values:s.getRange(range).values,formulas:s.getRange(range).formulas})){
    throw new Error('Styling changed a cell value or formula on '+name);
  }
}
raw.getRange('D1').values=[['USD millions (stored USD)']];
// Frozen exported numbers must still match every metric and source snapshot.
wb.recalculate();
let row=2;
for(const snapshot of samples.snapshots){
  for(const metric of Object.values(snapshot.metrics)){
    if(main.getRange(`C${row}`).values[0][0]!==metric.value)throw new Error('Snapshot differs at row '+row);
    row++;
  }
}
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!',options:{useRegex:true,maxResults:15},maxChars:1000})).ndjson);
const out=path.join(root,'samples/liquidity_pilots.xlsx');
await(await SpreadsheetFile.exportXlsx(wb)).save(out);
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const sources={};
for(const name of ['liquidity_pilots.json','oracle_financing.json'])sources[name]=digest(await fs.readFile(path.join(root,'samples',name)));
await fs.writeFile(out.replace('.xlsx','.manifest.json'),JSON.stringify({sources,workbook_sha256:digest(await fs.readFile(out))},null,2)+'\n');
for(const [name,range,file] of [['Debt and liquidity','A1:E11','summary'],['Debt and liquidity','F1:H5','summary-notes'],
  ['Liquidity inputs','A1:G6','inputs'],['Liquidity inputs','H1:R5','provenance'],['About','A1:B7','about'],
  ['Other obligations','A1:F5','obligations'],['Other obligations','G1:I5','obligation-sources'],
  ['Oracle maturities','A1:F18','maturities'],['Oracle maturities','H2:Q10','chart'],
  ['Oracle debt inputs','A1:H6','debt-inputs'],['Oracle debt inputs','I1:O6','debt-sources'],
  ['Oracle financing','A1:F7','financing'],['Oracle financing','G1:N7','financing-sources']]){
  const img=await wb.render({sheetName:name,range,scale:1.1,format:'png'});
  await fs.writeFile(`pilots-${file}.png`,new Uint8Array(await img.arrayBuffer()));
}
await fs.rm(out+'.inspect.ndjson',{force:true});
console.log('Styled seven pilot sheets; source values and formulas preserved.');
