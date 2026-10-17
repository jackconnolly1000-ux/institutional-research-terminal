import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {frame,header} from './workbook_style.mjs';
export async function finishExportGuide(wb,root,ticker){
 const model=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c','import json,sys,export_guide as g;print(json.dumps({"contents":g.contents(sys.argv[1]),"fingerprint":g.fingerprint()}))',ticker],{cwd:root,encoding:'utf8'}));
 for(const [name] of model.contents)if(!wb.worksheets.getItem(name))throw Error('Missing export section '+name);
 const sheet=wb.worksheets.getItem('Funding conclusion'),last=20+model.contents.length;
 sheet.getRange(`A20:B${last}`).values=[['Workbook contents — select the named tab','Question / evidence'],...model.contents];
 const fmt=sheet.getRange(`A20:B${last}`).format;fmt.font.name='Arial';fmt.font.size=10;fmt.wrapText=true;fmt.verticalAlignment='top';fmt.rowHeight=44;frame(sheet,`A20:B${last}`);header(sheet,'A20:B20');sheet.getRange(`A21:A${last}`).format.font.bold=true;
 const notes=[['Units and dates','Amounts are stored as whole USD and displayed in millions unless marked x or %. Balance sheets are instants; FY and later TTM are overlapping twelve-month windows.'],['Colors','Blue numeric cells are reported inputs; green formulas reference other sheets; black formulas calculate within a sheet. Green does not mean favorable or recurring cash.'],['Evidence and uncertainty','Data contains source URLs and filing metadata. Copy a full URL into a browser to open the source. Unavailable is never zero; capacity and later events do not update balance-sheet cash or borrowing.'],['Reading the charts','FCF is OCF less capital spending, not another cash flow to add. Vistra has no supported older borrowing series. Other existing company-specific charts retain their own dated scope.']];
 sheet.getRange(`A${last+2}:B${last+5}`).values=notes;const nf=sheet.getRange(`A${last+2}:B${last+5}`).format;nf.font.name='Arial';nf.font.size=10;nf.wrapText=true;nf.verticalAlignment='top';nf.rowHeight=55;frame(sheet,`A${last+2}:B${last+5}`);
 const about=wb.worksheets.getItem('About'),n=about.getUsedRange().values.length+1;about.getRange(`A${n}:C${n}`).values=[['Workbook guide','The first sheet lists all workbook tabs and their questions. Core metrics, dated history and common charts agree with the app. URLs remain full, copyable source text. Native hyperlink actions are not authored by this spreadsheet runtime.','https://github.com/jackconnolly1000-ux/sec-filing-research-terminal/blob/main/docs/excel_parity.md']];const af=about.getRange(`A${n}:C${n}`).format;af.font.name='Arial';af.font.size=10;af.wrapText=true;af.rowHeight=76;frame(about,`A${n}:C${n}`);
 const charts=wb.worksheets.getItem('Core charts'),history=wb.worksheets.getItem('History');
 charts.getRange('A41:D41').values=[['Evidence trail',null,null,'Chart values link to Debt and liquidity and History. Data retains the exact input periods, tags, accessions and source URLs.']];charts.getRange('A41:D41').format.rowHeight=65;
 for(const [sheetName,range,name] of [['Funding conclusion',`A20:B${last}`,'contents'],['Funding conclusion',`A${last+2}:B${last+5}`,'reading'],['About',`A${n}:C${n}`,'about'],['Core charts','A41:D41','chart-evidence'],['History','A5:D19','history']]){const png=await wb.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(path.join(process.cwd(),`${ticker}-parity-${name}.png`),new Uint8Array(await png.arrayBuffer()));}
 return {guide_sha256:model.fingerprint};
}
