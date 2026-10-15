// Run from a temporary directory using the Codex artifact runtime; deployment only serves the saved file.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = process.argv[2];
if (!root) throw new Error('Pass the repository directory');
const samplePath = path.join(root, 'samples/oracle_liquidity.json');
const sourceBytes = await fs.readFile(samplePath);
const review = JSON.parse(sourceBytes);
if (review.status !== 'Checked' || Object.values(review.schedules).some(s => s.status !== 'Checked')) {
  throw new Error('Source review has incomplete reconciliations');
}
const wb = Workbook.create();
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
data.getRange('A1:O1').values = [['Key','USD unless labelled x','Reported input','Period start','Period end / as of',
  'Form','Filed','Accession','Tag','Context ID','Scale','Decimals','Source','Filing location','Unavailable reason']];
data.getRange(`A2:O${sourceRows.length+1}`).values = sourceRows;
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
main.getRange('H35:I40').values = [['Quarter measure','USD'],['Reported OCF',null],['OCF less\nprepayments',null],
  ['Cash capex',null],['OCF less\ncash capex',null],['OCF less prepayments\nand capex',null]];
for (const [r, source] of [[36,6],[37,8],[38,10],[39,11],[40,12]]) set(main,`I${r}`,`=B${source}`,true);
main.getRange('I36:I40').setNumberFormat(USD);
const chart = main.charts.add('bar', main.getRange('H35:I40'));
chart.title = 'Quarter cash flow and capex (USD billions)';
chart.titleTextStyle.typeface = 'Arial';
chart.titleTextStyle.fontSize = 13;
chart.hasLegend = false;
chart.xAxis = {axisType:'textAxis',tickLabelPosition:'low',textStyle:{typeface:'Arial',fontSize:11},majorGridlines:null};
chart.yAxis = {numberFormatCode:'0.0,,,',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};
chart.series.items[0].fill = '#737985';
chart.setPosition('D4','L20');

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

about.getRange('A1:C1').values = [['Topic','Explanation','Source']];
const notes = [
  ['Snapshot','Saved Oracle review of June 1–August 31, 2026, checked October 15, 2026. Not live data or investment advice.',null],
  ['Workbook','Cash analysis calculates funding contributions. Payment dates keeps contracts on their own bases. Data retains reported inputs and sources.',null],
  ['Colors and units','Arial 10. Dollar inputs are full USD displayed in millions. Blue inputs, green links, black calculations. A dash is a reported zero; blank capacity is Unavailable.',null],
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
];
about.getRange(`A2:C${notes.length+1}`).values = notes;

for (const sheet of [main,due,data,about]) {
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
main.getRange('H35:I40').format.wrapText=true;
main.getRange('H35:I40').format.rowHeight=38;
data.getRange(`A1:O${sourceRows.length+1}`).format.rowHeight=45;
data.getRange(`A1:A${sourceRows.length+1}`).format.columnWidth=24;
data.getRange(`B1:B${sourceRows.length+1}`).format.columnWidth=19;
data.getRange(`C1:C${sourceRows.length+1}`).format.columnWidth=48;
data.getRange(`D1:G${sourceRows.length+1}`).format.columnWidth=19;
data.getRange(`H1:J${sourceRows.length+1}`).format.columnWidth=48;
data.getRange(`K1:L${sourceRows.length+1}`).format.columnWidth=12;
data.getRange(`M1:O${sourceRows.length+1}`).format.columnWidth=65;
data.getUsedRange().format.wrapText=true;
data.freezePanes.freezeRows(1);
about.getRange('A1:A14').format.columnWidth=33;
about.getRange('B1:B14').format.columnWidth=100;
about.getRange('C1:C14').format.columnWidth=65;
about.getUsedRange().format.wrapText=true;
about.getUsedRange().format.rowHeight=60;
about.freezePanes.freezeRows(1);

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
console.log(JSON.stringify({cash:expected,payments:due.getRange('B14:D20').values}));
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!',
  options:{useRegex:true,maxResults:20},maxChars:1200})).ndjson);
const output=path.join(root,'samples/oracle_liquidity.xlsx');
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
await fs.rm(output+'.inspect.ndjson',{force:true});
const digest = b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.writeFile(output.replace('.xlsx','.manifest.json'),JSON.stringify({review_sha256:digest(sourceBytes),
  workbook_sha256:digest(await fs.readFile(output))},null,2)+'\n');
for (const [sheet,range,file] of [['Cash analysis','A2:B27','cash'],['Cash analysis','D4:L20','chart'],
  ['Payment dates','A2:F20','payments'],['Data','A1:G6','inputs'],['About','A1:B14','about']]) {
  const preview=await wb.render({sheetName:sheet,range,scale:1.4,format:'png'});
  await fs.writeFile(path.join(process.cwd(),`oracle-liquidity-${file}.png`),new Uint8Array(await preview.arrayBuffer()));
}
console.log('Exported',output);
await fs.rm(output+'.inspect.ndjson',{force:true});
