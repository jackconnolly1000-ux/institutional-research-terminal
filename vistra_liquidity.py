"""Vistra's dated cash and repayment evidence. No forecasts, network calls or credit ratings.

Dimensions are accepted only through this filing-specific map. Facility availability is a
reported June 30 amount, never a promise that a later drawing or parent distribution can occur.
"""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx
import vistra_interest
from reviewed_financing import BASE, VST
from vistra_liquidity_sources import PAYMENTS, RESOURCES, TERMS, LIMITS

SAMPLE = Path(__file__).parent / 'samples/vistra_liquidity.json'
WORKBOOK = SAMPLE.with_suffix('.xlsx')
END, START = '2026-06-30', '2026-01-01'
PERIODS = {
    'quarter': {'accession':'0001692819-26-000019', 'form':'10-Q', 'filed':'2026-08-10',
                'end':END, 'document':'vistra-20260630.htm'},
    'annual': {'accession':'0001692819-26-000006', 'form':'10-K', 'filed':'2026-02-27',
               'end':'2025-12-31', 'document':'vistra-20251231.htm'},
}
for p in PERIODS.values():
    p['source_url'] = BASE + p['accession'].replace('-', '') + '/' + p['document']

FLOWS = {
    'ocf': ('Operating cash flow','us-gaap:NetCashProvidedByUsedInOperatingActivities',1),
    'capex': ('Capital spending, including nuclear fuel and LTSA prepayments','us-gaap:PaymentsToAcquirePropertyPlantAndEquipment',-1),
    'acquisition_adjustment': ('Lotus purchase-price adjustment','us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired',-1),
    'trust_sales': ('Sales of nuclear decommissioning trust securities','us-gaap:ProceedsFromDecommissioningFund',1),
    'trust_purchases': ('Purchases of nuclear decommissioning trust securities','us-gaap:PaymentsToInvestInDecommissioningFund',-1),
    'allowance_sales': ('Environmental allowance sales','us-gaap:ProceedsFromSaleOfIntangibleAssets',1),
    'allowance_purchases': ('Environmental allowance purchases','us-gaap:PaymentsToAcquireIntangibleAssets',-1),
    'insurance': ('Insurance recovery of damaged property','us-gaap:ProceedsFromInsuranceSettlementInvestingActivities',1),
    'asset_sales': ('Sales of property and nuclear fuel','us-gaap:ProceedsFromSaleOfOtherProductiveAssets',1),
    'other_investing': ('Other investing cash flow','us-gaap:PaymentsForProceedsFromOtherInvestingActivities',-1),
    'investing': ('Reported net investing cash flow','us-gaap:NetCashProvidedByUsedInInvestingActivities',1),
    'debt_issued': ('Debt issuance cash proceeds','us-gaap:ProceedsFromIssuanceOfDebt',1),
    'debt_repaid': ('Debt repayments and repurchases','us-gaap:RepaymentsOfLongTermDebt',-1),
    'receivables_net': ('Receivables financing, net repayments','vistra:ProceedsFromRepaymentsOfAccountsReceivableFinancing',1),
    'revolver_draws': ('Revolver borrowings','us-gaap:ProceedsFromLinesOfCredit',1),
    'revolver_repaid': ('Revolver repayments','us-gaap:RepaymentsOfLinesOfCredit',-1),
    'commodity_draws': ('Commodity-linked borrowings','us-gaap:ProceedsFromShortTermDebt',1),
    'commodity_repaid': ('Commodity-linked repayments','us-gaap:RepaymentsOfShortTermDebt',-1),
    'fees': ('Debt issuance costs paid','us-gaap:PaymentsOfFinancingCosts',-1),
    'buybacks': ('Stock repurchases','us-gaap:PaymentsForRepurchaseOfCommonStock',-1),
    'common_dividends': ('Common dividends paid','us-gaap:PaymentsOfDividendsCommonStock',-1),
    'preferred_dividends': ('Preferred dividends paid','us-gaap:PaymentsOfDividendsPreferredStockAndPreferenceStock',-1),
    'withholding': ('Share compensation tax withholding','us-gaap:PaymentsRelatedToTaxWithholdingForShareBasedCompensation',-1),
    'nuveen_principal_paid': ('Nuveen principal paid','vistra:RedeemableNoncontrollingInterestPrincipalPayment',-1),
    'other_financing': ('Other financing cash flow','us-gaap:ProceedsFromPaymentsForOtherFinancingActivities',1),
    'financing': ('Reported net financing cash flow','us-gaap:NetCashProvidedByUsedInFinancingActivities',1),
    'change': ('Reported cash change including restricted cash','us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',1),
}
INVESTING = ['capex','acquisition_adjustment','trust_sales','trust_purchases','allowance_sales',
             'allowance_purchases','insurance','asset_sales','other_investing']
