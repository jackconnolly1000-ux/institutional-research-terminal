import {addCoreChartSheet,finishCoreChartSheet} from './core_chart_sheet.mjs';
import {addBorrowingLeaseSheet,finishBorrowingLeaseSheet} from './borrowing_lease_sheet.mjs';
import {addRatioSheet,finishRatioSheet} from './ratio_sheet.mjs';
import {addHistorySheet,finishHistorySheet} from './history_sheet.mjs';
import {documentationLinks} from './workbook_style.mjs';
import {addFundingSheet,finishFundingSheet} from './funding_sheet.mjs';
// Build only Lilly's checked review. No network or application dependency is required.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
import {frame,header,subtotal} from './workbook_style.mjs';
const root=process.argv[2];
const source=await fs.readFile(path.join(root,'samples/liquidity_pilots.json'));
const snapshot=JSON.parse(source).snapshots.find(s=>s.ticker==='LLY');
if(snapshot.metrics.cash.accession!=='0000059478-26-000081')throw new Error('Lilly disclosure notes require the checked June filing');
const reviewBytes=await fs.readFile(path.join(root,'samples/lly_liquidity.json'));
const review=JSON.parse(reviewBytes);
const financingBytes=await fs.readFile(path.join(root,'samples/lly_financing.json'));
const financing=JSON.parse(financingBytes);
const interestBytes=await fs.readFile(path.join(root,'samples/lly_interest.json'));
const interestReview=JSON.parse(interestBytes),ic=interestReview.calculation;
if(ic.value===null||ic.detail)throw new Error('Incomplete interest coverage');
if(financing.status!=='Checked'||financing.rows.length!==8||financing.initial_principal_total!==financing.reported_issue_total)throw new Error('Incomplete financing audit');
if(!review.cash||!review.notes_schedule||review.disclosures.length!==10)throw new Error('Incomplete Lilly evidence');
const wb=Workbook.create();
const funding=addFundingSheet(wb,root,'LLY');
const borrowingLeases=addBorrowingLeaseSheet(wb,root,'LLY');
const ratios=addRatioSheet(wb,root,'LLY');
const main=wb.worksheets.add('Debt and liquidity');
const history=addHistorySheet(wb,root,'LLY');
const coreCharts=addCoreChartSheet(wb,root,'LLY');
const repayment=wb.worksheets.add('Repayment review');
const data=wb.worksheets.add('Data'),about=wb.worksheets.add('About');
const USD='#,##0,,;(#,##0,,);"-"',date=s=>s?new Date(s+'T00:00:00Z'):null;
const inputs=[],index=new Map();
function leaf(f){
 const key=[f.tag,f.period_start||'',f.period_end,f.accession].join('|');
 if(!index.has(key)){
  const row=inputs.length+2;index.set(key,row);
  inputs.push([f.label,f.value,date(f.period_start),date(f.period_end),f.form,date(f.filed),f.accession,
   f.tag,f.context_id||null,f.scale??null,f.decimals??null,f.source_url||snapshot.source_url,
   f.selection_rule||'',f.detail||'',(f.notes||[]).join(' ')]);
 }
 const cell=`'Data'!B${index.get(key)}`;
 return `IF(ISNUMBER(${cell}),${cell},NA())`;
}
const m=snapshot.metrics;
leaf(m.cash);m.gross_debt.inputs.forEach(leaf);
leaf(m.current_ratio.inputs.current_liabilities);leaf(m.current_ratio.inputs.current_assets);
for(const key of ['operating_cash_flow','capital_spending'])m[key].inputs.forEach(leaf);
data.getRange(`A1:O${inputs.length+1}`).values=[['Input','USD millions','Period start','Period end','Form','Filed','Accession','Tag','Context','Scale','Decimals','Source','Selection rule','Unavailable reason','Notes'],...inputs];
data.getRange(`B2:B${inputs.length+1}`).format.font.color='#0000FF';
data.getRange(`B2:B${inputs.length+1}`).setNumberFormat(USD);
for(const col of ['C','D','F'])data.getRange(`${col}2:${col}${inputs.length+1}`).setNumberFormat('mmm d, yyyy');
main.getRange('A2').values=[['Eli Lilly and Company']];
main.getRange('A3').values=[['Balance sheet June 30, 2026. TTM July 2025–June 2026. USD millions unless ratio or %.']];
main.getRange('A5:D5').values=[['Measure','Value','Period end','Basis / limitation']];
const order=['cash','gross_debt','net_debt','current_ratio','operating_cash_flow','capital_spending','free_cash_flow','ocf_to_debt','fcf_to_debt'];
main.getRange('B6:B14').setNumberFormat(USD);main.getRange('B9').setNumberFormat('0.00"x"');main.getRange('B13:B14').setNumberFormat('0.0%');
main.getRange('C6:C14').setNumberFormat('mmm d, yyyy');
main.getRange('A17').values=[['Selected obligations, separate from borrowing']];
main.getRange('A18:C18').values=[['Item','Disclosed amount / timing','Basis']];
const disclosures=[['Pending AtaiBeckley acquisition','Approximately $2.8B','Potential payment at closing, subject to closing conditions. Not recognized as borrowing.','10-Q MD&A, p. 31'],
 ['Venture fund commitments','Approximately $806M','Expected to be paid over up to ten years. Not recognized as borrowing.','10-Q MD&A, p. 31; Note 8']];
