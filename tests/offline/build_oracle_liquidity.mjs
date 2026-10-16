import {addFundingSheet,finishFundingSheet} from './funding_sheet.mjs';
// Run from a temporary directory using the Codex artifact runtime; deployment only serves the saved file.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
import {frame, header, subtotal} from './workbook_style.mjs';

const root = process.argv[2];
if (!root) throw new Error('Pass the repository directory');
const samplePath = path.join(root, 'samples/oracle_liquidity.json');
const sourceBytes = await fs.readFile(samplePath);
const review = JSON.parse(sourceBytes);
const annualBytes=await fs.readFile(path.join(root,'samples/oracle_financing.json'));
const annual=JSON.parse(annualBytes);
const revolverBytes=await fs.readFile(path.join(root,'samples/oracle_revolver.json'));
const interestBytes=await fs.readFile(path.join(root,'samples/oracle_interest.json'));
const interestReview=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
 'import json,oracle_interest as i;r=i.load();assert r is not None;print(json.dumps(r))'],{cwd:root,encoding:'utf8'}));
if(interestReview.calculation.value===null)throw new Error('Checked interest coverage is incomplete');
// Reuse the app's evidence model rather than maintaining another repayment interpretation in JS.
const repayment=JSON.parse(execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON,['-c',
  'import json,oracle_repayment as r,oracle_liquidity as l,oracle_financing as f;print(json.dumps(r.build(json.loads(l.SAMPLE.read_text()),json.loads(f.SAMPLE.read_text()))))'],{cwd:root,encoding:'utf8'}));
if(repayment.status!=='Checked')throw new Error(repayment.detail);
const revolver=repayment.revolver;
if(revolver.status!=='Checked')throw new Error(revolver.detail);
if (review.status !== 'Checked' || Object.values(review.schedules).some(s => s.status !== 'Checked')) {
  throw new Error('Source review has incomplete reconciliations');
}
const wb = Workbook.create();
const funding=addFundingSheet(wb,root,'ORCL');
const repay = wb.worksheets.add('Repayment review');
const main = wb.worksheets.add('Cash analysis');
const due = wb.worksheets.add('Payment dates');
const data = wb.worksheets.add('Data');
const about = wb.worksheets.add('About');
const USD = '#,##0,,;(#,##0,,);"-"';
const toDate = s => s ? new Date(s + 'T00:00:00Z') : null;
const rows = new Map();
const sourceRows = Object.entries(review.inputs).map(([key, f], i) => {
  rows.set(key, i + 2);
  return [key, f.value, f.label, toDate(f.period_start), toDate(f.period_end), f.form,
    toDate(f.filed), f.accession, f.tag, f.context_id, f.scale, f.decimals,
    f.source_url, f.location, f.detail || null];
});
for(const [i,f] of annual.buckets.entries()){
 rows.set('annual_'+i,sourceRows.length+2);
 sourceRows.push(['annual_'+i,f.value,'Historical May principal: '+f.label,null,toDate(annual.as_of),annual.form,
  toDate(annual.filed),annual.accession,f.tag,f.context_id,f.scale,f.decimals,annual.source_url,annual.location,
  'Historical principal. Not rolled forward to August; excludes interest and leases.']);
}
for (const [key, value, label, asof] of [
  ['facility_commitment', review.facility.commitment, 'Original revolver commitment', review.facility.agreement_date],
  ['facility_drawn', review.facility.drawn, 'Revolver drawn, May 31 only', review.facility.drawn_as_of],
  ['covenant_minimum', review.facility.covenant_minimum, 'Contract-defined minimum interest coverage (x)', review.facility.agreement_date],
]) {
  rows.set(key, sourceRows.length + 2);
  sourceRows.push([key, value, label, null, toDate(asof), review.facility.form,
    toDate(review.facility.filed), review.facility.accession, null, null, null, null,
    key === 'facility_drawn' ? 'https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm' : review.facility.source_url,
    key === 'facility_drawn' ? '10-K Note 6, p. 85, filed June 22, 2026' : review.facility.location, null]);
  if (key === 'facility_drawn') {
    sourceRows.at(-1)[5] = '10-K';
    sourceRows.at(-1)[6] = toDate('2026-06-22');
    sourceRows.at(-1)[7] = '0001193125-26-277521';
  }
}
function auditSource(key,value,label,sourceKey,asof,location,detail){
 const s=revolver.sources[sourceKey];rows.set(key,sourceRows.length+2);
 sourceRows.push([key,value,label,null,toDate(asof),s.form,toDate(s.filed),s.accession,
  null,null,null,null,s.source_url,location,detail]);
}
auditSource('facility_may_commitment',revolver.dates[1].commitment,'Revolver commitment confirmed at May 31',
 'annual','2026-05-31','10-K Note 6, pp. 84–85','Reported commitment. Not a drawable amount.');
auditSource('facility_increase_ceiling',revolver.increase_ceiling,'Conditional aggregate commitment ceiling',
 'agreement','2026-03-06','§2.05(d)','Lender agreement and conditions required; no exercised increase established. Not committed capacity.');