FINANCING = [k for k in FLOWS if k not in ['ocf',*INVESTING,'investing','financing','change']]
INSTANTS = {
    'opening_total': ('Opening cash including restricted cash','us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents','2025-12-31'),
    'closing_total': ('Ending cash including restricted cash','us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',END),
    'cash': ('Cash and equivalents excluding restricted cash','us-gaap:CashAndCashEquivalentsAtCarryingValue',END),
    'restricted_current': ('Current restricted cash','us-gaap:RestrictedCashCurrent',END),
    'restricted_noncurrent': ('Noncurrent restricted cash','us-gaap:RestrictedCashNoncurrent',END),
    'nuveen_carrying': ('Nuveen obligation carrying amount','vistra:ForwardRepurchaseObligationToBePaidCurrent',END),
    'lt_carrying': ('Long-term debt including current portion','us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities',END),
    'debt_costs': ('Unamortized debt premiums, discounts and costs','us-gaap:DebtInstrumentUnamortizedDiscountPremiumAndDebtIssuanceCostsNet',END),
    'receivables': ('Receivables financing outstanding','vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed',END),
    'shortterm': ('Short-term borrowings, reported zero','us-gaap:ShortTermBorrowings',END),
    'margin_cash': ('Posted margin deposits','us-gaap:MarginDepositAssets',END),
    'affiliate_margin': ('Affiliate-financed eligible assets posted','vistra:MarginDepositsPostedUnderAffiliateFinancingAgreementAsset',END),
}
TYPE, INSTRUMENT = 'us-gaap:LongtermDebtTypeAxis','us-gaap:DebtInstrumentAxis'
def dims(kind, member):
    return [(TYPE,kind),(INSTRUMENT,member)]