const disclosureHeader=inputs.length+4;
data.getRange(`A${disclosureHeader}:I${disclosureHeader+2}`).values=[['Disclosure','Amount as disclosed','As of','Form','Filed','Accession','Source','Filing location','Conditions'],
 ...disclosures.map((d,i)=>[d[0],d[1],date(i===0?'2026-08-05':'2026-06-30'),'10-Q',date('2026-08-05'),snapshot.metrics.cash.accession,snapshot.source_url,d[3],d[2]])];
for(let i=0;i<2;i++){
 const r=disclosureHeader+i+1,n=i+19;
 main.getRange(`A${n}:C${n}`).formulas=[[`='Data'!A${r}`,`='Data'!B${r}`,`='Data'!I${r}`]];
 main.getRange(`A${n}:C${n}`).format.font.color='#008000';
}
main.getRange('A23').values=[['Remaining gaps']];
main.getRange('A24').values=[['June lease liabilities and a complete updated principal schedule are Unavailable. Historical interest coverage is built below.']];
main.getRange('A25').values=[['See Repayment review for dated cash flows, facilities, acquisitions and manufacturing commitments.']];
main.getRange('A26').values=[['Financing index checked through October 15, 2026. See Repayment review for May terms; all sources and limits are in Data.']];
about.getRange('A1:C6').values=[['Topic','Explanation','Source'],
 ['Scope','Lilly only. Balance-sheet facts checked October 14, 2026; financing and interest reviewed October 15; funding interpretation checked October 16. Financial statements dated June 30. Not investment advice.',snapshot.source_url],
 ['Colors','Arial 10. Full USD displayed in millions. Blue reported inputs, green cross-sheet links, black same-sheet calculations. Zero is a dash. Missing inputs are not zero.',null],
 ['Cash generation','Fiscal year + current YTD − prior YTD. Capital spending uses Lilly’s checked other-PP&E tag. FCF excludes acquisitions, dividends and other cash uses.','docs/pilot_cashflow_reconciliation.md'],
 ['Borrowing','Balance-sheet current and noncurrent borrowing are added once. Fair-value table carrying amounts are not added again.','docs/pilot_evidence_lly.md'],
 ['Selected commitments','Descriptions retain their disclosure dates; AtaiBeckley was disclosed after quarter end. They are not added to debt or to each other.',snapshot.source_url]];
// New review inputs have stable keys and explicit dimensions: same-tag note buckets never collapse.
const auditHeader=disclosureHeader+5,auditRows=new Map();
const contractRecord=(r)=>{
 const source=financing.sources[r.source];
 return {value:r.initial_principal,label:r.label+' — May 20 initial issue',period_start:null,period_end:r.stated_maturity,
 form:source.form,filed:source.filed,accession:source.accession,tag:null,context_id:null,scale:null,decimals:null,
 source_url:source.url,location:r.location,source_kind:r.source_kind,dimensions:[],sha256:source.sha256,
 detail:r.basis+'. Issued '+r.issued+'. '+r.detail,coupon:r.coupon,sofr_margin:r.sofr_margin};
};
const issueSource=financing.sources.offering;
const records=[...Object.entries(review.inputs),...review.disclosures.map(f=>[f.key,f]),
 ...Object.entries(interestReview.inputs).map(([key,f])=>['coverage_'+key,{...f,sha256:f.source_sha256,source_kind:'Inline XBRL',detail:f.selection_rule}]),
 ...financing.rows.map(r=>[r.key,contractRecord(r)]),
 ['may_issue_control',{value:financing.reported_issue_total,label:'Reported completed May issue, initial principal',period_start:null,period_end:'2026-05-20',form:issueSource.form,filed:issueSource.filed,accession:issueSource.accession,tag:null,context_id:null,scale:null,decimals:null,source_url:issueSource.url,location:'Item 8.01, completed offering',source_kind:'Reviewed filing text',dimensions:[],sha256:issueSource.sha256,detail:'Initial issue principal, not net cash proceeds, current outstanding debt or unused financing.'}]];
data.getRange(`A${auditHeader}:R${auditHeader+records.length}`).values=[
 ['Review input key','USD millions','Label','Period start','Date / disclosure basis','Form','Filed','Accession','Tag','Context','Scale','Decimals','Source','Filing location','Source kind','Dimensions','Limitations','Reviewed source SHA256'],
 ...records.map(([key,f],i)=>{auditRows.set(key,auditHeader+i+1);return [key,f.value,f.label,date(f.period_start),/^\d{4}-\d{2}-\d{2}$/.test(f.period_end)?date(f.period_end):f.period_end,f.form,date(f.filed),f.accession,f.tag,f.context_id,f.scale,f.decimals,f.source_url,f.location,f.source_kind,JSON.stringify(f.dimensions),f.detail||'',f.sha256];})];
