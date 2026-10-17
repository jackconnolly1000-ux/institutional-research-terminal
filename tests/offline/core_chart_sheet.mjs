import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {frame,header} from './workbook_style.mjs';
export function addCoreChartSheet(wb,root,ticker){
 const model=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c','import json,sys,core_charts as c;from pathlib import Path;s=next(s for s in json.loads(Path("samples/liquidity_pilots.json").read_text())["snapshots"] if s["ticker"]==sys.argv[1]);print(json.dumps(c.build(s)))',ticker],{cwd:root,encoding:'utf8'}));
 return {model,sheet:wb.worksheets.add('Core charts')};
}
export async function finishCoreChartSheet(wb,root,ticker,{model,sheet}){
 const USD='#,##0,,;(#,##0,,);"-"';sheet.showGridLines=false;
 sheet.getRange('A1:O43').format.font.name='Arial';sheet.getRange('A1:O43').format.font.size=10;
 sheet.getRange('A1:D43').format.wrapText=true;sheet.getRange('A1:D43').format.verticalAlignment='top';sheet.getRange('A1:D43').format.rowHeight=35;
 [34,23,23,24].forEach((w,i)=>sheet.getRangeByIndexes(0,i,43,1).format.columnWidth=w);sheet.getRange('E1:E43').format.columnWidth=3;sheet.getRange('F1:O43').format.columnWidth=10;
 sheet.getRange('A2').values=[[ticker+' — two chart questions']];sheet.getRange('A2').format.font.bold=true;sheet.getRange('A2').format.font.size=14;sheet.getRange('A2').format.wrapText=false;
 sheet.getRange('A3').values=[['TTM '+model.period_start+' to '+model.period_end+'. Values stored in USD, displayed in millions.']];sheet.getRange('A3').format.wrapText=false;
 sheet.getRange('A5:B8').values=[['TTM measure','USD millions'],...model.flow.map(([label])=>[label,null])];
 for(const [cell,formula] of [['B6',"='Debt and liquidity'!B10"],['B7',"=-'Debt and liquidity'!B11"],['B8',"='Debt and liquidity'!B12"]])sheet.getRange(cell).formulas=[[formula]];
 sheet.getRange('B6:B8').format.font.color='#008000';sheet.getRange('B6:B8').setNumberFormat(USD);frame(sheet,'A5:B8');header(sheet,'A5:B5');
 sheet.getRange('A10:D10').values=[['Calculation basis',null,null,'FCF = OCF − capital spending. FCF is a result, not an additional cash flow. Capital spending is shown negative.']];sheet.getRange('A10:D10').format.rowHeight=80;
 sheet.getRange('A24:C26').values=[['Balance-sheet date',...model.series,...(model.series.length===1?[null]:[])],...model.points.map(([date])=>[date,null,null])];
 sheet.getRange('B25').formulas=[["='History'!B6"]];sheet.getRange('B26').formulas=[["='History'!C6"]];
 if(model.series.length===2){sheet.getRange('C25').formulas=[["='History'!B7"]];sheet.getRange('C26').formulas=[["='History'!C7"]];}
 sheet.getRange('B25:C26').setNumberFormat(USD);sheet.getRange('B25:C26').format.font.color='#008000';frame(sheet,model.series.length===2?'A24:C26':'A24:B26');header(sheet,model.series.length===2?'A24:C24':'A24:B24');
 sheet.getRange('A29').values=[['Scope / missing history']];sheet.getRange('D29').values=[[model.note]];sheet.getRange('A29:D29').format.rowHeight=95;
 const configure=(chart,title)=>{chart.title=title;chart.titleTextStyle.fontSize=12;chart.titleTextStyle.typeface='Arial';chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};chart.yAxis={numberFormatCode:'#,##0,,;(#,##0,,)',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};chart.yAxis.title.text='USD millions';chart.legend={position:'bottom',textStyle:{typeface:'Arial'}};chart.series.items.forEach((s,i)=>s.fill=i?'#47627F':'#8D99A8');};
 const flow=sheet.charts.add('bar',sheet.getRange('A5:B8'));configure(flow,'What remained after capital spending?');flow.setPosition('F4','O20');
 const balances=sheet.charts.add('bar',sheet.getRange(model.series.length===2?'A24:C26':'A24:B26'));configure(balances,model.title);balances.setPosition('F23','O39');
 const about=wb.worksheets.getItem('About'),n=about.getUsedRange().values.length+1;about.getRange(`A${n}:C${n}`).values=[['Core charts','Two native charts link to Debt and liquidity and History. Signed capital spending is a use; FCF is the result. Unsupported older Vistra borrowing is omitted, never plotted as zero.','https://github.com/jackconnolly1000-ux/sec-filing-research-terminal/blob/main/docs/core_charts.md']];
 const af=about.getRange(`A${n}:C${n}`).format;af.font.name='Arial';af.font.size=10;af.wrapText=true;af.rowHeight=70;frame(about,`A${n}:C${n}`);
 wb.recalculate();
 for(const [i,[,value]] of model.flow.entries())if(sheet.getRange('B'+(i+6)).values[0][0]!==value)throw Error('Chart flow mismatch');
 for(const [i,[,values]] of model.points.entries())for(const [j,value] of values.entries())if(sheet.getRange('BC'[j]+(i+25)).values[0][0]!==value)throw Error('Chart balance mismatch');
 const source=wb.worksheets.getItem('Debt and liquidity'),original=source.getRange('B10').values[0][0],originalFormula=source.getRange('B10').formulas;
 source.getRange('B10').values=[[original+1000000]];wb.recalculate();
 if(sheet.getRange('B6').values[0][0]!==model.flow[0][1]+1000000||sheet.getRange('B8').values[0][0]!==model.flow[2][1]+1000000)throw Error('Chart source change did not recalculate');
 source.getRange('B10').formulas=originalFormula;wb.recalculate();
 const aboutPng=await wb.render({sheetName:'About',range:`A${n}:C${n}`,scale:1,format:'png'});await fs.writeFile(path.join(process.cwd(),`${ticker}-core-about.png`),new Uint8Array(await aboutPng.arrayBuffer()));
 for(const [range,name] of [['A2:O20','flows'],['A23:O39','balances']]){const png=await wb.render({sheetName:'Core charts',range,scale:1,format:'png'});await fs.writeFile(path.join(process.cwd(),`${ticker}-core-${name}.png`),new Uint8Array(await png.arrayBuffer()));}
 return {charts_sha256:JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c','import json,core_charts as c;print(json.dumps(c.fingerprint()))'],{cwd:root,encoding:'utf8'}))};
}
