"""
African universe for yfinance.

For the risk-gate test we focus on the top ~80 most liquid Johannesburg
Stock Exchange (JSE) names since that's where yfinance coverage is most
likely to work. Other African exchanges (Nigeria, Egypt, Kenya) have
spottier yfinance coverage and we'll evaluate them only if JSE proves out.

JSE tickers on yfinance use the .JO suffix:
  NPN.JO    Naspers
  SOL.JO    Sasol
  AGL.JO    Anglo American
  SLM.JO    Sanlam
  etc.

We hand-curate the list because there's no clean Wikipedia table for the
JSE Top 100 that scrapes reliably. This is the JSE Top 60-80 by market cap
as of late 2025 — large, liquid, foreign-investable names.
"""

# JSE Top ~80 by market cap (curated, all .JO suffix)
JSE_TOP_80 = [
    # Megacaps / tech
    "NPN.JO", "PRX.JO", "CFR.JO",
    # Banks
    "FSR.JO", "SBK.JO", "ABG.JO", "NED.JO", "CPI.JO", "INL.JO", "INP.JO",
    # Resources / mining
    "AGL.JO", "BHG.JO", "GLN.JO", "AMS.JO", "IMP.JO", "SSW.JO", "GFI.JO",
    "ANG.JO", "HAR.JO", "EXX.JO", "ARI.JO", "KIO.JO", "AFE.JO", "S32.JO",
    "NHM.JO", "DRD.JO", "PAN.JO",
    # Energy / chemicals
    "SOL.JO", "OMU.JO",
    # Insurance / financials
    "SLM.JO", "DSY.JO", "OUT.JO", "MMI.JO", "RMI.JO", "QLT.JO",
    # Retail / consumer
    "SHP.JO", "WHL.JO", "MRP.JO", "TFG.JO", "CLS.JO", "PIK.JO", "SPP.JO",
    "TBS.JO", "BID.JO", "BVT.JO", "AVI.JO",
    # Telecoms / media
    "MTN.JO", "VOD.JO",
    # Industrials / construction
    "RMH.JO", "BAW.JO", "PPC.JO", "RBP.JO", "MND.JO", "MNP.JO",
    # Property (REITs)
    "GRT.JO", "RDF.JO", "VKE.JO", "HYP.JO", "FFA.JO", "FFB.JO", "RES.JO",
    "EMI.JO", "ATT.JO",
    # Healthcare
    "APN.JO", "NTC.JO", "MEI.JO", "LHC.JO",
    # Diversified
    "BTI.JO", "REM.JO", "ABI.JO", "AIP.JO",
    # Tech / IT services
    "EOH.JO", "DTC.JO",
    # Other
    "TKG.JO", "DSY.JO", "SNT.JO", "TRU.JO", "MTM.JO",
]


def get_universe(n: int | None = None) -> list[str]:
    """Return JSE universe. Deduplicated. n=None returns all."""
    tickers = sorted(set(JSE_TOP_80))
    if n is None:
        return tickers
    return tickers[:n]