data.getRange(`S${auditHeader}:T${auditHeader+records.length}`).values=[['Fixed coupon, fraction','Compounded SOFR margin, fraction'],...records.map(([,f])=>[f.coupon??null,f.sofr_margin??null])];
function ref(key){const cell=`'Data'!B${auditRows.get(key)}`;return `IF(ISNUMBER(${cell}),${cell},NA())`;}
repayment.getRange('A2').values=[['Lilly — dated liquidity and repayment review']];
repayment.getRange('A3').values=[['Saved filings reviewed October 15, 2026. Cash flows: January–June 2026. USD millions.']];
repayment.getRange('A4').values=[['H1 cash generation after PP&E was positive; acquisitions and payouts competed for it. Net borrowing contributed to cash growth. Future funding coverage: Unavailable.']];
repayment.getRange('A4:D4').merge();
repayment.getRange('A6:D6').values=[['Half-year cash build','USD millions','Period / basis','Interpretation']];
const cashRows=[
 ['Opening cash',ref('opening'),'December 31, 2025','Excludes restricted cash. Not an additional half-year flow.'],
 ['Operating cash flow',ref('ocf'),'January–June 2026','Historical; includes working capital. Future recurrence not established.'],
 ['Cash PP&E spending','-'+ref('capex'),'January–June 2026','Cash use, not a forecast of manufacturing investment.'],
 ['Cash acquisitions, net of cash acquired','-'+ref('acquisitions'),'January–June 2026','Not added again to the approximately $13.3B business-development disclosure.'],
 ['Purchased in-process R&D','-'+ref('iprd'),'January–June 2026','Separate cash use; not all acquisition-related expense is cash.'],
 ['Cash dividends','-'+ref('dividends'),'January–June 2026','Competes with repayments for cash.'],
 ['Share repurchases','-'+ref('buybacks'),'January–June 2026','Historical spending; no future pace assumed.'],
 ['Short-term borrowing, net',ref('short_debt'),'January–June 2026','Financing inflow, not recurring operating generation.'],
 ['Long-term debt proceeds, net',ref('long_proceeds'),'January–June 2026','May $9B issue is already included here; net cash differs from face amount.'],
 ['Long-term debt repaid','-'+ref('long_repayments'),'January–June 2026','Already paid; not a future maturity schedule.'],
 ['Other investing and financing','-'+ref('investments')+'-'+ref('other_investing')+'+'+ref('other_financing'),'January–June 2026','Investment purchases, other investing and other financing.'],
 ['Exchange-rate effect',ref('fx'),'January–June 2026','Reconciles the cash balance.'],
 ['Calculated cash change','SUM(B8:B18)','January–June 2026','All signed flows counted once.'],
 ['Calculated closing cash','B7+B19','June 30, 2026','Opening cash plus change.'],
 ['Reported closing cash',ref('closing'),'June 30, 2026','Not a current cash balance after subsequent payments.'],
 ['Cash reconciliation difference','B20-B21','Zero = reconciled','No cash forecast or unrestricted-funding total.'],
 ['OCF less cash PP&E spending','B8+B9','Historical H1 only','Excludes acquisitions, payouts and other cash uses.'],
 ['Net borrowing cash flow','SUM(B14:B16)','Historical H1 only','Borrowing contributed to closing cash.'],
 ['Acquisitions + purchased IPR&D','-SUM(B10:B11)','Historical H1 only','Approximately $13.3B, already spent.'],
 ['Dividends + buybacks','-SUM(B12:B13)','Historical H1 only','Not automatically recurring future obligations.'],
 ];
for(const [i,[label,formula,period,note]] of cashRows.entries()){
 const n=i+7;repayment.getRange(`A${n}:D${n}`).values=[[label,null,period,note]];
 repayment.getRange(`B${n}`).formulas=[['='+formula]];
 repayment.getRange(`B${n}`).format.font.color=formula.includes("'Data'!")?'#008000':'#000000';
}
repayment.getRange('F27:G33').values=[['H1 cash contribution','USD millions'],
 ['Operating cash flow',null],['Cash PP&E spending',null],['Acquisitions + purchased IPR&D',null],
 ['Dividends + buybacks',null],['Net borrowing',null],['Other cash flows including FX',null]];
for(const [i,formula] of ['=B8','=B9','=-B25','=-B26','=B24','=B17+B18'].entries())repayment.getRange(`G${i+28}`).formulas=[[formula]];
const chart=repayment.charts.add('bar',repayment.getRange('F27:G33'));
chart.title='What added to or used cash? January–June 2026';chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;chart.hasLegend=false;
chart.xAxis={axisType:'textAxis',tickLabelPosition:'low',textStyle:{typeface:'Arial',fontSize:10},majorGridlines:null};
chart.yAxis={numberFormatCode:'#,##0,,',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};
chart.yAxis.title.text='USD millions (negative = cash used)';chart.series.items[0].fill='#737985';chart.setPosition('F6','P24');
repayment.getRange('A29:D29').values=[['Credit capacity, dates kept separate','USD millions','Date / expiry','Availability limitation']];
const facilities=[['unused_june','June 30, 2026','Reported unused, not cash or verified drawable. $10B supports CP and is not added again.'],
 ['facility_2026','August 2026 expiry','Annual terms: 364-day facility. Exact expiry day and renewal Unavailable; do not carry June capacity past expiry.'],
 ['facility_2029','December 2029 expiry','Annual terms only. Exact day, June facility composition, contract conditions and current draws Unavailable.']];
