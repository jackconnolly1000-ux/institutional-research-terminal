import {addBorrowingLeaseSheet,finishBorrowingLeaseSheet} from './borrowing_lease_sheet.mjs';
import {documentationLinks} from './workbook_style.mjs';
import {addFundingSheet,finishFundingSheet} from './funding_sheet.mjs';
// Build with the Codex spreadsheet runtime in a temporary directory; the app serves saved bytes.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
import {frame, header, subtotal} from './workbook_style.mjs';

const root=process.argv[2];
if(!root) throw new Error('Pass repository directory');
const input=path.join(root,'samples/vistra_liquidity.json');
const bytes=await fs.readFile(input), r=JSON.parse(bytes);
const interestBytes=await fs.readFile(path.join(root,'samples/vistra_interest.json'));
const interest=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
 'import json,vistra_interest as i;r=i.load();assert r is not None;print(json.dumps(r))'],{cwd:root,encoding:'utf8'}));
if(interest.calculation.value===null)throw new Error('Interest review is incomplete');
if(r.status!=='Checked'||!r.capacity||!r.debt||!r.annual) throw new Error('Source reconciliations incomplete');
const wb=Workbook.create();
const funding=addFundingSheet(wb,root,'VST');
const borrowingLeases=addBorrowingLeaseSheet(wb,root,'VST');
const main=wb.worksheets.add('Cash review'), due=wb.worksheets.add('Payment dates');
const capacity=wb.worksheets.add('Financing capacity'), data=wb.worksheets.add('Data'), about=wb.worksheets.add('About');
const USD='#,##0,,;(#,##0,,);"-"', diff='#,##0.00,,;(#,##0.00,,);0.00';
const date=s=>s?new Date(s+'T00:00:00Z'):null;
const rows=new Map();
const inputs=Object.entries(r.inputs).map(([key,f],i)=>{
  rows.set(key,i+2);
  return [key,f.value,f.label,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,
    f.tag,f.context_id,JSON.stringify(f.dimensions),f.scale,f.decimals,f.source_url,f.location,f.detail||null];
});
for(const [key,f] of Object.entries(interest.inputs)){
 rows.set('coverage_'+key,inputs.length+2);
 inputs.push(['coverage_'+key,f.value,f.label,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,
  f.tag,f.context_id,JSON.stringify(f.dimensions),f.scale,f.decimals,f.source_url,f.location,f.detail||'',
  f.source_sha256,f.unit+'; '+f.selection_rule]);
}
data.getRange(`A1:R${inputs.length+1}`).values=[['Input','USD, displayed millions','Description','Period from','Period through','Form','Filed','Accession','Tag','Context','Dimensions','Scale','Decimals','Source','Location','Reason if unavailable','Reviewed source SHA256','Unit and selection rule'],...inputs.map(r=>r.concat(Array(18-r.length).fill(null)))];
data.getRange(`B2:B${inputs.length+1}`).format.font.color='#0000FF';
data.getRange(`B2:B${inputs.length+1}`).setNumberFormat(USD);
data.getRange(`D2:E${inputs.length+1}`).setNumberFormat('mmm d, yyyy');
data.getRange(`G2:G${inputs.length+1}`).setNumberFormat('mmm d, yyyy');
function set(s,c,value,formula=false){s.getRange(c)[formula?'formulas':'values']=[[value]];if(formula)s.getRange(c).format.font.color=value.includes('Data!')?'#008000':'#000000';}
const link=k=>`=IF(ISNUMBER(Data!B${rows.get(k)}),Data!B${rows.get(k)},NA())`;
function entry(s,n,label,value,note=''){
  set(s,`A${n}`,label);set(s,`B${n}`,value,true);if(note)set(s,`D${n}`,note);
}
set(main,'A2','Vistra cash generation and repayment');
set(main,'A3','Jan 1–Jun 30, 2026. USD millions. Historical cash flows, not a forecast.');
main.getRange('A5:B5').values=[['Cash measure','USD millions']];
entry(main,6,'Operating cash flow',link('ocf'));
entry(main,7,'Capital spending',link('capex'));
entry(main,8,'Cash flow after capital spending','=B6-B7');
entry(main,10,'Stock repurchases',link('buybacks'));
entry(main,11,'Common dividends',link('common_dividends'));
entry(main,12,'Preferred dividends',link('preferred_dividends'));
entry(main,13,'Buybacks and dividends','=SUM(B10:B12)');
entry(main,14,'After capex, buybacks and dividends','=B8-B13');
entry(main,16,'Debt issuance cash proceeds',link('debt_issued'));
entry(main,17,'Corporate revolver borrowings',link('revolver_draws'));
entry(main,18,'Commodity-linked borrowings',link('commodity_draws'));
entry(main,19,'Debt repayments and repurchases',link('debt_repaid'));
entry(main,20,'Revolver repayments',link('revolver_repaid'));
entry(main,21,'Commodity-linked repayments',link('commodity_repaid'));
entry(main,22,'Net receivables financing cash flow',link('receivables_net'));
entry(main,23,'Net debt cash flow','=SUM(B16:B18)-SUM(B19:B21)+B22');
entry(main,25,'Other investing cash flow',
  `=-${link('acquisition_adjustment').slice(1)}+${link('trust_sales').slice(1)}-${link('trust_purchases').slice(1)}+${link('allowance_sales').slice(1)}-${link('allowance_purchases').slice(1)}+${link('insurance').slice(1)}+${link('asset_sales').slice(1)}-${link('other_investing').slice(1)}`);