for(const [i,t] of revolver.terms.entries())auditSource('revolver_term_'+i,null,t.label,t.source,
 revolver.sources[t.source].period,t.location,t.detail);
for(const [key,s] of Object.entries(revolver.sources))auditSource('revolver_source_'+key,null,
 'Saved document reviewed: '+s.document,key,s.period,'Revolver audit source set',
 'Exact reviewed saved bytes, SHA256 '+s.sha256+'. Latest saved filing September 14; no complete later inventory.');
for(const [key,f] of Object.entries(interestReview.inputs)){
 rows.set('coverage_'+key,sourceRows.length+2);
 sourceRows.push(['coverage_'+key,f.value,f.label,toDate(f.period_start),toDate(f.period_end),f.form,toDate(f.filed),
  f.accession,f.tag,f.context_id,f.scale,f.decimals,f.source_url,f.location,f.detail||'',
  JSON.stringify(f.dimensions),f.source_sha256,f.unit+'; '+f.selection_rule]);
}
data.getRange('A1:R1').values = [['Key','USD millions unless x','Reported input','Period start','Period end / as of',
  'Form','Filed','Accession','Tag','Context ID','Scale','Decimals','Source','Filing location','Finding / Unavailable reason',
  'Dimensions','Reviewed source SHA256','Unit and selection rule']];
data.getRange(`A2:R${sourceRows.length+1}`).values = sourceRows.map(r=>r.concat(Array(18-r.length).fill(null)));
data.getRange(`B2:B${sourceRows.length+1}`).setNumberFormat(USD);
data.getRange(`B${rows.get('covenant_minimum')}`).setNumberFormat('0.0"x"');
data.getRange(`B2:B${sourceRows.length+1}`).format.font.color = '#0000FF';
for (const col of ['D','E','G']) data.getRange(`${col}2:${col}${sourceRows.length+1}`).setNumberFormat('mmm d, yyyy');
const ref = key => `'Data'!B${rows.get(key)}`;
const link = key => `=IF(ISNUMBER(${ref(key)}),${ref(key)},NA())`;
const set = (s, cell, value, formula=false) => {
  s.getRange(cell)[formula ? 'formulas' : 'values'] = [[value]];
};
const entry = (sheet, row, label, formula, note='') => {
  set(sheet, `A${row}`, label);
  set(sheet, `B${row}`, formula, true);
  set(sheet, `D${row}`, note);
  if (formula.includes("'Data'!")) sheet.getRange(`B${row}`).format.font.color = '#008000';
};

set(main, 'A2', 'Oracle cash sources and uses');
set(main, 'A3', 'June 1–August 31, 2026. USD millions. Cash totals include restricted cash.');
main.getRange('A4:B4').values = [['Quarter cash analysis','USD millions']];
for (const [r, label, key] of [
  [5,'Opening cash, including restricted','opening_total'],
  [6,'Reported operating cash flow','ocf'],[7,'Specified customer-prepayment contribution','prepay'],
  [9,'ATM equity proceeds, net','equity'],[10,'Cash capital spending','capex'],
  [13,'Cash dividends','dividends'],[14,'Grouped debt repayments','debt_repayments'],
  [18,'Reported ending cash, including restricted','closing_total'],[20,'Balance-sheet cash excluding restricted','closing_cash'],
]) entry(main,r,label,link(key));
entry(main,8,'OCF less specified prepayments','=B6-B7','Recurrence of this remainder is not established.');
entry(main,11,'Reported OCF less cash capex','=B6-B10');
entry(main,12,'OCF less specified prepayments and capex','=B8-B10');
const otherKeys = ['investment_purchases','investment_proceeds','employee','cp','capex_financing','other_financing','fx'];
const otherExpression = `-${ref('investment_purchases')}+${ref('investment_proceeds')}+${ref('employee')}-${ref('cp')}+${ref('capex_financing')}+${ref('other_financing')}+${ref('fx')}`;
entry(main,15,'Other cash flows, net',`=IF(COUNT(${otherKeys.map(ref).join(',')})=7,${otherExpression},NA())`,
  'Investments, employee shares, CP, capex financing, other financing and FX. Dividends are separate in row 13.');