for(const [i,[key,period,detail]] of facilities.entries()){
 const n=i+30,f=review.inputs[key]||review.disclosures.find(f=>f.key===key);
 repayment.getRange(`A${n}:D${n}`).values=[[f.label,null,period,detail]];
 repayment.getRange(`B${n}`).formulas=[['='+ref(key)]];repayment.getRange(`B${n}`).format.font.color='#008000';
}
repayment.getRange('A34:D35').values=[['Drawable credit','Unavailable','No saved credit agreement','Draw conditions, covenants, permitted uses and post-August renewal not established. Cash + commitments is not a verified funding total.'],
 ['December unused capacity',null,'December 31, 2025','Annual unused total is $10.1B, primarily the $6B and $4B facilities. The residual $0.1B is not separately described.']];
repayment.getRange('B35').formulas=[['='+ref('annual_unused')]];repayment.getRange('B35').format.font.color='#008000';
repayment.getRange('A38:D38').values=[['Acquisitions / manufacturing','USD millions','Date and classification','Timing, overlap and funding limitation']];
const obligations=review.disclosures.filter(f=>!['unused_june','cp_support'].includes(f.key));
for(const [i,f] of obligations.entries()){
 const n=i+39;repayment.getRange(`A${n}:D${n}`).values=[[f.label,null,f.period_end+' · '+f.kind,f.detail]];
 repayment.getRange(`B${n}`).formulas=[['='+ref(f.key)]];repayment.getRange(`B${n}`).format.font.color='#008000';
}
repayment.getRange('A48:D50').values=[['Contingent consideration fair value',null,'June 30, 2026','Current $814M + noncurrent $1,704M. Valuation, not dated payment or contractual maximum. Not added to acquisition amounts above.'],
 ['Future funding coverage','Unavailable','Each future obligation','Future principal dates, future cash generation, payment dates and drawable credit not all established. No coverage ratio calculated.'],
 ['Scope','Financing index through Oct 15, 2026','10-K; 10-Q; earnings and financing documents','SEC financing candidates screened through October 15. Not a complete review of all liability notes. No combined obligations total.']];
repayment.getRange('B48').formulas=[['='+ref('contingent_current')+'+'+ref('contingent_noncurrent')]];repayment.getRange('B48').format.font.color='#008000';
repayment.getRange('A53:D53').values=[['Notes grouped by due year','USD millions','Basis date','Interpretation']];
const noteKeys=Object.keys(review.inputs).filter(k=>k.startsWith('notes_'));
for(const [i,key] of noteKeys.entries()){
 const n=i+54;repayment.getRange(`A${n}:D${n}`).values=[[review.inputs[key].label,null,'December 31, 2025','Historical carrying amount; not principal cash payments. Multi-year groups are combined.']];
 repayment.getRange(`B${n}`).formulas=[['='+ref(key)]];repayment.getRange(`B${n}`).format.font.color='#008000';
}
for(const [n,label,formula,note] of [[63,'Total notes','SUM(B54:B62)','Carrying amount; not payment total.'],
 [64,'Other debt and adjustments','-'+ref('adjustment'),'Printed as (339). Tagged +339 source magnitude; presentation coefficient −1.'],
 [65,'Commercial paper',ref('annual_cp'),'Reported zero at December 31, 2025.'],
 [66,'Calculated total debt','SUM(B63:B65)','Same annual filing; no roll-forward to June.'],
 [67,'Reported total debt',ref('annual_total'),'Reconciles to annual balance sheet.'],
 [68,'Debt reconciliation difference','B66-B67','Zero = reconciled.']]){
 repayment.getRange(`A${n}:D${n}`).values=[[label,null,'December 31, 2025',note]];
 repayment.getRange(`B${n}`).formulas=[['='+formula]];repayment.getRange(`B${n}`).format.font.color=formula.includes("'Data'!")?'#008000':'#000000';
}
repayment.getRange('A70:D71').values=[['June 30 principal schedule','Unavailable','Updated payment dates missing','Do not allocate May issuance or H1 repayments to annual buckets. Current borrowing $7.050B is not an instrument-level schedule.'],
 ['Repayment conclusion',null,'Coverage Unavailable','H1 cash generation after PP&E was positive; acquisitions and payouts competed for cash. Net borrowing contributed materially. Updated debt dates, draw terms/renewal and payment calendars are needed.']];
about.getRange('A7:C8').values=[['Dated review','Repayment review uses exact H1 cash flows and historical annual carrying-debt buckets. Future coverage remains Unavailable. Text disclosures are identified separately; source hashes and dimensions are in Data.','docs/lly_liquidity_review.md'],
 ['Post-quarter events','July acquisition cash is separate from June cash. The July $3.9B ceiling includes upfront cash. August $4.5B manufacturing announcement has no dated cash schedule. No overlap total inferred.',review.sources.release.source_url]];