entry(main,26,'Debt issuance costs',link('fees'));
entry(main,27,'Share compensation tax withholding',link('withholding'));
entry(main,28,'Nuveen principal paid',link('nuveen_principal_paid'));
entry(main,29,'Other financing cash flow',link('other_financing'));
entry(main,30,'Calculated net investing cash flow','=B25-B7');
entry(main,31,'Reported net investing cash flow',link('investing'));
entry(main,32,'Investing reconciliation difference','=B30-B31');
entry(main,33,'Calculated net financing cash flow','=B23-B13-B26-B27-B28+B29');
entry(main,34,'Reported net financing cash flow',link('financing'));
entry(main,35,'Financing reconciliation difference','=B33-B34');
entry(main,37,'Calculated cash change','=B6+B30+B33');
entry(main,38,'Reported cash change',link('change'));
entry(main,39,'Cash-change reconciliation difference','=B37-B38');
entry(main,41,'Opening cash including restricted cash',link('opening_total'));
entry(main,42,'Calculated ending cash including restricted cash','=B41+B37');
entry(main,43,'Reported ending cash including restricted cash',link('closing_total'));
entry(main,44,'Ending-cash reconciliation difference','=B42-B43');
entry(main,45,'Current restricted cash',link('restricted_current'));
entry(main,46,'Noncurrent restricted cash',link('restricted_noncurrent'));
entry(main,47,'Cash excluding restricted cash','=B42-SUM(B45:B46)');
entry(main,48,'Reported cash and equivalents',link('cash'));
entry(main,49,'Balance-sheet cash reconciliation difference','=B47-B48');
const cashNotes=[
  'Capital spending includes nuclear fuel and LTSA prepayments.',
  'Reported operating cash flow contains working-capital and margin movements; recurrence is not established.',
  'Operating cash flow is seasonal and weighted toward the second half; H1 is not annualized.',
  'Nuveen interest already included in operating cash flow is not subtracted again.',
  'Trust-security turnover is not gross cash available to fund corporate debt.',
  'Cash after capex fell short of buybacks and dividends by 309M in this historical period.',
];
cashNotes.forEach((n,i)=>set(main,`D${6+i*3}`,n));
set(main,'A52','Historical operating-income interest coverage');
set(main,'A53','TTM July 1, 2025–June 30, 2026. Selected interest component before capitalized interest.');
main.getRange('A55:D55').values=[['Build, USD millions','FY2025','+ H1 2026','− H1 2025']];
const signs={operating_income:1,interest:1,swaps:-1,amortization:1,extinguishment:-1,capitalized:-1,other:1,total:1};
for(const [n,key,label] of [[56,'operating_income','Reported operating income'],[57,'interest','Selected interest component'],
 [58,'swaps','Unrealized swap (gain) loss'],[59,'amortization','Debt-cost amortization'],
 [60,'extinguishment','Extinguishment (gain) loss'],[61,'capitalized','Less capitalized interest'],[62,'other','Other'],
 [64,'total','Reported mixed interest total']]){
 set(main,`A${n}`,label);
 ['fy','current','prior'].forEach((role,i)=>{
  const f=link('coverage_'+role+'_'+key);set(main,`${'BCD'[i]}${n}`,signs[key]===1?f:'=-'+f.slice(1),true);
 });
}
set(main,'A63','Reconstructed mixed interest total');set(main,'A65','Reconciliation difference, zero = matched');
for(const col of 'BCD'){set(main,`${col}63`,`=SUM(${col}57:${col}62)`,true);set(main,`${col}65`,`=${col}63-${col}64`,true);}
const ttmRows=[[68,56,'TTM reported operating income'],[69,57,'TTM selected interest component'],
 [70,58,'TTM unrealized swap (gain) loss'],[71,59,'TTM debt-cost amortization'],
 [72,60,'TTM extinguishment (gain) loss'],[73,61,'TTM capitalized-interest deduction'],[74,62,'TTM Other'],
 [76,64,'TTM reported mixed interest total']];