entry(main,16,'Calculated cash increase','=B6+B9-B10-B13-B14+B15');
entry(main,17,'Calculated ending cash, including restricted','=B5+B16');
entry(main,19,'Ending-cash reconciliation difference','=B17-B18','Zero means detailed flows reconcile to reported ending cash.');
entry(main,21,'Restricted cash at August 31','=B18-B20','Balance exclusion, not a further cash outflow.');
entry(main,22,'Reported cash increase',link('change'));
entry(main,23,'Cash-increase reconciliation difference','=B16-B22');
entry(main,25,'Cash increase less ATM equity proceeds','=B16-B9');
entry(main,26,'Cash increase less ATM and specified prepayments','=B25-B7');
entry(main,27,'Specified prepayments / reported OCF','=IF(B6>0,B7/B6,NA())');
main.getRange('B27').setNumberFormat('0.0%');
for (const r of [19,23]) main.getRange(`B${r}`).setNumberFormat('#,##0.00,,;(#,##0.00,,);"-"');
set(main,'A29','Rows 25–26 hold every other reported flow fixed. They are historical arithmetic, not forecasts.');
set(main,'A30','No cash runway or future repayment surplus is calculated. August debt maturity amounts and drawable credit are Unavailable.');
set(main,'A31','Interest and operating lease cash payments within OCF are not subtracted again.');
set(main,'A32','The 11.363B prepayment contribution is already in OCF; the 19.909B ATM proceeds are already in August cash.');
main.getRange('H35:I38').values = [['Quarter measure','USD'],['Reported\nOCF',null],['OCF excluding specified\nprepayments',null],['Cash\ncapex',null]];
for (const [r, source] of [[36,6],[37,8],[38,10]]) set(main,`I${r}`,`=B${source}`,true);
main.getRange('I36:I38').setNumberFormat(USD);
set(main,'A41','Historical operating-income interest coverage');
set(main,'A42','TTM September 1, 2025–August 31, 2026. Reported interest line; capitalization basis Unavailable.');
main.getRange('A44:E44').values=[['Build, USD millions','FY2026','+ Q1 FY2027','− Q1 FY2026','TTM']];
for(const [n,key,label] of [[45,'operating_income','Reported operating income'],[46,'interest','Reported Interest expense'],
 [47,'lease_interest','Lease-note interest, context only']]){
 set(main,`A${n}`,label);
 ['fy','current','prior'].forEach((role,i)=>set(main,`${'BCD'[i]}${n}`,link('coverage_'+role+'_'+key),true));
 set(main,`E${n}`,`=B${n}+C${n}-D${n}`,true);
}
set(main,'A49','Historical reported-line interest coverage');
set(main,'B49','=IF(E46>0,E45/E46,NA())',true);
set(main,'A51','Capitalization basis: Unavailable. See About.');
set(main,'A52','Borrowing-only coverage: Unavailable. See About.');
set(main,'A53','Covenant headroom: Unavailable. Different contract formula.');
set(main,'A54','Lease overlap: Unavailable; row 47 is not added.');
const chart = main.charts.add('bar', main.getRange('H35:I38'));
chart.title = 'Cash capex exceeded operating cash flow';
chart.titleTextStyle.typeface = 'Arial';
chart.titleTextStyle.fontSize = 13;
chart.hasLegend = false;
chart.xAxis = {axisType:'textAxis',tickLabelPosition:'low',textStyle:{typeface:'Arial',fontSize:11},majorGridlines:null};
chart.yAxis = {numberFormatCode:'#,##0,,',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};
chart.yAxis.title.text='USD millions';
chart.series.items[0].fill = '#737985';
chart.setPosition('D5','L20');
set(main,'D4','June–August 2026. USD millions. The second bar subtracts specified prepayments from OCF.');

set(due,'A2','Oracle payment dates and financing limits');
set(due,'A3','At August 31, 2026. USD millions. Leases include interest; no combined obligations total.');
due.getRange('A5:F5').values = [['Due period','Operating leases','Finance leases','Purchase and other','Due from','Due through']];
for (let i=0;i<7;i++) {
  const r=i+6, bucket=review.schedules.operating.rows[i];
  set(due,`A${r}`,bucket.label);
  ['operating','finance','purchase'].forEach((k,j)=>set(due,`${'BCD'[j]}${r}`,link(`${k}_${i}`),true));
  due.getRange(`E${r}:F${r}`).values=[[toDate(bucket.due_start),toDate(bucket.due_end)]];
}
due.getRange('E6:F12').setNumberFormat('mmm d, yyyy');
for (const [r,label,op,fin,purchase] of [
  [14,'Calculated payment total','=SUM(B6:B12)','=SUM(C6:C12)','=SUM(D6:D12)'],
  [15,'Reported payment total',link('operating_total'),link('finance_total'),link('purchase_total')],
  [16,'Payment-total difference','=B14-B15','=C14-C15','=D14-D15'],
  [17,'Less: imputed interest',link('operating_interest'),link('finance_interest'),null],
  [18,'Calculated lease liability','=B14-B17','=C14-C17',null],
  [19,'Reported lease liability',link('operating_liability'),link('finance_liability'),null],
  [20,'Lease-liability difference','=B18-B19','=C18-C19',null],
]) {
  set(due,`A${r}`,label);
  [op,fin,purchase].forEach((f,j)=>{if(f) set(due,`${'BCD'[j]}${r}`,f,true);});
}
set(due,'A22','Operating leases not yet commenced'); set(due,'B22',link('not_commenced'),true);
set(due,'D22','Commencement FY2027–2029; terms 15–19 years. Annual payment timing Unavailable.');
entry(due,24,'Original revolver commitment',link('facility_commitment'),'Agreement dated March 6, 2026. Original maturity March 6, 2031.');
entry(due,25,'Revolver drawn at May 31',link('facility_drawn'),'Historical drawing balance only.');
set(due,'A26','August drawable revolver capacity'); set(due,'D26','Unavailable: current drawings, conditions and covenant headroom not established.');
entry(due,27,'Minimum contractual interest coverage',link('covenant_minimum'),'3.0x, contract-defined. Current covenant headroom Unavailable.');
due.getRange('B27').setNumberFormat('0.0"x"');
set(due,'A29','The May borrowing schedule is historical; remaining August debt maturities are Unavailable.');
set(due,'A30','The $20B gross ATM program was fully used in Q1. It is not unused equity capacity.');
set(due,'A31','Purchase obligations, unpaid capex and leases may overlap. No aggregate funding requirement is inferred.');
entry(due,33,'Unpaid capex, noncash disclosure',link('unpaid_capex'),'Payment dates and overlap with purchase obligations are Unavailable.');