repayment.getRange('A74').values=[['May 2026 issue — documented stated maturities']];
repayment.getRange('A75:D75').merge();repayment.getRange('A75').values=[['Initial issue principal, not a complete June/October outstanding-debt schedule. Already in June borrowing and H1 proceeds; do not add to either.']];
repayment.getRange('A76:D76').values=[['Series','Initial principal, USD millions','Stated maturity','Contract rate']];
for(const [i,r] of financing.rows.entries()){
 const n=i+77,sourceRow=auditRows.get(r.key);
 repayment.getRange(`A${n}`).values=[[r.label]];
 repayment.getRange(`B${n}`).formulas=[['='+ref(r.key)]];
 repayment.getRange(`C${n}`).formulas=[[`='Data'!E${sourceRow}`]];
 repayment.getRange(`D${n}`).formulas=[[r.coupon!==null?`='Data'!S${sourceRow}`:`="Compounded SOFR + "&TEXT('Data'!T${sourceRow},"0.000%")`]];
 repayment.getRange(`B${n}:D${n}`).format.font.color='#008000';
 if(r.coupon!==null)repayment.getRange(`D${n}`).setNumberFormat('0.000%');
}
repayment.getRange('A85:D89').values=[['Calculated initial issue total',null,'May 20, 2026','Eight series; not additional June debt.'],
 ['Reported completed issue total',null,'May 20, 2026','8-K Item 8.01; face principal differs from net cash proceeds.'],
 ['Issue reconciliation difference',null,'Zero = reconciled','No roll-forward to June outstanding principal.'],
 ['Current outstanding by series','Unavailable','June / October 2026','Initial issue amounts do not establish current balances.'],
 ['Drawable capacity / future coverage','Unavailable','October 15 review','No new verified facility renewal, drawable credit or complete future funding coverage.']];
repayment.getRange('B85').formulas=[['=SUM(B77:B84)']];repayment.getRange('B86').formulas=[['='+ref('may_issue_control')]];repayment.getRange('B86').format.font.color='#008000';repayment.getRange('B87').formulas=[['=B85-B86']];
for(const [n,key] of [[91,'coupon_conflict'],[92,'redemption_detail'],[93,'inventory_detail'],[94,'credit_detail'],[95,'date_detail'],[96,'delisting_detail']]){
 repayment.getRange(`A${n}:D${n}`).merge();repayment.getRange(`A${n}`).values=[[financing[key]]];
}
about.getRange('A9:C10').values=[['Financing inventory','SEC index screened through October 15, 2026. May offering terms added as initial principal; full June debt schedule and drawable capacity remain Unavailable.',financing.inventory.source_url],
 ['Contract evidence','Series rates and maturities come from the final prospectus and certificates, corroborated by the completed offering. An 8-K coupon conflict is flagged; the corroborated 2029 fixed rate is 4.150%.','docs/lly_financing_audit.md']];
main.getRange('A15:D15').values=[['Historical interest coverage',null,date(interestReview.period_end),'Derived operating income / reported interest expense. Annual net of capitalized interest; interim capitalization basis not explicitly stated.']];
main.getRange('B15').formulas=[['=B50']];main.getRange('B15').format.font.color='#000000';main.getRange('B15').setNumberFormat('0.00"x"');main.getRange('C15').setNumberFormat('mmm d, yyyy');
main.getRange('A30').values=[['Historical operating-income interest coverage']];
main.getRange('A31:D31').merge();main.getRange('A31').values=[['TTM July 1, 2025–June 30, 2026. Derived operating income / reported interest expense on borrowings. USD millions unless ratio.']];
main.getRange('A33:D33').values=[['Calculation component','FY2025','+ H1 2026','− H1 2025']];
const operatingLines=[['revenue','Revenue'],['cost_sales','Cost of sales'],['rd','R&D'],['sga','SG&A'],['iprd','Acquired IPR&D, expense'],['special','Impairment, restructuring and special charges']];
for(const [col,role] of [['B','fy'],['C','current'],['D','prior']]){
 for(const [i,[key,label]] of operatingLines.entries()){
  const row=i+34;main.getRange(`A${row}`).values=[[label]];
  main.getRange(`${col}${row}`).formulas=[['='+ref('coverage_'+role+'_'+key)]];main.getRange(`${col}${row}`).format.font.color='#008000';
 }
 main.getRange(`${col}40`).formulas=[[`=${col}34-SUM(${col}35:${col}39)`]];
 main.getRange(`${col}41`).formulas=[['='+ref('coverage_'+role+'_pretax')]];
 main.getRange(`${col}42`).formulas=[['='+ref('coverage_'+role+'_other_income')]];
 main.getRange(`${col}43`).formulas=[[`=${col}41-${col}42`]];
 main.getRange(`${col}44`).formulas=[[`=${col}40-${col}43`]];
 main.getRange(`${col}46`).formulas=[['='+ref('coverage_'+role+'_interest')]];
 for(const row of [41,42,46])main.getRange(`${col}${row}`).format.font.color='#008000';
}
for(const [row,label] of [[40,'Derived operating income'],[41,'Pretax income, reported'],[42,'Nonoperating income (expense), tagged sign'],[43,'Control: pretax − tagged nonoperating'],[44,'Reconciliation difference, zero = matched'],[46,'Reported interest expense on borrowings']])main.getRange(`A${row}`).values=[[label]];
main.getRange('A48:D50').values=[['TTM derived operating income',null,'FY + current H1 − prior H1','Acquired IPR&D and special charges are retained; no adjusted earnings addbacks.'],
 ['TTM reported interest expense',null,'FY + current H1 − prior H1','Annual 895 + H1 2026 677 − H1 2025 493. No capitalized-interest adjustment or interest-income offset.'],
 ['Historical interest coverage',null,'Operating income / interest','Accrual earnings measure. Not cash interest coverage, covenant headroom, drawable credit or a repayment forecast.']];