for(const [n,source,label] of ttmRows){set(main,`A${n}`,label);set(main,`B${n}`,`=B${source}+C${source}-D${source}`,true);}
set(main,'A75','TTM reconstructed mixed interest total');set(main,'B75','=SUM(B69:B74)',true);
set(main,'A77','TTM reconciliation difference');set(main,'B77','=B75-B76',true);
set(main,'A79','Historical interest-component coverage');
set(main,'B79','=IF(AND(B65=0,C65=0,D65=0,B77=0,D91=0,B69>0),B68/B69,NA())',true);
main.getRange('A82:D82').values=[['Prior H1 raw fact','2026 comparative','Original 2025 filing','Difference']];
for(const [i,key] of Object.keys(signs).entries()){
 const labels={operating_income:'Operating income',interest:'Interest component',swaps:'Swap gain (loss)',
  amortization:'Debt-cost amortization',extinguishment:'Extinguishment gain (loss)',capitalized:'Capitalized interest',other:'Other',total:'Mixed interest total'};
 const n=83+i;set(main,`A${n}`,labels[key]+' (raw)');
 set(main,`B${n}`,link('coverage_prior_'+key),true);set(main,`C${n}`,link('coverage_prior_original_'+key),true);
 set(main,`D${n}`,`=B${n}-C${n}`,true);
}
set(main,'A91','Total absolute prior-period difference');set(main,'D91','=SUM(ABS(D83),ABS(D84),ABS(D85),ABS(D86),ABS(D87),ABS(D88),ABS(D89),ABS(D90))',true);
set(main,'A93','Raw gains are positive; swap/extinguishment signs are reversed only in the expense build.');
set(main,'A94','Capitalization is deducted in the mixed total, not adjusted again in the selected denominator.');
set(main,'A95','Receivables/Nuveen allocation and Other composition: Unavailable. See About.');

