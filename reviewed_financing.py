"""Small, accession-specific manual financing review; no inference from form or item numbers.

Only the listed documents were checked. The EDGAR submissions index supplies the actual filing
list at run time; unknown, changed, and later filings remain Not checked. This is not a live
document classifier and these events never change the dated balance-sheet metrics.
"""

from copy import deepcopy

REVIEWED_AS_OF = "2026-10-14"
VST_BALANCE_DATE = "2026-06-30"
BASE = "https://www.sec.gov/Archives/edgar/data/1692819/"

# Dates and forms are independently matched against EDGAR's submissions index. The links point to
# the document supporting each statement; offering documents describe one transaction, not four.
VST = {
    "0001140361-26-026944": {
        "form": "8-K", "filed": "2026-06-30", "period": "2026-06-24",
        "event_date": "2026-06-24", "kind": "Facility capacity before balance sheet",
        "finding": ("Corporate revolving credit commitments increased from $3.44 billion "
                    "to $5.50 billion and certain guarantees and covenants changed. The "
                    "event preceded the June 30 balance sheet; $5.50 billion is facility "
                    "capacity, not an additional borrowing after that date."),
        "source_url": BASE + "000114036126026944/ef20077059_8k.htm",
        "related": [("Credit agreement amendment, Ex. 10.1",
                     BASE + "000114036126026944/ef20077059_ex10-1.htm"),
                    ("Commodity-linked amendment, Ex. 10.2",
                     BASE + "000114036126026944/ef20077059_ex10-2.htm")],
    },
    "0001140361-26-028619": {
        "form": "8-K", "filed": "2026-07-16", "period": "2026-07-10",
        "event_date": "2026-07-10", "kind": "Facility capacity and term",
        "finding": ("Receivables purchasers' aggregate commitment rose from $1.1 billion to "
                    "$1.25 billion, and the agreement was extended to July 9, 2027. The "
                    "separate repurchase facility was also extended to that date. The $1.25 "
                    "billion is capacity, not a reported outstanding borrowing."),
        "source_url": BASE + "000114036126028619/ef20077984_8k.htm",
        "related": [
            ("Receivables amendment, Ex. 4.1", BASE + "000114036126028619/ef20077984_ex4-1.htm"),
            ("Repurchase amendment, Ex. 10.1", BASE + "000114036126028619/ef20077984_ex10-1.htm"),
        ],
    },
    "0001140361-26-028454": {
        "form": "8-K", "filed": "2026-07-14", "period": "2026-07-14",
        "event_date": "2026-07-14", "kind": "Not a financing filing",
        "finding": ("Reports PJM electricity capacity auction results for planning year "
                    "2028/2029; it does not report a new borrowing or financing facility."),
        "source_url": BASE + "000114036126028454/ef20077988_8k.htm",
        "related": [],
    },
    "0001692819-26-000017": {
        "form": "8-K", "filed": "2026-08-07", "period": "2026-08-07",
        "event_date": "2026-08-07", "kind": "Earnings release, not later borrowing",
        "finding": ("Exhibit 99.1 reports June 30 liquidity, including $4,408 million "
                    "corporate revolver availability and $1,452 million commodity-linked "
                    "availability. These are June 30 availability figures, not later "
                    "borrowing. The release also discusses the Helix investment commitment, "
                    "which is outside baseline debt."),
        "source_url": BASE + "000169281926000017/vistra-20260807.htm",
        "related": [("Earnings release, Ex. 99.1",
                     BASE + "000169281926000017/vistra-20260630xearningsre.htm")],
    },
    "0001140361-26-035954": {
        "form": "S-3ASR", "filed": "2026-09-09", "period": "",
        "event_date": "", "kind": "Shelf registration, not issuance",
        "finding": ("Registers securities for possible offerings. The later pricing "
                    "sheet, final prospectus and September 24 8-K identify the completed "
                    "junior-note issuance; this registration is not a separate borrowing."),
        "source_url": BASE + "000114036126035954/ny20081693x1_s3asr.htm",
        "related": [],
    },
    "0001140361-26-036130": {
        "form": "424B5", "filed": "2026-09-10", "period": "",
        "event_date": "", "kind": "Preliminary offering document, not issuance",
        "finding": ("Preliminary prospectus for the two junior-note series due 2057 "
                    "has blank principal amounts and rates. The later FWP supplies pricing "
                    "and the September 24 8-K confirms issuance; this document is not "
                    "another borrowing."),
        "source_url": BASE + "000114036126036130/ny20081693x2_424b5.htm",
        "related": [],
    },
    "0001140361-26-036245": {
        "form": "FWP", "filed": "2026-09-11", "period": "",
        "event_date": "2026-09-10", "kind": "Pricing terms; same notes as September 24 issuance",
        "finding": ("Pricing sheet for $850 million Series A and $650 million Series B "
                    "junior subordinated notes due 2057, with initial rates of 7.000% and "
                    "7.250%. It projected September 24 settlement; the later 8-K confirms "
                    "issuance. This is not additional debt beyond that issuance."),
        "source_url": BASE + "000114036126036245/ef20081902_fwp.htm",
        "related": [],
    },
    "0001140361-26-036415": {
        "form": "424B2", "filed": "2026-09-14", "period": "",
        "event_date": "", "kind": "Final offering terms; same notes as September 24 issuance",
        "finding": ("Final prospectus estimates about $1.48 billion in net proceeds. It says "
                    "proceeds are intended for general corporate purposes, including possible "
                    "redemption of Series A and B preferred stock at or after their October "
                    "and December reset dates. Redemption is not confirmed here; the "
                    "prospectus is not another issuance."),
        "source_url": BASE + "000114036126036415/ny20081693x3_424b2.htm",
        "related": [],
    },
    "0001140361-26-037577": {
        "form": "8-K", "filed": "2026-09-24", "period": "2026-09-24",
        "event_date": "2026-09-24", "kind": "New debt issued after balance sheet",
        "finding": ("Vistra Operations completed $1.5 billion of junior subordinated "
                    "notes due 2057: $850 million Series A at an initial 7.000% and "
                    "$650 million Series B at an initial 7.250%, guaranteed by Vistra. "
                    "The indenture permits "
                    "interest deferral for up to 10 consecutive years per period, subject "
                    "to its terms. This issuance is not part of June 30 debt."),
        "source_url": BASE + "000114036126037577/ef20082680_8k.htm",
        "related": [
            ("Supplemental indenture, Ex. 4.2", BASE + "000114036126037577/ef20082680_ex4-2.htm"),
        ],
    },
    "0001140361-26-038468": {
        "form": "8-K", "filed": "2026-10-02", "period": "2026-09-30",
        "event_date": "2026-09-30", "kind": "Facility maturity change",
        "finding": ("Commodity-linked revolving credit facility maturity was extended "
                    "from September 30, 2026 to September 29, 2027. This filing does "
                    "not establish an additional amount borrowed."),
        "source_url": BASE + "000114036126038468/ef20083016_8k.htm",
        "related": [("Credit agreement amendment, Ex. 10.1",
                     BASE + "000114036126038468/ef20083016_ex10-1.htm")],
    },
}


def annotate(inventory: dict, ticker: str) -> dict:
    """Add only accession-matched, source-checked findings to the live index.

    Never use a review performed later than the requested index-through date, or apply this
    checked anchor's review to another balance sheet. Incomplete indexes keep their incomplete status.
    """
    import oracle_financing
    result = deepcopy(inventory)
    company = ticker.upper()
    checked_filings, balance = ((VST, VST_BALANCE_DATE) if company == "VST" else
                                (oracle_financing.FILINGS, oracle_financing.ANCHOR) if company == "ORCL" else
                                ({}, ""))
    if not checked_filings or result.get("since") != balance \
            or result.get("through", "") < REVIEWED_AS_OF:
        return result
    for row in result.get("filings", []):
        checked = checked_filings.get(row.get("accession"))
        # reportDate is an event date for an 8-K; offering forms need not carry one.
        keys = ("form", "filed", "period") if row.get("form") == "8-K" else ("form", "filed")
        if checked and all(row.get(k, "") == checked[k] for k in keys):
            row.update(deepcopy(checked))
            row["review"] = f"Checked {REVIEWED_AS_OF}"
    return result