main.getRange('B48').formulas=[['=B40+C40-D40']];main.getRange('B49').formulas=[['=B46+C46-D46']];
main.getRange('B50').formulas=[['=IF(AND(B44=0,C44=0,D44=0,B49>0),B48/B49,NA())']];
for(const [row,text] of [[52,interestReview.basis],[53,interestReview.limitations],[54,'Operating income is derived, not a reported subtotal. Statement-table selection excludes rounded MD&A repeats. Other–net XBRL values are positive income / negative expense; the control preserves and subtracts that sign.'],[55,'Interest uses the exact six-month single-segment contexts in the quarterly filing; three-month amounts are not added. Source tags, dates, dimensions and selection rules are in Data.']]){
 main.getRange(`A${row}:D${row}`).merge();main.getRange(`A${row}`).values=[[text]];
}
about.getRange('A11:C12').values=[['Historical interest coverage','Derived TTM operating income / reported interest expense. FY + current H1 − prior H1; each operating-income period reconciles to pretax less tagged nonoperating income (expense).','docs/lly_interest_coverage.md'],
 ['Capitalization basis',interestReview.basis,'FY2025 10-K Note 11 p. 77; June 10-Q Note 11 p. 23']];
for(const s of [main,repayment,data,about]){
 s.showGridLines=false;const u=s.getUsedRange();u.format.font.name='Arial';u.format.font.size=10;
 u.format.verticalAlignment='top';u.format.rowHeight=30;u.format.wrapText=true;
}
main.getRange('A2').format.font.bold=true;main.getRange('A2').format.font.size=14;
for(const [col,width] of [['A',42],['B',29],['C',26],['D',73]])main.getRange(`${col}1:${col}26`).format.columnWidth=width;
main.getRange('A6:D15').format.rowHeight=46;main.getRange('A19:C20').format.rowHeight=62;
for(let n=6;n<=14;n++)main.getRange(`A${n}:D${n}`).format.rowHeight=Math.max(46,Math.ceil(String(main.getRange(`D${n}`).values[0][0]).length/73)*14+12);
main.getRange('A3').format.wrapText=false;main.getRange('A24:A26').format.wrapText=false;
for(const a of ['A5:D15','A18:C20'])frame(main,a);
header(main,'A5:D5');header(main,'A18:C18');
for(const n of [7,8,12])subtotal(main,`A${n}:D${n}`);
main.getRange('D6:D14').format.font.bold=false;
const widths=[45,22,20,20,14,20,33,68,20,12,12,75,75,60,90];
widths.forEach((w,i)=>data.getRangeByIndexes(0,i,inputs.length+1,1).format.columnWidth=w);
data.getUsedRange().format.rowHeight=65;data.getRange('A1:O1').format.rowHeight=32;
frame(data,`A1:O${inputs.length+1}`);header(data,'A1:O1');data.freezePanes.freezeRows(1);
frame(data,`A${disclosureHeader}:I${disclosureHeader+2}`);header(data,`A${disclosureHeader}:I${disclosureHeader}`);
data.getRange(`A${disclosureHeader}:I${disclosureHeader+2}`).format.rowHeight=80;
for(const col of ['C','E'])data.getRange(`${col}${disclosureHeader+1}:${col}${disclosureHeader+2}`).setNumberFormat('mmm d, yyyy');
about.getRange('A1:A6').format.columnWidth=28;about.getRange('B1:B6').format.columnWidth=100;about.getRange('C1:C6').format.columnWidth=75;
about.getUsedRange().format.rowHeight=70;about.getRange('A2:C2').format.rowHeight=100;about.getRange('A1:C1').format.rowHeight=30;frame(about,'A1:C6');header(about,'A1:C1');
// Apply the existing restrained borders and input/formula colors to the new blocks.
repayment.getRange('A2').format.font.size=14;repayment.getRange('A2').format.font.bold=true;
repayment.getRange('A3').format.wrapText=false;repayment.getRange('A4:D4').format.rowHeight=43;
for(const [col,width] of [['A',46],['B',23],['C',34],['D',99]])repayment.getRange(`${col}1:${col}71`).format.columnWidth=width;
repayment.getRange('E1:E71').format.columnWidth=3;
repayment.getRange('F1:P71').format.columnWidth=11;
for(const a of ['A6:D26','A29:D35','A38:D46','A48:D50','A53:D68','A70:D71'])frame(repayment,a);
for(const a of ['A6:D6','A29:D29','A38:D38','A53:D53'])header(repayment,a);
for(const n of [19,20,22,23,24,25,26,63,66,68])subtotal(repayment,`A${n}:D${n}`);
repayment.getRange('B7:B68').setNumberFormat(USD);repayment.getRange('G28:G33').setNumberFormat(USD);
repayment.getRange('A7:D26').format.rowHeight=43;
repayment.getRange('A30:D35').format.rowHeight=70;
repayment.getRange('A39:D46').format.rowHeight=96;
repayment.getRange('A48:D50').format.rowHeight=68;
repayment.getRange('A54:D68').format.rowHeight=43;
repayment.getRange('A70:D71').format.rowHeight=80;
repayment.freezePanes.freezeRows(6);
frame(data,`A${auditHeader}:R${auditHeader+records.length}`);header(data,`A${auditHeader}:R${auditHeader}`);
data.getRange(`A${auditHeader}:R${auditHeader+records.length}`).format.rowHeight=85;
data.getRange(`B${auditHeader+1}:B${auditHeader+records.length}`).format.font.color='#0000FF';
data.getRange(`B${auditHeader+1}:B${auditHeader+records.length}`).setNumberFormat(USD);
for(const col of ['D','E','G'])data.getRange(`${col}${auditHeader+1}:${col}${auditHeader+records.length}`).setNumberFormat('mmm d, yyyy');
for(const [col,width] of [['I',68],['P',85],['Q',100],['R',72]])data.getRange(`${col}1:${col}${auditHeader+records.length}`).format.columnWidth=width;
about.getRange('A7:C8').format.rowHeight=95;frame(about,'A1:C8');
repayment.getRange('A74').format.font.bold=true;
repayment.getRange('A75:D75').format.rowHeight=43;
frame(repayment,'A76:D89');header(repayment,'A76:D76');repayment.getRange('A76:D89').format.rowHeight=43;
repayment.getRange('B77:B87').setNumberFormat(USD);repayment.getRange('C77:C84').setNumberFormat('mmm d, yyyy');
for(const n of [85,87])subtotal(repayment,`A${n}:D${n}`);
repayment.getRange('A91:D96').format.rowHeight=70;
data.getRange(`S${auditHeader}:T${auditHeader+records.length}`).format.rowHeight=85;
data.getRange(`S${auditHeader}:T${auditHeader+records.length}`).format.columnWidth=23;
data.getRange(`S${auditHeader+1}:T${auditHeader+records.length}`).setNumberFormat('0.000%');
data.getRange(`S${auditHeader+1}:T${auditHeader+records.length}`).format.font.color='#0000FF';
frame(data,`S${auditHeader}:T${auditHeader+records.length}`);header(data,`S${auditHeader}:T${auditHeader}`);
about.getRange('A9:C10').format.rowHeight=85;frame(about,'A1:C10');
main.getRange('A30').format.font.bold=true;main.getRange('A30').format.font.size=13;
main.getRange('A31:D31').format.rowHeight=36;main.getRange('A33:D50').format.rowHeight=44;
main.getRange('B34:D49').setNumberFormat(USD);main.getRange('B50').setNumberFormat('0.00"x"');
for(const a of ['A33:D44','A46:D46','A48:D50'])frame(main,a);header(main,'A33:D33');
for(const n of [40,44,48,49,50])subtotal(main,`A${n}:D${n}`);
main.getRange('A52:D55').format.rowHeight=65;main.getRange('A15:D15').format.rowHeight=65;
about.getRange('A11:C12').format.rowHeight=100;frame(about,'A1:C12');
const ratioManifest=await finishRatioSheet(wb,root,'LLY',ratios);
wb.recalculate();
for(const [cell,value] of [['B40',ic.periods.fy.operating_income],['C40',ic.periods.current.operating_income],['D40',ic.periods.prior.operating_income],['B44',0],['C44',0],['D44',0],['B48',ic.operating_income],['B49',ic.interest],['B50',ic.value],['B15',ic.value]])if(main.getRange(cell).values[0][0]!==value)throw new Error('Coverage reconciliation failed '+cell);
const interestCells=['fy','current','prior'].map(role=>data.getRange(`B${auditRows.get('coverage_'+role+'_interest')}`)),savedInterest=interestCells.map(cell=>cell.values);
interestCells[0].values=[[null]];wb.recalculate();if(typeof main.getRange('B50').values[0][0]==='number')throw new Error('Missing interest became a ratio');
for(const cell of interestCells)cell.values=[[0]];wb.recalculate();if(typeof main.getRange('B50').values[0][0]==='number')throw new Error('Zero interest became a ratio');
interestCells.forEach((cell,i)=>cell.values=savedInterest[i]);wb.recalculate();
const revenueCheck=data.getRange(`B${auditRows.get('coverage_fy_revenue')}`),savedRevenue=revenueCheck.values;revenueCheck.values=[[savedRevenue[0][0]+1000000]];wb.recalculate();if(typeof main.getRange('B50').values[0][0]==='number')throw new Error('Unreconciled operating income became coverage');revenueCheck.values=savedRevenue;wb.recalculate();
if(repayment.getRange('B85').values[0][0]!==financing.reported_issue_total||repayment.getRange('B87').values[0][0]!==0)throw new Error('May issue does not reconcile');
if(repayment.getRange('D79').values[0][0]!==0.0415||repayment.getRange('D77').values[0][0]!=='Compounded SOFR + 0.350%')throw new Error('Contract rates do not match');
const firstPrincipal=data.getRange(`B${auditRows.get('may_notes_0')}`),savedPrincipal=firstPrincipal.values;
firstPrincipal.values=[[null]];wb.recalculate();if(typeof repayment.getRange('B85').values[0][0]==='number')throw new Error('Missing issue principal became zero');firstPrincipal.values=savedPrincipal;wb.recalculate();
for(const [cell,expected] of [['B22',0],['B23',review.cash.ocf_less_capex],['B24',review.cash.net_borrowing],['B25',review.cash.acquisitions_iprd],['B26',review.cash.payouts],['B48',2518000000],['B63',review.notes_schedule.total_notes],['B68',0]])if(repayment.getRange(cell).values[0][0]!==expected)throw new Error('Review formula mismatch '+cell);
const testCell=data.getRange(`B${auditRows.get('ocf')}`),saved=testCell.values;testCell.values=[[null]];wb.recalculate();
if(typeof repayment.getRange('B23').values[0][0]==='number')throw new Error('Missing OCF became zero');testCell.values=saved;wb.recalculate();
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:20},summary:'Final formula scan'})).ndjson);
for(const [i,key] of order.entries())if(main.getRange(`B${i+6}`).values[0][0]!==m[key].value)throw new Error('LLY value mismatch '+key);
// A missing source must remain unavailable, including in linked calculations.
const cashCell=data.getRange('B2'),original=cashCell.values;cashCell.values=[[null]];wb.recalculate();
if(typeof main.getRange('B8').values[0][0]==='number')throw new Error('Missing cash became zero');
cashCell.values=original;wb.recalculate();
documentationLinks(about);
const fundingManifest=await finishFundingSheet(wb,root,'LLY',funding);
Object.assign(fundingManifest,await finishBorrowingLeaseSheet(wb,root,'LLY',borrowingLeases));
Object.assign(fundingManifest,ratioManifest);
Object.assign(fundingManifest,await finishHistorySheet(wb,root,'LLY',history));
Object.assign(fundingManifest,await finishCoreChartSheet(wb,root,'LLY',coreCharts));
const out=path.join(root,'samples/lly_liquidity.xlsx');await(await SpreadsheetFile.exportXlsx(wb)).save(out);
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.writeFile(out.replace('.xlsx','.manifest.json'),JSON.stringify({...fundingManifest,sources:{'liquidity_pilots.json':digest(source),'lly_liquidity.json':digest(reviewBytes),'lly_financing.json':digest(financingBytes),'lly_interest.json':digest(interestBytes)},workbook_sha256:digest(await fs.readFile(out))},null,2)+'\n');
if(process.env.SKIP_UNCHANGED_RENDERS!=='1') for(const [sheet,range,file] of [['Debt and liquidity','A2:D15','review'],['Debt and liquidity','A17:D26','obligations'],['Data','A1:G6','inputs'],['Data','H1:O6','provenance'],['Data',`A${disclosureHeader}:I${disclosureHeader+2}`,'disclosures'],['About','A1:C12','about'],['Repayment review','A2:D26','cash-build'],['Repayment review','F6:P24','cash-chart'],['Repayment review','A29:D35','facilities'],['Repayment review','A38:D50','commitments'],['Repayment review','A53:D71','notes'],['Data',`A${auditHeader}:H${auditHeader+6}`,'review-inputs'],['Data',`I${auditHeader}:L${auditHeader+6}`,'review-contexts'],['Data',`M${auditHeader}:R${auditHeader+6}`,'review-provenance'],['Repayment review','A74:D89','may-maturities'],['Repayment review','A91:D96','financing-limits'],['Data',`A${auditRows.get('may_notes_0')}:H${auditRows.get('may_issue_control')}`,'contract-inputs'],['Data',`M${auditRows.get('may_notes_0')}:T${auditRows.get('may_issue_control')}`,'contract-provenance'],['Debt and liquidity','A30:D50','coverage-build'],['Debt and liquidity','A52:D55','coverage-basis'],['Data',`A${auditRows.get('coverage_fy_revenue')}:H${auditRows.get('coverage_fy_interest')}`,'coverage-inputs'],['Data',`I${auditRows.get('coverage_current_interest')}:Q${auditRows.get('coverage_prior_interest')}`,'coverage-contexts']]){
 const img=await wb.render({sheetName:sheet,range,scale:1.1,format:'png'});await fs.writeFile(`lly-${file}.png`,new Uint8Array(await img.arrayBuffer()));
}
await fs.rm(out+'.inspect.ndjson',{force:true});
console.log('Lilly: all nine metrics reconcile; source and missing-value checks passed.');