set(repay,'A2','Oracle repayment funding review');
set(repay,'A3','At August 31, 2026. USD millions. Future coverage is Unavailable; no combined funding total.');
repay.getRange('A5:E5').values=[['Resource','USD millions','Date / period','Available for future payments?','Evidence / condition']];
repayment.resources.forEach((resource,i)=>{
 const n=i+6;
 set(repay,`A${n}`,resource.label);
 set(repay,`B${n}`,resource.key==='restricted'?"='Cash analysis'!B21":link(resource.input_key),true);
 set(repay,`C${n}`,resource.period_start===resource.period_end?resource.period_end:resource.period_start+' to '+resource.period_end);
 set(repay,`D${n}`,resource.key==='restricted'?'Excluded':resource.key==='cash'?'Not allocated; future availability Unavailable':resource.key==='revolver'?'Drawable capacity Unavailable':'Historical flow; already in cash');
 set(repay,`E${n}`,resource.detail);
});
set(repay,'A13','One shared cash pool. OCF, prepayments and equity proceeds are not added to closing cash again.');
repay.getRange('A15:G15').values=[['Due period','Obligation','USD millions','Potential funding','Confirmed funds at due date, USD millions','Coverage (x)','Competing uses / missing evidence']];
repayment.obligations.forEach((o,i)=>{
 const n=i+16;
 repay.getRange(`A${n}:G${n}`).values=[[o.period,o.label,null,o.candidate_resources,null,'Unavailable',o.competing_uses+' '+o.coverage_detail]];
 set(repay,`C${n}`,link(o.key),true);
});
set(repay,'A38','Dates are fiscal buckets, not specific payment days. See Payment dates for exact period boundaries.');
set(repay,'A39','Blank confirmed funding is Unavailable, not zero. No cash pool is allocated to several obligations.');
set(repay,'A40','Remaining August borrowing principal and interest dates are Unavailable. Current borrowing is carrying value.');
set(repay,'A42','Historical debt principal at May 31, 2026 — not the remaining August schedule');
repay.getRange('A43:F43').values=[['Historical bucket','USD millions','Due from','Due through','Basis','Why not used for coverage?']];
repayment.historical_debt.forEach((o,i)=>{
 const n=i+44;
 repay.getRange(`A${n}:F${n}`).values=[[o.label,null,toDate(o.due_start),toDate(o.due_end),'May 31 principal, excluding interest and leases','Quarter repayments cannot be assigned to these buckets; no August roll-forward is inferred.']];
 set(repay,`B${n}`,link('annual_'+i),true);
});
repay.getRange('C44:D49').setNumberFormat('mmm d, yyyy');
set(repay,'A51','Obligations without usable payment dates');
repay.getRange('A52:D52').values=[['Disclosure','USD millions','Payment timing','Limitation']];
repayment.gaps.forEach((g,i)=>{
 const n=i+53;set(repay,`A${n}`,g.label);set(repay,`C${n}`,'Unavailable');set(repay,`D${n}`,g.detail);
 if(i>0)set(repay,`B${n}`,link(i===1?'not_commenced':'unpaid_capex'),true);
});
set(repay,'A57','Revolver availability by evidence date');
repay.getRange('A58:G58').values=[['Evidence date','Commitment, USD millions','Advances, USD millions',
 'Undrawn commitment, USD millions','Drawable capacity','Covenant evidence','Date-specific limit']];