set(due,'A2','Vistra dated repayment review');
set(due,'A3','Selected June 30 balances. USD millions. Principal except Nuveen includes interest.');
due.getRange('A5:E5').values=[['Obligation','Due from','Due through','USD millions','Basis and condition']];
r.payments.forEach((p,i)=>{const n=i+6;
  due.getRange(`A${n}:C${n}`).values=[[p.label,date(p.due_start),date(p.due_end)]];
  set(due,`D${n}`,link(p.key),true);set(due,`E${n}`,p.detail);
});
due.getRange('B6:C11').setNumberFormat('mmm d, yyyy');due.getRange('D6:D11').setNumberFormat(USD);
// The chart compares separate dated balances; no combined funding-need total is implied.
due.getRange('H24:I30').values=[['Selected payment','USD'],...r.payments.map((p,i)=>[
  ['Dec 3, 2026\nPulaski bridge','Dec 2026\nConstruction','Dec 30, 2026\nSenior notes','Dec 31, 2026\nNuveen','Jan 30, 2027\nSenior notes','Jul 31, 2027\nSenior notes'][i],null])];
for(let i=0;i<6;i++)set(due,`I${25+i}`,`=D${6+i}`,true);
due.getRange('I25:I30').setNumberFormat(USD);
const chart=due.charts.add('bar',due.getRange('H24:I30'));
chart.title='Selected payments (USD millions)';chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=13;
chart.hasLegend=false;chart.xAxis={axisType:'textAxis',tickLabelPosition:'low',textStyle:{typeface:'Arial',fontSize:11},majorGridlines:null};
chart.yAxis={numberFormatCode:'#,##0,,',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};
chart.series.items[0].fill='#737985';chart.setPosition('A14','F31');
entry(due,33,'Nuveen carrying liability',link('nuveen_carrying'),'Same obligation as the 631M final payment above; not added.');
entry(due,35,'Expected Cogentrix cash consideration',link('cogentrix'),'Late-2026 expected closing; conditions and adjustments apply. Exact payment date and completed closing Unavailable.');
entry(due,37,'Helix initial callable commitment',link('helix_initial'),'Call date and amount funded to date Unavailable. Not assigned to December.');
entry(due,39,'Helix additional conditional commitment',link('helix_additional'),'Milestones had not occurred at June 30; Vistra may elect to invest regardless.');
set(due,'A42','Historical annual schedule at Dec 31, 2025');
due.getRange('A43:C43').values=[['Due year','USD millions','Basis']];
for(let i=0;i<6;i++){
  set(due,`A${44+i}`,i<5?2026+i:'Thereafter');set(due,`B${44+i}`,link('annual_'+i),true);
  set(due,`C${44+i}`,'Historical principal schedule, not rolled forward to June.');
}
entry(due,50,'Calculated annual principal','=SUM(B44:B49)');
entry(due,51,'Less annual premiums, discounts and costs',link('annual_costs'));
entry(due,52,'Calculated annual carrying debt','=B50-B51');
entry(due,53,'Reported annual carrying debt',link('annual_carrying'));
entry(due,54,'Annual carrying reconciliation difference','=B52-B53');
set(due,'A56','No full remaining June debt-service schedule or overall future repayment surplus is inferred.');

