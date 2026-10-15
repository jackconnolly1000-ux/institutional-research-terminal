"""Manually read dates and contract terms, separate from extracted monetary facts."""
from reviewed_financing import BASE

Q = BASE+'000169281926000019/vistra-20260630.htm'
K = BASE+'000169281926000006/vistra-20251231.htm'
REV = BASE+'000114036126026944/ef20077059_ex10-1.htm'
COM = BASE+'000114036126038468/ef20083016_ex10-1.htm'
AR = BASE+'000114036126028619/ef20077984_ex4-1.htm'
REPO = BASE+'000114036126028619/ef20077984_ex10-1.htm'

PAYMENTS = [
    ('bridge','Pulaski bridge loan','2026-12-03','2026-12-03','Principal balance; Vistra guarantees repayment. Expected investment tax credits are not cash already available.'),
    ('pulaski_construction','Pulaski construction loan','2026-12-01','2026-12-31','Outstanding construction balance matures in December. Conversion to a term loan requires commercial operation and other conditions; completion is not assumed.'),
    ('notes_2026','5.050% senior notes','2026-12-30','2026-12-30','Vistra Operations principal; coupon interest is additional.'),
    ('nuveen_payment','Nuveen final payment','2026-12-31','2026-12-31','Principal and interest combined. The 613M carrying liability is the same obligation, not an additional payment.'),
    ('notes_jan2027','3.700% senior notes','2027-01-30','2027-01-30','Vistra Operations principal; coupon interest is additional.'),
    ('notes_jul2027','5.000% senior notes','2027-07-31','2027-07-31','Vistra Operations principal; coupon interest is additional.'),
]
RESOURCES = [
    ('cash','Cash and equivalents','Vistra consolidated','cash','Cash excludes 46M restricted cash. Cash located at Parent and amounts transferable from each subsidiary are Unavailable.'),
    ('revolver','Corporate revolver','Vistra Operations','revolver_available','General corporate purposes, including permitted acquisitions and restricted payments (§9.13). Borrowing conditions and distribution restrictions still apply.'),
    ('commodity','Commodity-linked facility','Vistra Operations','commodity_available','Supports commodity collateral, working capital and general corporate purposes. Weekly hedge-based borrowing base can fall and require repayment. June capacity is not a later commitment to lend that amount.'),
    ('receivables','Receivables facility','TXU Energy Receivables Company','none','Purchase limit rose to 1.25B on July 10, due July 9, 2027. June borrowings 300M. Eligible receivables, advance conditions and a contemporaneous drawing balance are needed; 1.25B less June borrowings is not drawable capacity.'),
    ('repo','Repurchase facility','TXU Energy and originators','none','125M uncommitted program, extended to July 9, 2027. Secured by the receivables program’s subordinated note. June drawings were zero; no guaranteed cash availability or independent collateral pool is established.'),
    ('bcop','BCOP facilities','BCOP project subsidiaries','bcop_available','Zero unused capacity in the June table. Project assets and cash flows service project debt; Pulaski bridge has a Vistra guarantee. The rest is otherwise non-recourse to Vistra Operations and its other subsidiaries.'),
    ('zero','Vistra Zero term loan','Vistra Zero Operating','zero_available','Zero unused capacity in the June table; 697M is already drawn and included in debt. Subsidiary guarantees and project security; otherwise non-recourse to Vistra Operations and its other subsidiaries.'),
    ('txef','Texas Energy Fund loan','Permian Power','txef_available','June table shows 172M drawn and zero unused capacity. The broader 583M development agreement does not establish freely drawable funds. Project use, security and conditions apply; otherwise non-recourse to Vistra Operations and its other subsidiaries.'),
]
TERMS = [
    {'name':'Corporate revolver draw conditions','source_url':REV,'accession':'0001140361-26-026944','filed':'2026-06-30','event_date':'2026-06-24','location':'Ex.10.1, clean agreement Annex B §§7.1–7.2, 9.13, 10.9; Compliance Period definition',
     'detail':'Each drawing requires no continuing default, specified representations to remain true and a borrowing notice. The springing covenant caps contract-defined total net leverage at 5.50x during a Compliance Period. The trigger exceeds 35% of revolving commitments, with specified LC exclusions including undrawn LCs. Ordinary undrawn LCs reduce availability but are not automatically covenant-trigger usage. Covenant headroom is Unavailable.'},
    {'name':'Commodity-linked borrowing conditions','source_url':COM,'accession':'0001140361-26-038468','filed':'2026-10-05','event_date':'2026-09-30','location':'Ex.10.1, §1.1 definitions, §§2.1, 5.2, 7.1–7.2, 10.9; amendment commitment schedule',
     'detail':'September amendment retains 1.75B commitments and extends maturity to September 29, 2027. Draws remain subject to the borrowing base, no default, representations and notice. The agreement has a springing contract-defined 5.50x total net leverage covenant for a Compliance Quarter. Current borrowing base, drawings and headroom are Unavailable; June availability is not rolled forward.'},
    {'name':'Receivables and repurchase renewals','source_url':AR,'accession':'0001140361-26-028619','filed':'2026-07-16','event_date':'2026-07-10','location':'Ex.4.1 §§2.1–2.5 and Schedule VI; Ex.10.1 §2; 10-Q Note 12 p.27',
     'detail':'Receivables amendment extends termination to July 9, 2027 and its purchaser schedule totals 1.25B. RecCo funds purchased eligible receivables under conditions. The separate repo remains uncommitted and uses the subordinated note from that same receivables structure. Capacity and term extensions are not cash receipts.'},
    {'name':'Project repayment and recourse','source_url':Q,'accession':'0001692819-26-000019','filed':'2026-08-10','event_date':'2026-06-30','location':'10-Q Note 12 pp.24–25',
     'detail':'BCOP term loans amortize over 20 years from conversion using project cash flows. Pulaski construction conversion requires commercial operation and other conditions; the 206M combined term balance has a December 2029 final maturity, not a single 206M balloon established here. Vistra guarantees the 261M bridge. Vistra Zero and Permian obligations have separate security and recourse terms. Project cash available for parent obligations is Unavailable.'},
    {'name':'Parent distributions','source_url':K,'accession':'0001692819-26-000006','filed':'2026-02-27','event_date':'2025-12-31','location':'10-K Note 13 p.116; Schedule I pp.159–160; 10-Q Note 12 p.23',
     'detail':'At December 31, 2025 the annual filing said Vistra Operations restricted net assets could be distributed to Parent, and reported 1.625B of subsidiary dividends received during 2025. That does not locate June cash or establish a future parent distribution. The June filing describes investment and dividend restrictions that can apply following a downgrade below investment grade. No future transfer amount is assumed.'},
]
LIMITS = [
    'June 30 is the cash and availability date. Current cash, drawable capacity, parent-accessible cash and contractual covenant headroom are Unavailable.',
    'Operating cash flow is seasonal and weighted toward the second half. The first-half result and TTM figures do not establish future recurring cash generation.',
    'Interest cash in operating cash flow is not deducted twice. Nuveen principal paid in financing is separate from interest paid in operating cash flow.',
    'Posted margin deposits of 1.436B and affiliate-financed eligible assets of 438M are already posted, not additional cash sources. Trust-security sale proceeds are reinvested within nuclear decommissioning funds and do not represent gross free cash available for debt repayment.',
    'Letters of credit total 3.587B: 1.092B corporate revolver, 1.759B other LOC facilities and 736M alternative facilities. The 1.092B already reduces revolver availability. Other LOC facilities are uncommitted credit support, not extra cash borrowing capacity.',
    'Note 12 also states 13M of BCOP debt-service reserve LCs while its credit facilities table displays zero project LCs. Scope/overlap with the 3.587B total is not established; no additional aggregate is inferred.',
    'The 2025 annual maturity schedule is historical. First-half refinancing and new debt prevent carrying it forward as remaining June maturities. The selected dated payments are not a full debt-service or obligations schedule.',
    'Cogentrix expected cash consideration is approximately 2.3B, with an estimated 1.5B of debt assumed and 5M shares also contemplated. Closing conditions and adjustments apply; late-2026 closing was an expectation, not a confirmed payment date or completed transaction.',
    'Helix initial 500M remains callable at June 30. Funded-to-date and call dates are Unavailable. The additional 500M milestones had not occurred; Vistra could elect to invest anyway. Neither amount is scheduled into December.',
    'No forecast surplus, cash runway or overall repayment shortfall is calculated. Future collateral calls, capex, acquisitions and transfer restrictions prevent combining dated cash and capacity into a promised funding result.',
]