REVOLVER = dims('us-gaap:LineOfCreditMember','vistra:SeniorSecuredRevolvingCreditFacilityMember')
COMMODITY = dims('us-gaap:RevolvingCreditFacilityMember','vistra:SeniorSecuredCommodityLinkedRevolvingCreditFacilityMember')
PROJECT = [(TYPE,'vistra:ProjectLevelDebtMember')]
BCOP = dims('us-gaap:BridgeLoanMember','vistra:BCOPCreditFacilitiesMember')
CONSTRUCTION = dims('vistra:ConstructionAndTermLoansMember','vistra:BCOPCreditFacilitiesMember')
ZERO = dims('us-gaap:RevolvingCreditFacilityMember','vistra:VistraZeroTermLoanBFacilityMember')
TXEF = dims('us-gaap:RevolvingCreditFacilityMember','vistra:TexasEnergyFundLoanMember')
DIMENSIONED = {
    'project_debt': ('Project debt principal','us-gaap:DebtInstrumentCarryingAmount',PROJECT),
    'operations_debt': ('Vistra Operations debt principal','us-gaap:DebtInstrumentCarryingAmount',[(TYPE,'vistra:VistraOperationsDebtMember')]),
    'bridge': ('Pulaski bridge loan','vistra:LineOfCreditFacilityBorrowingsOutstanding',BCOP),
    'construction_total': ('BCOP construction and term loans','vistra:LineOfCreditFacilityBorrowingsOutstanding',CONSTRUCTION),
    'pulaski_construction': ('Pulaski construction loan','us-gaap:DebtInstrumentFaceAmount',dims('us-gaap:ConstructionLoansMember','vistra:PulaskiMember')),
    # The same 206M combined balance is tagged against each of three projects in the prose.
    # Select the checked Coffeen context once; never add its Oak Hill and Baldwin duplicates.
    'bcop_term': ('BCOP combined term loans','us-gaap:DebtInstrumentFaceAmount',dims('us-gaap:ConstructionLoansMember','vistra:CoffeenTermLoanMember')),
    'zero_debt': ('Vistra Zero term loan','vistra:LineOfCreditFacilityBorrowingsOutstanding',ZERO),
    'txef_debt': ('Texas Energy Fund drawn loan','vistra:LineOfCreditFacilityBorrowingsOutstanding',TXEF),
    'nuveen_payment': ('Nuveen final principal and interest payment','vistra:RedeemableNoncontrollingInterestToBePaidYearOne',[('srt:OwnershipAxis','vistra:VistraVisionMember')]),
    'notes_2026': ('5.050% senior notes','us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities',dims('vistra:VistraOperationsSeniorNotesMember','vistra:A5.050SeniorNotesDue2026Member')),
    'notes_jan2027': ('3.700% senior notes','us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities',dims('vistra:VistraOperationsSeniorNotesMember','vistra:A3.700SeniorNotesDue2027Member')),
    'notes_jul2027': ('5.000% senior notes','us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities',dims('vistra:VistraOperationsSeniorNotesMember','vistra:A5.000SeniorNotesDue2027Member')),
    'loc_other': ('Other LOC facilities outstanding','us-gaap:LettersOfCreditOutstandingAmount',[(TYPE,'us-gaap:LetterOfCreditMember'),(INSTRUMENT,'vistra:SecuredLetterOfCreditFacilitiesMember'),('dei:LegalEntityAxis','vistra:VistraOperationsCompanyLLCMember')]),
    'loc_alternative': ('Alternative LOC facilities outstanding','us-gaap:LettersOfCreditOutstandingAmount',[('us-gaap:CreditFacilityAxis','us-gaap:LetterOfCreditMember'),(INSTRUMENT,'vistra:AlternateLetterOfCreditFacilityMember')]),
    'loc_total': ('Reported letters of credit total','us-gaap:LettersOfCreditOutstandingAmount',[('us-gaap:GuaranteeObligationsByNatureAxis','us-gaap:FinancialStandbyLetterOfCreditMember'),('dei:LegalEntityAxis','vistra:VistraOperationsCompanyLLCMember')]),
}
for facility, ds in [('revolver',REVOLVER),('commodity',COMMODITY)]:
    for field,tag in [('limit','us-gaap:LineOfCreditFacilityMaximumBorrowingCapacity'),
                      ('drawn','vistra:LineOfCreditFacilityBorrowingsOutstanding'),
                      ('lc','vistra:LineOfCreditFacilityLettersOfCreditOutstanding'),
                      ('available','us-gaap:LineOfCreditFacilityRemainingBorrowingCapacity')]:
        DIMENSIONED[facility+'_'+field] = (facility.title()+' '+field,tag,ds)
for key,ds in [('bcop',[(INSTRUMENT,'vistra:BCOPCreditFacilitiesMember')]),('zero',ZERO),('txef',TXEF)]:
    DIMENSIONED[key+'_available'] = (key.upper()+' reported unused capacity','us-gaap:LineOfCreditFacilityRemainingBorrowingCapacity',ds)

ANNUAL_TAGS = ['LongTermDebtMaturitiesRepaymentsOfPrincipal'+s for s in
              ['InNextTwelveMonths','InYearTwo','InYearThree','InYearFour','InYearFive','AfterYearFive']]