set(capacity,'A2','Vistra funding resources and conditions');
set(capacity,'A3','Reported available capacity at June 30, 2026. USD millions. Current drawable capacity is Unavailable.');
capacity.getRange('A5:E5').values=[['Resource','June available','Current drawable','Borrower / scope','Conditions']];
r.resources.forEach((resource,i)=>{
  const n=i+6;set(capacity,`A${n}`,resource.label);
  if(rows.has(resource.input_key))set(capacity,`B${n}`,link(resource.input_key),true);
  set(capacity,`C${n}`,'Unavailable');set(capacity,`D${n}`,resource.borrower);set(capacity,`E${n}`,resource.detail);
});
entry(capacity,16,'Calculated June reported liquidity','=SUM(B6:B8)');
entry(capacity,18,'Revolver commitment',link('revolver_limit'));
entry(capacity,19,'Less revolving borrowings',link('revolver_drawn'));
entry(capacity,20,'Less revolver letters of credit',link('revolver_lc'));
entry(capacity,21,'Calculated revolver availability','=B18-B19-B20');
entry(capacity,22,'Reported revolver availability',link('revolver_available'));
entry(capacity,23,'Revolver reconciliation difference','=B21-B22');
entry(capacity,25,'Commodity-linked commitment',link('commodity_limit'));
entry(capacity,26,'Commodity-linked reported availability',link('commodity_available'),'Weekly borrowing base is lower than commitment. Do not use 1.75B as available cash.');
entry(capacity,28,'Other LOC facilities',link('loc_other'));
entry(capacity,29,'Alternative LOC facilities',link('loc_alternative'));
entry(capacity,30,'Calculated LOC total','=B20+B28+B29');
entry(capacity,31,'Reported LOC total',link('loc_total'));
entry(capacity,32,'LOC reconciliation difference','=B30-B31');
entry(capacity,34,'Project debt already in baseline borrowing',link('project_debt'));
entry(capacity,35,'Vistra Operations principal',link('operations_debt'));
entry(capacity,36,'Calculated long-term principal','=B34+B35');
entry(capacity,37,'Less unamortized premiums/discounts/costs',link('debt_costs'));
entry(capacity,38,'Calculated long-term carrying debt','=B36-B37');
entry(capacity,39,'Reported long-term carrying debt',link('lt_carrying'));
entry(capacity,40,'Long-term debt reconciliation difference','=B38-B39');
entry(capacity,41,'Receivables financing outstanding',link('receivables'));
entry(capacity,42,'Baseline gross borrowing','=B38+B41');
entry(capacity,44,'Margin cash already posted',link('margin_cash'));
entry(capacity,45,'Affiliate-financed assets already posted',link('affiliate_margin'));
set(capacity,'D44','Posted assets are not extra cash available for repayments.');