revolver.dates.forEach((r,i)=>{
 const n=59+i;set(repay,`A${n}`,toDate(r.date));
 if(i<2)set(repay,`B${n}`,link(i===0?'facility_commitment':'facility_may_commitment'),true);
 if(i===1){set(repay,`C${n}`,link('facility_drawn'),true);set(repay,`D${n}`,`=IF(COUNT(B${n}:C${n})=2,B${n}-C${n},NA())`,true);}
 set(repay,`E${n}`,'Unavailable');set(repay,`F${n}`,r.compliance);
 set(repay,`G${n}`,r.detail+' '+r.drawable_detail);
});
set(repay,'A63','Revolver contract terms. Source evidence is on Data.');
repay.getRange('A64:D64').values=[['Term','USD millions, if applicable','Filing location','Interpretation / condition']];
revolver.terms.forEach((t,i)=>{
 const n=65+i;set(repay,`A${n}`,t.label);set(repay,`C${n}`,t.location);
 set(repay,`D${n}`,`='Data'!O${rows.get('revolver_term_'+i)}`,true);
 if(t.label==='Conditional increase ceiling')set(repay,`B${n}`,link('facility_increase_ceiling'),true);
});
set(repay,'A74','Later saved filings. Balances are not carried forward.');
repay.getRange('A75:D75').values=[['Filed','Documents checked','Event date','Revolver finding']];
revolver.later.forEach((event,i)=>{
 const n=76+i;set(repay,`A${n}`,toDate(event.date));set(repay,`B${n}`,'8-K and Exhibit 99.1');
 set(repay,`C${n}`,toDate(revolver.sources[event.sources[0]].period));set(repay,`D${n}`,event.detail);
});
set(repay,'A79','Saved-source scope');set(repay,'D79',revolver.scope);
set(repay,'A81','Blank commitment, advances or undrawn cells mean Unavailable. A dash is a reported zero.');

about.getRange('A1:C1').values = [['Topic','Explanation','Source']];
const notes = [
  ['Snapshot','Saved Oracle review of June 1–August 31, 2026, checked October 15, 2026. Not live data or investment advice.',null],
  ['Workbook','Repayment review pairs obligations with resource evidence and explicit gaps. Cash analysis calculates historical contributions. Payment dates keeps contracts on their own bases. Data retains reported inputs and sources.',null],
  ['Colors and units','Arial 10. Dollar inputs are full USD displayed in millions. Blue inputs, green cross-sheet links, black same-sheet calculations. OCF less specified prepayments stays black because it subtracts two cells on Cash analysis. A dash is a reported zero; blank capacity is Unavailable.',null],
  ['Missing inputs','A missing numeric input produces #N/A in dependent calculations rather than zero. Data is a frozen source record, not forecast assumptions.',null],
  ['Cash basis','Ending total cash of 38.934B includes restricted cash. Balance-sheet cash is 36.369B; the 2.565B difference is derived from these exact rounded-million totals.',review.source_url],
  ['Customer prepayments','11.363B is the specified cash-flow contribution within OCF. Subtracting it does not isolate recurring cash flow or remove future service costs.',review.source_url],
  ['Commercial paper','Cash-flow CP repayments show zero; MD&A describes about 1.1B. Grouped debt repayments of 4.202B are counted once; classification is unresolved.',review.source_url],
  ['Agreement review',review.facility.detail,review.facility.source_url],
  ['Agreement definitions','Contract EBITDA includes specified addbacks and exclusions. Cash interest includes finance-lease interest and specified swap costs, net of cash interest income. Generic ratios do not establish compliance.',review.facility.source_url],
  ['8-K event Sep 10, filed Sep 10','Accession 0001193125-26-387905, main document and Ex.99.1 checked. Reports the same quarter equity program and dividends, not another equity inflow or later borrowing.','https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-ex99_1.htm'],
  ['8-K event Sep 12, filed Sep 14','Accession 0001193125-26-389753, main document and Ex.99.1 checked. Insider trading-plan cancellation; no corporate financing event identified.','https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/d20034dex991.htm'],
  ['Later filing scope','Two saved later 8-Ks and exhibits reviewed. This does not rebuild a complete current submissions index. Unmatched later filings remain Not checked.',null],
  ['Repayment limits','Remaining August debt principal dates, drawable credit and future operating cash generation are Unavailable. No overall future repayment surplus or shortfall can be established.',null],
  ['Revolver audit',revolver.conclusion+' '+revolver.scope,null],
  ['Revolver arithmetic','May 31 undrawn commitment = reported commitment less outstanding advances. This is not a verified drawable amount. March 6 and August 31 undrawn cells stay blank because advances or the current commitment are not established.',null],
  ['Historical interest coverage',interestReview.formula+'. '+interestReview.ttm_formula+'. Reported operating income is used without adjusted earnings addbacks. This is a historical accrual measure, not future repayment coverage.','docs/oracle_interest_coverage.md'],
  ['Interest capitalization basis',interestReview.basis,interestReview.inputs.fy_interest.source_url],
  ['Interest composition',interestReview.composition,interestReview.inputs.fy_interest.source_url],
  ['Borrowing and covenant limits',interestReview.limitations,review.facility.source_url],
  ['Lease interest context','279M annual + 126M current quarter − 48M comparative = 357M TTM. This separately reported expense is not added to or subtracted from the selected interest line because overlap is not established.','10-K Leases Note 9 p. 88; 10-Q Leases Note 6 p. 12'],
];
about.getRange(`A2:C${notes.length+1}`).values = notes;