def build(quarter: Path, annual: Path) -> dict:
    """Derive results only after each independent source group reconciles."""
    out = {'ticker':'VST','accession':PERIODS['quarter']['accession'],'period_start':START,
           'period_end':END,'checked_as_of':'2026-10-15','status':'Unavailable','detail':'',
           'inputs':{},'cash':None,'capacity':None,'debt':None,'annual':None}
    docs = {'quarter':quarter,'annual':annual}
    contexts = {}
    try:
        for key,path in docs.items(): contexts[key] = fx._contexts(ET.parse(path).getroot())
    except (OSError,ET.ParseError) as exc:
        out['detail'] = f'Saved filing could not be read: {type(exc).__name__}.'
        return out

    def read(key,label,tag,*,period='quarter',instant=None,start=None,dimensions=(),location=None):
        p = PERIODS[period]
        fact = (fx.read_duration(docs[period],p['accession'],tag,start,instant or p['end'],dimensions=dimensions)
                if start else fx.read_instant(docs[period],p['accession'],tag,instant or p['end'],dimensions=dimensions))
        if fact['value'] is not None and (contexts[period][fact['context_id']]['entity_identifier'] or '').lstrip('0') != '1692819':
            fact.update(value=None,note='Unavailable',detail='Selected context does not identify Vistra CIK 1692819.')
        fact.update(label=label,period_start=start,period_end=instant or p['end'],form=p['form'],
                    filed=p['filed'],document=p['document'],source_url=p['source_url'],
                    location=location or ('10-Q cash flows, pp. 4–5' if start else '10-Q Note 12, pp. 20–28'))
        out['inputs'][key] = fact

    for k,(label,tag,_) in FLOWS.items(): read(k,label,tag,start=START)
    for k,(label,tag,end) in INSTANTS.items(): read(k,label,tag,instant=end,location='10-Q balance sheet p. 2; cash flows p. 5; Note 12')
    for k,(label,tag,ds) in DIMENSIONED.items(): read(k,label,tag,dimensions=ds)
    for key,tag in [('helix_initial','vistra:InvestmentCompanyInitialCommitmentCapital'),
                    ('helix_additional','vistra:InvestmentCompanyAdditionalCommitmentCapital')]:
        read(key,key.replace('_',' ').title(),tag,start='2026-06-01',location='10-Q Note 7 p. 15; MD&A p. 69')
    read('cogentrix','Expected Cogentrix cash consideration','us-gaap:BusinessCombinationConsiderationTransferred1',
         start='2025-12-31',instant='2025-12-31',dimensions=[('us-gaap:BusinessAcquisitionAxis','vistra:CogentrixEnergyMember')],location='10-Q Note 3 p. 9; expected closing late 2026')
    for i,tag in enumerate(ANNUAL_TAGS):
        read('annual_'+str(i),str(2026+i) if i<5 else 'Thereafter','us-gaap:'+tag,period='annual',location='10-K Note 13, long-term debt maturities, pp. 114–115')
    read('annual_carrying','Annual long-term debt carrying amount','us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities',period='annual',location='10-K Note 13, pp. 114–115')
    read('annual_costs','Annual debt premiums, discounts and costs',INSTANTS['debt_costs'][1],period='annual',location='10-K Note 13, pp. 114–115')
    v = {k:f['value'] for k,f in out['inputs'].items()}
    def complete(keys): return all(v[k] is not None for k in keys)
    cashkeys = [*FLOWS,'opening_total','closing_total','cash','restricted_current','restricted_noncurrent']
    if complete(cashkeys):
        signed = lambda k: v[k]*FLOWS[k][2]
        invest = sum(signed(k) for k in INVESTING)
        finance = sum(signed(k) for k in FINANCING)
        if (invest==v['investing'] and finance==v['financing'] and v['ocf']+invest+finance==v['change']
                and v['opening_total']+v['change']==v['closing_total']
                and v['cash']+v['restricted_current']+v['restricted_noncurrent']==v['closing_total']
                and all(v[k]>=0 for k in ['capex','debt_issued','debt_repaid','buybacks','cash','restricted_current','restricted_noncurrent'])):
            out['cash'] = {'fcf':v['ocf']-v['capex'], 'distributions':v['buybacks']+v['common_dividends']+v['preferred_dividends'],
                'net_debt_cash':v['debt_issued']-v['debt_repaid']+v['receivables_net']+v['revolver_draws']-v['revolver_repaid']+v['commodity_draws']-v['commodity_repaid'],
                'other_investing':invest+v['capex'],'restricted':v['restricted_current']+v['restricted_noncurrent']}
            out['status']='Checked'
        else: out['detail']='Cash uses, investing, financing and restricted-cash balances do not reconcile.'
    else: out['detail']='Cash inputs Unavailable: '+', '.join(k for k in cashkeys if v[k] is None)
    capacitykeys = [k for k in v if k.startswith(('revolver_','commodity_')) and k not in FLOWS]+['loc_other','loc_alternative','loc_total','cash']
    if complete(capacitykeys) and all(v[k]>=0 for k in capacitykeys):
        if (v['revolver_limit']-v['revolver_drawn']-v['revolver_lc']==v['revolver_available']
                and v['commodity_available']<=v['commodity_limit']-v['commodity_drawn']-v['commodity_lc']
                and v['revolver_lc']+v['loc_other']+v['loc_alternative']==v['loc_total']):
            out['capacity']={'reported_liquidity':v['cash']+v['revolver_available']+v['commodity_available'],
                             'later_drawable':None,'covenant_headroom':None}
    debtkeys=['project_debt','operations_debt','lt_carrying','debt_costs','bridge','construction_total','zero_debt','txef_debt','bcop_term','pulaski_construction','receivables','shortterm']
    if complete(debtkeys) and all(v[k]>=0 for k in debtkeys) and v['project_debt']==sum(v[k] for k in ['bridge','construction_total','zero_debt','txef_debt']) \
            and v['construction_total']==v['bcop_term']+v['pulaski_construction'] \
            and v['project_debt']+v['operations_debt']-v['debt_costs']==v['lt_carrying']:
        out['debt']={'principal':v['project_debt']+v['operations_debt'],'baseline':v['lt_carrying']+v['receivables']+v['shortterm']}
    annualkeys=['annual_'+str(i) for i in range(6)]+['annual_costs','annual_carrying']
    if complete(annualkeys) and sum(v['annual_'+str(i)] for i in range(6))-v['annual_costs']==v['annual_carrying']:
        out['annual']={'principal':sum(v['annual_'+str(i)] for i in range(6)),
                       'detail':'December 31, 2025 schedule only. April refinancing and later borrowing prevent using it as the remaining June schedule.'}
    out['payments'] = [dict(key=k,label=label,due_start=a,due_end=b,detail=detail,
                            value=v[k],source_url=PERIODS['quarter']['source_url'])
                       for k,label,a,b,detail in PAYMENTS]
    out['resources'] = [dict(key=k,label=label,borrower=borrower,input_key=inp,
                             available=v.get(inp),as_of=END,later_available=None,detail=detail)
                        for k,label,borrower,inp,detail in RESOURCES]
    out['terms'], out['limits'] = TERMS, LIMITS
    out['events'] = [{**row,'accession':acc,'related':[list(pair) for pair in row['related']]}
                     for acc,row in VST.items()]
    out['inventory'] = {'checked_as_of':'2026-10-15', 'since':END,
                        'detail':'SEC submissions index checked October 15, 2026. Ten candidate financing documents since June 30; six 8-Ks plus four offering documents. Main documents and relevant exhibits reviewed. No later financing candidate appeared in that retrieved index. New or mismatched filings remain Not checked.'}
    return out