about.getRange('A1:D1').values=[['Topic','Finding / limitation','Source','Location / filing date']];
const notes=[
  ['Scope','Liquidity review checked October 15, 2026; interest and funding interpretation checked October 16. Cash and facility balances remain June 30. Not live data or investment advice.',null,null],
  ['Workbook','Cash review shows historical sources and uses. Payment dates separates June amounts from the old annual schedule. Financing capacity distinguishes resources and borrowers. Data retains facts and provenance.',null,null],
  ['Format','Full USD stored, displayed in millions. Arial 10. Blue inputs, green links, black calculations. A dash is numeric zero; a blank available-capacity cell means Unavailable.',null,null],
  ['Numeric inputs','Missing inputs produce a visible #N/A in dependent arithmetic, never zero. Original facts are a frozen evidence record, not forecast assumptions.',null,null],
  ...r.terms.map(t=>[t.name,t.detail,t.source_url,`${t.location}; event ${t.event_date}; filed ${t.filed}; ${t.accession}`]),
  ...r.events.map(e=>[e.kind,e.finding,e.source_url,`Event ${e.event_date||'not stated'}; filed ${e.filed}; ${e.form}; ${e.accession}`]),
  ...r.limits.map((n,i)=>['Limit '+(i+1),n,null,null]),
  ['Index review',r.inventory.detail,'https://data.sec.gov/submissions/CIK0001692819.json','Retrieved October 15, 2026'],
  ['October filing date','The Sep 30 amendment was accepted Oct 2 at 20:12:47 but its EDGAR filing date is Oct 5. Filing date corrected from the older review.','https://www.sec.gov/Archives/edgar/data/1692819/000114036126038468/0001140361-26-038468-index.html','Event Sep 30, filed Oct 5, 2026'],
  ['Historical interest coverage',interest.formula+'. '+interest.ttm_formula+'. Every period reconciles to the mixed total; the original H1 2025 filing independently agrees.','docs/vistra_interest_coverage.md','Checked October 16, 2026'],
  ['Capitalized-interest basis',interest.basis,interest.inputs.current_interest.source_url,'10-K p. 121; 10-Q Note 12 p. 28'],
  ['Interest composition',interest.composition,interest.inputs.current_interest.source_url,'Separate interest component, not the mixed statement total'],
  ['Signs and definitions','Raw swap gains and extinguishment gains are positive. Their signs are reversed only to match the printed expense table. Capitalization is a deduction. The interest extension is monetary, duration, debit; its terse label is Interest expense and documentation adds no allocation detail.','https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630.xsd','Schema and labels reviewed; raw facts and hashes are retained'],
  ['Coverage limits',interest.limitations,null,'Receivables/Nuveen allocation and Other composition remain Unavailable'],
];
about.getRange(`A2:D${notes.length+1}`).values=notes;
for(const s of [main,due,capacity,data,about]){
  s.showGridLines=false;const u=s.getUsedRange();u.format.font.name='Arial';u.format.font.size=10;
  u.format.rowHeight=25;u.format.verticalAlignment='center';u.format.wrapText=false;
}
for(const s of [main,due,capacity]){
  s.getRange('A2').format.font.bold=true;s.getRange('A2').format.font.size=14;
  s.getRange('A3').format.font.italic=true;s.getRange('A1:A57').format.columnWidth=50;
  s.getRange('B1:B57').format.columnWidth=21;s.getRange('C1:C57').format.columnWidth=21;
  s.getRange('D1:D57').format.columnWidth=50;s.getRange('E1:E57').format.columnWidth=75;
  s.getRange('B6:B54').setNumberFormat(USD);s.getRange('A5:E5').format.font.bold=true;
  s.getRange('A5:E5').format.borders={bottom:{style:'thin',color:'#AEB4BD'}};
}
main.getRange('A6:B49').format.rowHeight=28;
main.getRange('D6:D24').format.wrapText=true;main.getRange('D6:D24').format.columnWidth=66;
for(const n of [8,13,14,23,37,42,47])main.getRange(`A${n}:B${n}`).format.font.bold=true;
for(const n of [32,35,39,44,49])main.getRange(`B${n}`).setNumberFormat(diff);
due.getRange('B6:C11').setNumberFormat('mmm d, yyyy');
due.getRange('D6:D11').setNumberFormat(USD);due.getRange('A6:E11').format.rowHeight=70;
due.getRange('A6:A11').format.wrapText=true;due.getRange('E6:E11').format.wrapText=true;
for(const n of [33,35,37,39]){due.getRange(`D${n}`).format.wrapText=true;due.getRange(`A${n}:E${n}`).format.rowHeight=52;}
due.getRange('C44:C49').format.wrapText=true;due.getRange('C44:C49').format.rowHeight=40;
due.getRange('B54').setNumberFormat(diff);
capacity.getRange('A6:E13').format.wrapText=true;capacity.getRange('A6:E13').format.rowHeight=90;
capacity.getRange('D26:D26').format.wrapText=true;capacity.getRange('D26').format.rowHeight=45;
for(const n of [23,32,40])capacity.getRange(`B${n}`).setNumberFormat(diff);
data.getUsedRange().format.wrapText=true;data.getUsedRange().format.rowHeight=52;
for(const [range,width] of [['A1:A90',26],['B1:B90',21],['C1:C90',55],['D1:G90',20],['H1:H90',32],['I1:K90',65],['L1:M90',12],['N1:P90',75]])data.getRange(range).format.columnWidth=width;
data.getRange('A1:P1').format.font.bold=true;data.freezePanes.freezeRows(1);
data.getRange(`Q1:Q${inputs.length+1}`).format.columnWidth=50;data.getRange(`R1:R${inputs.length+1}`).format.columnWidth=80;
about.getRange(`A1:A${notes.length+1}`).format.columnWidth=35;about.getRange(`B1:B${notes.length+1}`).format.columnWidth=105;
about.getRange(`C1:D${notes.length+1}`).format.columnWidth=65;about.getUsedRange().format.wrapText=true;
about.getUsedRange().format.rowHeight=90;about.getRange('A1:D1').format.rowHeight=25;about.getRange('A1:D1').format.font.bold=true;about.freezePanes.freezeRows(1);
for(const address of ['A5:B8','A10:B14','A16:B23','A25:B35','A37:B39','A41:B49'])frame(main,address);
for(const address of ['A5:E11','A33:B33','A35:B35','A37:B37','A39:B39','A43:C54','H24:I30'])frame(due,address);
for(const address of ['A5:E13','A16:B16','A18:B23','A25:B26','A28:B32','A34:B42','A44:B45'])frame(capacity,address);
frame(data,`A1:R${inputs.length+1}`);frame(about,`A1:D${notes.length+1}`);header(data,'A1:R1');
main.getRange('A52').format.font.bold=true;main.getRange('A52').format.font.size=14;
for(const a of ['A55:D65','A68:B79','A82:D91']){main.getRange(a).format.rowHeight=32;frame(main,a);}
main.getRange('A55:D65').format.wrapText=true;main.getRange('A82:D91').format.wrapText=true;
for(const a of ['B56:D64','B68:B77','B83:C90'])main.getRange(a).setNumberFormat(USD);
for(const a of ['B65:D65','B77','D83:D90'])main.getRange(a).setNumberFormat(diff);
main.getRange('D91').setNumberFormat(diff);
main.getRange('B79').setNumberFormat('0.00"x"');main.getRange('A79:B79').format.font.italic=true;
for(const a of ['A55:D55','A82:D82'])header(main,a);
for(const n of [57,63,64,65])subtotal(main,`A${n}:D${n}`);
for(const n of [68,69,75,76,77,79])subtotal(main,`A${n}:B${n}`);
for(let n=notes.length-3;n<=notes.length+1;n++)about.getRange(`A${n}:D${n}`).format.rowHeight=120;
for(const [sheet,address] of [[main,'A5:B5'],[due,'A5:E5'],[due,'A43:C43'],[due,'H24:I24'],[capacity,'A5:E5'],[data,'A1:P1'],[about,'A1:D1']])header(sheet,address);
for(const n of [8,13,14,23,30,33,37,42,47])subtotal(main,`A${n}:B${n}`);
for(const n of [16,21,30,36,38,42])subtotal(capacity,`A${n}:B${n}`);
subtotal(due,'A50:B50');subtotal(due,'A52:B52');
wb.recalculate();
for(const [cell,value] of Object.entries({B8:650e6,B13:959e6,B14:-309e6,B23:-162e6,B25:293e6,B32:0,B35:0,B37:-341e6,B39:0,B42:481e6,B44:0,B47:435e6,B49:0})){
  if(main.getRange(cell).values[0][0]!==value)throw new Error('Cash reconciliation '+cell);
}
for(const [cell,value] of Object.entries({B16:6295e6,B23:0,B32:0,B40:0,B42:19895e6})){
  if(capacity.getRange(cell).values[0][0]!==value)throw new Error('Capacity/debt reconciliation '+cell);
}
if(due.getRange('B54').values[0][0]!==0)throw new Error('Annual principal reconciliation');
const source=data.getRange(`B${rows.get('capex')}`), original=source.values;
source.values=[[null]];wb.recalculate();if(typeof main.getRange('B8').values[0][0]==='number')throw new Error('Missing capex became zero');
source.values=[[0]];wb.recalculate();if(main.getRange('B8').values[0][0]!==2222e6)throw new Error('Reported zero lost');
source.values=[[original[0][0]+1e6]];wb.recalculate();if(main.getRange('B14').values[0][0]!==-310e6)throw new Error('Cash formula did not recalculate');
source.values=original;wb.recalculate();
for(const [cell,v] of Object.entries({B68:3563e6,B69:1117e6,B70:-14e6,B71:45e6,B72:35e6,B73:-151e6,B74:100e6,B75:1132e6,B76:1132e6,B77:0,B79:3563/1117,D91:0})){
 if(Math.abs(main.getRange(cell).values[0][0]-v)>1e-10)throw new Error('Interest reconciliation '+cell);
}
const ci=data.getRange(`B${rows.get('coverage_current_interest')}`),cio=ci.values;
ci.values=[[null]];wb.recalculate();if(typeof main.getRange('B79').values[0][0]==='number')throw new Error('Missing interest became coverage');
ci.values=cio;
const zeroCase=['fy','current','prior','prior_original'].flatMap(role=>{
 const i=data.getRange(`B${rows.get('coverage_'+role+'_interest')}`),t=data.getRange(`B${rows.get('coverage_'+role+'_total')}`);
 return [{cell:i,original:i.values,value:0},{cell:t,original:t.values,value:t.values[0][0]-i.values[0][0]}];
});
zeroCase.forEach(x=>x.cell.values=[[x.value]]);wb.recalculate();
if(main.getRange('B69').values[0][0]!==0||main.getRange('B77').values[0][0]!==0||typeof main.getRange('B79').values[0][0]==='number')throw new Error('Zero denominator guard failed');
zeroCase.forEach(x=>x.cell.values=x.original);
const swap=data.getRange(`B${rows.get('coverage_current_swaps')}`),swo=swap.values;
swap.values=[[-swo[0][0]]];wb.recalculate();if(typeof main.getRange('B79').values[0][0]==='number')throw new Error('Wrong raw swap sign escaped reconciliation');
swap.values=swo;
const originalPrior=data.getRange(`B${rows.get('coverage_prior_original_other')}`),originalPriorValue=originalPrior.values;
originalPrior.values=[[originalPriorValue[0][0]+1e6]];wb.recalculate();if(typeof main.getRange('B79').values[0][0]==='number')throw new Error('Changed original comparative not caught');
originalPrior.values=originalPriorValue;
const op=data.getRange(`B${rows.get('coverage_current_operating_income')}`),opo=op.values;
op.values=[[opo[0][0]+1e6]];wb.recalculate();if(Math.abs(main.getRange('B79').values[0][0]-3564/1117)>1e-12)throw new Error('Coverage does not recalculate');
op.values=opo;wb.recalculate();
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!',options:{useRegex:true,maxResults:10},maxChars:1500})).ndjson);
documentationLinks(about);
const fundingManifest=await finishFundingSheet(wb,root,'VST',funding);
Object.assign(fundingManifest,await finishBorrowingLeaseSheet(wb,root,'VST',borrowingLeases));
const output=path.join(root,'samples/vistra_liquidity.xlsx');await(await SpreadsheetFile.exportXlsx(wb)).save(output);
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.writeFile(output.replace('.xlsx','.manifest.json'),JSON.stringify({...fundingManifest,review_sha256:digest(bytes),interest_sha256:digest(interestBytes),workbook_sha256:digest(await fs.readFile(output))},null,2)+'\n');
if(process.env.SKIP_UNCHANGED_RENDERS!=='1') for(const [sheet,range,name] of [['Cash review','A2:B23','cash'],['Payment dates','A5:E11','payments'],['Payment dates','A14:F31','chart'],['Financing capacity','A5:E13','capacity'],['Data','A1:H6','data'],['About','A1:B10','about'],
 ['Cash review','A52:D65','interest-periods'],['Cash review','A68:B79','interest-ttm'],['Cash review','A82:D95','interest-comparatives'],
 ['Data',`A${rows.get('coverage_fy_operating_income')}:H${rows.get('coverage_current_operating_income')-1}`,'interest-inputs'],
 ['Data',`I${rows.get('coverage_current_operating_income')}:R${rows.get('coverage_prior_operating_income')-1}`,'interest-contexts'],
 ['About',`A${notes.length-3}:D${notes.length+1}`,'interest-basis']]){
  const preview=await wb.render({sheetName:sheet,range,scale:1.2,format:'png'});
  await fs.writeFile(path.join(process.cwd(),`vistra-${name}.png`),new Uint8Array(await preview.arrayBuffer()));
}
await fs.rm(output+'.inspect.ndjson',{force:true});
console.log('Exported and reconciled',output);