for (const sheet of [repay,main,due,data,about]) {
  sheet.showGridLines=false;
  const used=sheet.getUsedRange();
  // Set the common font without overwriting the financial input/link colors already applied.
  used.format.font.name='Arial'; used.format.font.size=10;
  used.format.rowHeight=24;
  used.format.verticalAlignment='center';
  used.format.wrapText=false;
}
for (const sheet of [main,due]) {
  sheet.getRange('A2').format.font.bold=true;
  sheet.getRange('A2').format.font.size=14;
  sheet.getRange('A3').format.font.italic=true;
  sheet.getRange('A1:A33').format.columnWidth=53;
  sheet.getRange('B1:C33').format.columnWidth=20;
  sheet.getRange('D1:F33').format.columnWidth=20;
  sheet.getRange('G1:Q33').format.columnWidth=11;
  sheet.getRange('B5:B33').setNumberFormat(USD);
  sheet.getRange('A29:A32').format.font.italic=true;
  sheet.getRange('D5:D28').format.wrapText=true;
}
// Override only the measure rows after the monetary range format above.
main.getRange('B27').setNumberFormat('0.0%');
due.getRange('B27').setNumberFormat('0.0"x"');
due.getRange('B6:D20').setNumberFormat(USD);
due.getRange('E1:F33').format.columnWidth=20;
due.getRange('E6:F12').setNumberFormat('mmm d, yyyy');
main.getRange('D5:F28').clear({applyTo:'contents'});
main.getRange('D1:L40').format.columnWidth=11;
main.getRange('A5:A27').format.wrapText=true;
main.getRange('A5:B27').format.rowHeight=30;
for (const r of [22,24,25,26,27,33]) due.getRange(`D${r}:F${r}`).format.rowHeight=42;
due.getRange('D22:F33').format.wrapText=true;
due.getRange('D22:D33').format.columnWidth=53;
for (const [sheet,range] of [[main,'A4:B4'],[due,'A5:F5'],[data,'A1:O1'],[about,'A1:C1']]) {
  sheet.getRange(range).format.font.bold=true;
  sheet.getRange(range).format.borders={bottom:{style:'thin',color:'#AEB4BD'}};
}
for (const r of [11,12,16,17,20,25,26]) main.getRange(`A${r}:B${r}`).format.font.bold=true;
for (const r of [19,23]) main.getRange(`B${r}`).setNumberFormat('#,##0.00,,;(#,##0.00,,);0.00');
for (const r of [16,20]) due.getRange(`B${r}:D${r}`).setNumberFormat('#,##0.00,,;(#,##0.00,,);0.00');
main.getRange('H35:I38').format.wrapText=true;
main.getRange('H35:H38').format.columnWidth=26;
main.getRange('H35:I38').format.rowHeight=38;
main.getRange('D4').format.wrapText=false;
set(main,'D22','Reported OCF less capex = B6 − B10.');
set(main,'D23','Excluding specified prepayments = B8 − B10.');
set(main,'D25','The prepayment exclusion is historical arithmetic, not recurring cash generation.');
main.getRange('D22:D25').format.wrapText=false;
data.getRange(`A1:R${sourceRows.length+1}`).format.rowHeight=45;
data.getRange(`A1:A${sourceRows.length+1}`).format.columnWidth=24;
data.getRange(`B1:B${sourceRows.length+1}`).format.columnWidth=19;
data.getRange(`C1:C${sourceRows.length+1}`).format.columnWidth=48;
data.getRange(`D1:G${sourceRows.length+1}`).format.columnWidth=19;
data.getRange(`H1:J${sourceRows.length+1}`).format.columnWidth=48;
data.getRange(`K1:L${sourceRows.length+1}`).format.columnWidth=12;
data.getRange(`M1:O${sourceRows.length+1}`).format.columnWidth=65;
data.getRange(`P1:Q${sourceRows.length+1}`).format.columnWidth=45;
data.getRange(`R1:R${sourceRows.length+1}`).format.columnWidth=80;
data.getUsedRange().format.wrapText=true;
for(const [i,t] of revolver.terms.entries()){
 const n=rows.get('revolver_term_'+i);
 data.getRange(`A${n}:O${n}`).format.rowHeight=Math.max(60,Math.ceil(t.detail.length/85)*12+18);
}
data.freezePanes.freezeRows(1);
about.getRange(`A1:A${notes.length+1}`).format.columnWidth=33;
about.getRange(`B1:B${notes.length+1}`).format.columnWidth=100;
about.getRange(`C1:C${notes.length+1}`).format.columnWidth=65;
about.getUsedRange().format.wrapText=true;
about.getUsedRange().format.rowHeight=60;
about.freezePanes.freezeRows(1);
for (const address of ['A4:B12','A13:B23','A25:B27','H35:I38']) frame(main,address);
for (const address of ['A5:F20','A22:B22','A24:B27','A33:B33']) frame(due,address);
for (const [sheet,address] of [[main,'A4:B4'],[main,'H35:I35'],[due,'A5:F5'],[data,'A1:O1'],[about,'A1:C1']]) header(sheet,address);
for (const n of [8,11,12,16,17,20,25,26]) subtotal(main,`A${n}:B${n}`);
for (const n of [14,18]) subtotal(due,`A${n}:D${n}`);
frame(data,`A1:R${sourceRows.length+1}`);frame(about,`A1:C${notes.length+1}`);
header(data,'A1:R1');
main.getRange('A41').format.font.bold=true;main.getRange('A41').format.font.size=14;
main.getRange('A44:E49').format.font.name='Arial';main.getRange('A44:E49').format.font.size=10;
main.getRange('A44:E49').format.rowHeight=32;main.getRange('A44:E49').format.verticalAlignment='center';
main.getRange('A44:E44').format.wrapText=true;
main.getRange('B45:E47').setNumberFormat(USD);main.getRange('B45:D47').format.font.color='#008000';
main.getRange('E45:E47').format.font.color='#000000';
main.getRange('B49').setNumberFormat('0.00"x"');main.getRange('A49:B49').format.font.italic=true;
header(main,'A44:E44');frame(main,'A44:E47');subtotal(main,'A49:B49');
main.getRange('A51:A54').format.font.size=10;main.getRange('A51:A54').format.rowHeight=26;
for(let n=notes.length-3;n<=notes.length+1;n++)about.getRange(`A${n}:C${n}`).format.rowHeight=115;
repay.getRange('A2').format.font.bold=true;repay.getRange('A2').format.font.size=14;
for(const [i,width] of [26,31,23,66,36,26,100].entries())repay.getRangeByIndexes(0,i,55,1).format.columnWidth=width;
repay.getRange('A5:G55').format.wrapText=true;
repay.getRange('A6:E11').format.rowHeight=100;
repay.getRange('A11:E11').format.rowHeight=130;
repay.getRange('A16:G36').format.rowHeight=65;
repay.getRange('A44:F49').format.rowHeight=65;
repay.getRange('A53:D55').format.rowHeight=100;
for(const a of ['B6:B11','C16:C36','E16:E36','B44:B49','B53:B55'])repay.getRange(a).setNumberFormat(USD);
for(const a of ['B6:B11','C16:C36','B44:B49','B53:B55'])repay.getRange(a).format.font.color='#008000';
for(const a of ['A5:E11','A15:G36','A43:F49','A52:D55'])frame(repay,a);
for(const a of ['A5:E5','A15:G15','A43:F43','A52:D52']){header(repay,a);repay.getRange(a).format.rowHeight=48;}
repay.getRange('A58:G79').format.wrapText=true;
repay.getRange('A59:A61').setNumberFormat('mmm d, yyyy');
repay.getRange('B59:D61').setNumberFormat(USD);
repay.getRange('B59:C60').format.font.color='#008000';
repay.getRange('D60').format.font.color='#000000';
repay.getRange('A59:G61').format.rowHeight=100;
for(const [n,height] of [[65,48],[66,85],[67,95],[68,72],[69,105],[70,125],[71,65],[72,100]])
 repay.getRange(`A${n}:D${n}`).format.rowHeight=height;
