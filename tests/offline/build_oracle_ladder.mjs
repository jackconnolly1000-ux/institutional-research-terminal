// Author only the new chart. Its table references bind to the original Payment dates sheet.
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2],out=process.argv[3];
const rows=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
 'import json,oracle_principal as o;r=o.load();assert r;print(json.dumps(r["calendar"]))'],{cwd:root,encoding:'utf8'}));
const w=Workbook.create(),s=w.worksheets.add('Payment dates');
s.getRange('A48:C54').values=[['Fiscal year',null,'Principal'],...rows.map(r=>[r.label,null,r.principal])];
s.getRange('A48:C54').format.font.name='Arial';s.getRange('A48:C54').format.font.size=10;
s.getRange('C49:C54').setNumberFormat('#,##0.0,,,');s.getRange('A48:A54').format.columnWidth=28;
const c=s.charts.add('bar',[s.getRange('A48:A54'),s.getRange('C48:C54')]);
c.title='Principal at Aug 31, 2026 (USD billions)\nFY2027 remainder; thereafter = FY2032 onward';
c.titleTextStyle.fontSize=12;c.titleTextStyle.typeface='Arial';
c.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};
c.yAxis={numberFormatCode:'0.0,,,',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};
c.yAxis.title.text='USD billions';c.hasLegend=false;c.series.items[0].fill='#D95926';c.setPosition('H36','S57');
w.recalculate();await(await SpreadsheetFile.exportXlsx(w)).save(out+'/oracle-ladder.xlsx');
const png=await w.render({sheetName:s.name,range:'H35:S58',scale:1});await fs.writeFile(out+'/oracle-ladder.png',new Uint8Array(await png.arrayBuffer()));