def for_snapshot(snapshot):
    anchor=snapshot.get('metrics',{}).get('cash',{})
    if (snapshot.get('ticker'),anchor.get('accession'),anchor.get('period_end')) != ('VST',PERIODS['quarter']['accession'],END):
        return None
    try:
        review=json.loads(SAMPLE.read_text(encoding='utf-8'))
        if (review['ticker'],review['accession'],review['period_start'],review['period_end'],review['inputs']['cash']['value']) != ('VST',PERIODS['quarter']['accession'],START,END,anchor.get('value')):
            raise ValueError('Snapshot mismatch')
        return review
    except (OSError,ValueError,KeyError,TypeError):
        return {'status':'Unavailable','detail':'The saved Vistra review is missing or does not match this filing.'}


def workbook_bytes(review):
    try:
        content=WORKBOOK.read_bytes()
        m=json.loads(WORKBOOK.with_suffix('.manifest.json').read_text())
        import borrowing_leases
        if m.get('borrowing_leases_sha256') != borrowing_leases.fingerprint():
            return None
        import funding_conclusions as funding
        if m.get('funding_sha256') != funding.fingerprint() or funding.load('VST') is None:
            return None
        if (review.get('status')=='Checked' and m['review_sha256']==hashlib.sha256(SAMPLE.read_bytes()).hexdigest()
                and m['workbook_sha256']==hashlib.sha256(content).hexdigest()
                and m['interest_sha256']==hashlib.sha256(vistra_interest.SAMPLE.read_bytes()).hexdigest()
                and vistra_interest.load() is not None):
            return content
    except (OSError,ValueError,KeyError): pass
    return None