repay.getRange('B65:B72').setNumberFormat(USD);
repay.getRange('B68').format.font.color='#008000';
repay.getRange('A76:D77').format.rowHeight=75;
repay.getRange('D79').format.rowHeight=100;
repay.getRange('A76:A77').setNumberFormat('mmm d, yyyy');
repay.getRange('C76:C77').setNumberFormat('mmm d, yyyy');
for(const a of ['A58:G61','A64:D72','A75:D77'])frame(repay,a);
for(const a of ['A58:G58','A64:D64','A75:D75']){header(repay,a);repay.getRange(a).format.rowHeight=52;}
// Formula colors express dependencies, never whether a cash amount is favorable.
main.getRange('B8').format.font.color='#000000';

wb.recalculate();
const expected = {B8:11740000000,B11:-5396000000,B12:-16759000000,B16:7645000000,
  B17:38934000000,B19:0,B20:36369000000,B21:2565000000,B23:0,B25:-12264000000,B26:-23627000000};
for (const [cell,value] of Object.entries(expected)) {
  if(main.getRange(cell).values[0][0] !== value) throw new Error(`Reconciliation failed at ${cell}`);
}
for (const cell of ['B16','C16','D16','B20','C20']) {
  if(due.getRange(cell).values[0][0] !== 0) throw new Error(`Payment reconciliation failed ${cell}`);
}
// A blank source must propagate as unavailable, not turn into a plausible zero.
const inputCell=data.getRange(`B${rows.get('prepay')}`), original=inputCell.values;
inputCell.values=[[null]]; wb.recalculate();
if(typeof main.getRange('B12').values[0][0] === 'number') throw new Error('Blank prepayments concealed');
inputCell.values=original; wb.recalculate();
const changed = data.getRange(`B${rows.get('prepay')}`);
changed.values=[[original[0][0]+1000000]]; wb.recalculate();
if(main.getRange('B12').values[0][0]!==-16760000000) throw new Error('Prepayment exclusion does not recalculate');
changed.values=original; wb.recalculate();
if(repay.getRange('D60').values[0][0]!==10000000000)throw new Error('May undrawn commitment arithmetic failed');
for(const n of [59,61])if(repay.getRange(`D${n}`).values[0][0]!==null)throw new Error('Unsupported undrawn amount');
const mayInput=data.getRange(`B${rows.get('facility_may_commitment')}`),mayOriginal=mayInput.values;
mayInput.values=[[null]];wb.recalculate();
if(typeof repay.getRange('D60').values[0][0]==='number')throw new Error('Missing commitment became undrawn capacity');
mayInput.values=[[mayOriginal[0][0]-1000000]];wb.recalculate();
if(repay.getRange('D60').values[0][0]!==9999000000)throw new Error('Undrawn commitment does not recalculate');
mayInput.values=mayOriginal;wb.recalculate();
console.log(JSON.stringify({cash:expected,payments:due.getRange('B14:D20').values}));
for(const [cell,key] of [['E45','operating_income'],['E46','interest'],['E47','lease_interest'],['B49','value']]){
 if(main.getRange(cell).values[0][0]!==interestReview.calculation[key])throw new Error('Interest reconciliation '+cell);
}
const interestInput=data.getRange(`B${rows.get('coverage_current_interest')}`),interestOriginal=interestInput.values;
interestInput.values=[[null]];wb.recalculate();
if(typeof main.getRange('B49').values[0][0]==='number')throw new Error('Missing interest became coverage');
interestInput.values=interestOriginal;
const interestCells=['fy','current','prior'].map(p=>data.getRange(`B${rows.get('coverage_'+p+'_interest')}`));
const originals=interestCells.map(c=>c.values);interestCells.forEach(c=>c.values=[[0]]);wb.recalculate();
if(typeof main.getRange('B49').values[0][0]==='number')throw new Error('Zero interest divided');
interestCells.forEach((c,i)=>c.values=originals[i]);
const opInput=data.getRange(`B${rows.get('coverage_current_operating_income')}`),opOriginal=opInput.values;
opInput.values=[[opOriginal[0][0]+1e6]];wb.recalculate();
if(Math.abs(main.getRange('B49').values[0][0]-(interestReview.calculation.operating_income+1e6)/interestReview.calculation.interest)>1e-12)throw new Error('Coverage does not recalculate');
opInput.values=opOriginal;wb.recalculate();
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!',
  options:{useRegex:true,maxResults:20},maxChars:1200})).ndjson);
const fundingManifest=await finishFundingSheet(wb,root,'ORCL',funding);
const output=path.join(root,'samples/oracle_liquidity.xlsx');
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
await fs.rm(output+'.inspect.ndjson',{force:true});
const digest = b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.writeFile(output.replace('.xlsx','.manifest.json'),JSON.stringify({...fundingManifest,review_sha256:digest(sourceBytes),
  financing_sha256:digest(annualBytes),
  revolver_sha256:digest(revolverBytes),
  interest_sha256:digest(interestBytes),
  workbook_sha256:digest(await fs.readFile(output))},null,2)+'\n');
if(process.env.SKIP_UNCHANGED_RENDERS!=='1') for (const [sheet,range,file] of [['Repayment review','A2:E11','resources'],['Repayment review','A15:D21','repayment'],
  ['Repayment review','E15:G21','funding-gaps'],['Repayment review','A43:F49','historical'],['Repayment review','A51:D55','undated'],
  ['Cash analysis','A2:B27','cash'],['Cash analysis','D4:L25','chart'],
  ['Cash analysis','A41:E54','interest'],
  ['Data',`A${rows.get('coverage_fy_operating_income')}:H${sourceRows.length+1}`,'interest-inputs'],
  ['Data',`I${rows.get('coverage_fy_operating_income')}:R${sourceRows.length+1}`,'interest-contexts'],
  ['Repayment review','A57:D61','revolver-amounts'],['Repayment review','E58:G61','revolver-limits'],
  ['Repayment review','A63:D68','revolver-terms-1'],['Repayment review','A69:D72','revolver-terms-2'],
  ['Repayment review','A74:D81','revolver-later'],
  ['Payment dates','A2:F33','payments'],['Data','A1:G6','inputs'],['Data','H1:O6','provenance'],
  ['Data',`A${rows.get('facility_may_commitment')}:H${rows.get('facility_increase_ceiling')}`,'revolver-inputs'],
  ['Data',`M${rows.get('facility_may_commitment')}:O${rows.get('revolver_term_1')}`,'revolver-sources'],
  ['Data',`M${rows.get('revolver_term_2')}:O${rows.get('revolver_term_5')}`,'revolver-term-sources'],
  ['Data',`H${rows.get('revolver_source_annual')}:O${sourceRows.length+1}`,'revolver-document-sources'],
  ['About',`A1:C${notes.length+1}`,'about']]) {
  const preview=await wb.render({sheetName:sheet,range,scale:1.4,format:'png'});
  await fs.writeFile(path.join(process.cwd(),`oracle-liquidity-${file}.png`),new Uint8Array(await preview.arrayBuffer()));
}
console.log('Exported',output);
await fs.rm(output+'.inspect.ndjson',{force:true});
