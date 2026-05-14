export type StockMetadata = {
  symbol: string;
  name: string;
  exchange: string;
  country?: string;
  logoDomain?: string;
};

const STOCK_METADATA: Record<string, StockMetadata> = {
  // US swing and dividend names
  ABT: { symbol: "ABT", name: "Abbott Laboratories", exchange: "NYSE", logoDomain: "abbott.com" },
  ACN: { symbol: "ACN", name: "Accenture plc", exchange: "NYSE", logoDomain: "accenture.com" },
  ADBE: { symbol: "ADBE", name: "Adobe Inc.", exchange: "NASDAQ", logoDomain: "adobe.com" },
  AIZ: { symbol: "AIZ", name: "Assurant, Inc.", exchange: "NYSE", logoDomain: "assurant.com" },
  APP: {
    symbol: "APP",
    name: "AppLovin Corporation",
    exchange: "NASDAQ",
    logoDomain: "applovin.com",
  },
  ARE: {
    symbol: "ARE",
    name: "Alexandria Real Estate Equities",
    exchange: "NYSE",
    logoDomain: "are.com",
  },
  AVGO: { symbol: "AVGO", name: "Broadcom Inc.", exchange: "NASDAQ", logoDomain: "broadcom.com" },
  AXON: {
    symbol: "AXON",
    name: "Axon Enterprise, Inc.",
    exchange: "NASDAQ",
    logoDomain: "axon.com",
  },
  BAX: { symbol: "BAX", name: "Baxter International", exchange: "NYSE", logoDomain: "baxter.com" },
  BLK: { symbol: "BLK", name: "BlackRock, Inc.", exchange: "NYSE", logoDomain: "blackrock.com" },
  BRO: { symbol: "BRO", name: "Brown & Brown, Inc.", exchange: "NYSE", logoDomain: "bbrown.com" },
  CDW: { symbol: "CDW", name: "CDW Corporation", exchange: "NASDAQ", logoDomain: "cdw.com" },
  CMCSA: {
    symbol: "CMCSA",
    name: "Comcast Corporation",
    exchange: "NASDAQ",
    logoDomain: "comcast.com",
  },
  COIN: {
    symbol: "COIN",
    name: "Coinbase Global, Inc.",
    exchange: "NASDAQ",
    logoDomain: "coinbase.com",
  },
  CRM: { symbol: "CRM", name: "Salesforce, Inc.", exchange: "NYSE", logoDomain: "salesforce.com" },
  FDS: {
    symbol: "FDS",
    name: "FactSet Research Systems",
    exchange: "NYSE",
    logoDomain: "factset.com",
  },
  FISV: { symbol: "FISV", name: "Fiserv, Inc.", exchange: "NYSE", logoDomain: "fiserv.com" },
  FIX: {
    symbol: "FIX",
    name: "Comfort Systems USA",
    exchange: "NYSE",
    logoDomain: "comfortsystemsusa.com",
  },
  FSLR: {
    symbol: "FSLR",
    name: "First Solar, Inc.",
    exchange: "NASDAQ",
    logoDomain: "firstsolar.com",
  },
  FTNT: { symbol: "FTNT", name: "Fortinet, Inc.", exchange: "NASDAQ", logoDomain: "fortinet.com" },
  GDDY: { symbol: "GDDY", name: "GoDaddy Inc.", exchange: "NYSE", logoDomain: "godaddy.com" },
  GS: {
    symbol: "GS",
    name: "Goldman Sachs Group",
    exchange: "NYSE",
    logoDomain: "goldmansachs.com",
  },
  IBM: {
    symbol: "IBM",
    name: "International Business Machines",
    exchange: "NYSE",
    logoDomain: "ibm.com",
  },
  INTC: { symbol: "INTC", name: "Intel Corporation", exchange: "NASDAQ", logoDomain: "intel.com" },
  LEN: { symbol: "LEN", name: "Lennar Corporation", exchange: "NYSE", logoDomain: "lennar.com" },
  LITE: {
    symbol: "LITE",
    name: "Lumentum Holdings",
    exchange: "NASDAQ",
    logoDomain: "lumentum.com",
  },
  LNT: {
    symbol: "LNT",
    name: "Alliant Energy",
    exchange: "NASDAQ",
    logoDomain: "alliantenergy.com",
  },
  LOW: { symbol: "LOW", name: "Lowe's Companies", exchange: "NYSE", logoDomain: "lowes.com" },
  LRCX: {
    symbol: "LRCX",
    name: "Lam Research Corporation",
    exchange: "NASDAQ",
    logoDomain: "lamresearch.com",
  },
  MO: { symbol: "MO", name: "Altria Group", exchange: "NYSE", logoDomain: "altria.com" },
  MOS: { symbol: "MOS", name: "The Mosaic Company", exchange: "NYSE", logoDomain: "mosaicco.com" },
  MRNA: { symbol: "MRNA", name: "Moderna, Inc.", exchange: "NASDAQ", logoDomain: "modernatx.com" },
  MS: { symbol: "MS", name: "Morgan Stanley", exchange: "NYSE", logoDomain: "morganstanley.com" },
  MSFT: {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    exchange: "NASDAQ",
    logoDomain: "microsoft.com",
  },
  NFLX: { symbol: "NFLX", name: "Netflix, Inc.", exchange: "NASDAQ", logoDomain: "netflix.com" },
  NWS: { symbol: "NWS", name: "News Corporation", exchange: "NASDAQ", logoDomain: "newscorp.com" },
  ORCL: { symbol: "ORCL", name: "Oracle Corporation", exchange: "NYSE", logoDomain: "oracle.com" },
  PSKY: {
    symbol: "PSKY",
    name: "Paramount Skydance",
    exchange: "NASDAQ",
    logoDomain: "paramount.com",
  },
  QCOM: {
    symbol: "QCOM",
    name: "Qualcomm Incorporated",
    exchange: "NASDAQ",
    logoDomain: "qualcomm.com",
  },
  SATS: {
    symbol: "SATS",
    name: "EchoStar Corporation",
    exchange: "NASDAQ",
    logoDomain: "echostar.com",
  },
  SMCI: {
    symbol: "SMCI",
    name: "Super Micro Computer",
    exchange: "NASDAQ",
    logoDomain: "supermicro.com",
  },
  STX: { symbol: "STX", name: "Seagate Technology", exchange: "NASDAQ", logoDomain: "seagate.com" },
  TGT: { symbol: "TGT", name: "Target Corporation", exchange: "NYSE", logoDomain: "target.com" },
  TTD: {
    symbol: "TTD",
    name: "The Trade Desk",
    exchange: "NASDAQ",
    logoDomain: "thetradedesk.com",
  },
  VEEV: { symbol: "VEEV", name: "Veeva Systems", exchange: "NYSE", logoDomain: "veeva.com" },

  // Europe latest-pick names
  "ACX.MC": {
    symbol: "ACX.MC",
    name: "Acerinox, S.A.",
    exchange: "BME",
    logoDomain: "acerinox.com",
  },
  "ADM.L": {
    symbol: "ADM.L",
    name: "Admiral Group plc",
    exchange: "LSE",
    logoDomain: "admiralgroup.co.uk",
  },
  "ADYEN.AS": {
    symbol: "ADYEN.AS",
    name: "Adyen N.V.",
    exchange: "Euronext Amsterdam",
    logoDomain: "adyen.com",
  },
  "ANTO.L": {
    symbol: "ANTO.L",
    name: "Antofagasta plc",
    exchange: "LSE",
    logoDomain: "antofagasta.co.uk",
  },
  "AUTO.L": {
    symbol: "AUTO.L",
    name: "Auto Trader Group plc",
    exchange: "LSE",
    logoDomain: "autotrader.co.uk",
  },
  "BBVA.MC": {
    symbol: "BBVA.MC",
    name: "Banco Bilbao Vizcaya Argentaria",
    exchange: "BME",
    logoDomain: "bbva.com",
  },
  "BBY.L": {
    symbol: "BBY.L",
    name: "Balfour Beatty plc",
    exchange: "LSE",
    logoDomain: "balfourbeatty.com",
  },
  "BEZ.L": { symbol: "BEZ.L", name: "Beazley plc", exchange: "LSE", logoDomain: "beazley.com" },
  "BME.L": {
    symbol: "BME.L",
    name: "B&M European Value Retail",
    exchange: "LSE",
    logoDomain: "bandmretail.com",
  },
  "CPG.L": {
    symbol: "CPG.L",
    name: "Compass Group plc",
    exchange: "LSE",
    logoDomain: "compass-group.com",
  },
  "CTG.L": {
    symbol: "CTG.L",
    name: "Christie Group plc",
    exchange: "LSE",
    logoDomain: "christiegroup.com",
  },
  "DGE.L": { symbol: "DGE.L", name: "Diageo plc", exchange: "LSE", logoDomain: "diageo.com" },
  "DIA.MC": {
    symbol: "DIA.MC",
    name: "Distribuidora Internacional de Alimentacion",
    exchange: "BME",
    logoDomain: "dia.es",
  },
  "DLN.L": {
    symbol: "DLN.L",
    name: "Derwent London plc",
    exchange: "LSE",
    logoDomain: "derwentlondon.com",
  },
  "FER.AS": {
    symbol: "FER.AS",
    name: "Ferrovial SE",
    exchange: "Euronext Amsterdam",
    logoDomain: "ferrovial.com",
  },
  "GAW.L": {
    symbol: "GAW.L",
    name: "Games Workshop Group",
    exchange: "LSE",
    logoDomain: "games-workshop.com",
  },
  "HIK.L": {
    symbol: "HIK.L",
    name: "Hikma Pharmaceuticals",
    exchange: "LSE",
    logoDomain: "hikma.com",
  },
  "III.L": { symbol: "III.L", name: "3i Group plc", exchange: "LSE", logoDomain: "3i.com" },
  "JMT.LS": {
    symbol: "JMT.LS",
    name: "Jeronimo Martins",
    exchange: "Euronext Lisbon",
    logoDomain: "jeronimomartins.com",
  },
  "KER.PA": {
    symbol: "KER.PA",
    name: "Kering SA",
    exchange: "Euronext Paris",
    logoDomain: "kering.com",
  },
  "LIGHT.AS": {
    symbol: "LIGHT.AS",
    name: "Signify N.V.",
    exchange: "Euronext Amsterdam",
    logoDomain: "signify.com",
  },
  "NXT.L": { symbol: "NXT.L", name: "Next plc", exchange: "LSE", logoDomain: "nextplc.co.uk" },
  "NTGY.MC": {
    symbol: "NTGY.MC",
    name: "Naturgy Energy Group",
    exchange: "BME",
    logoDomain: "naturgy.com",
  },
  "OCDO.L": {
    symbol: "OCDO.L",
    name: "Ocado Group plc",
    exchange: "LSE",
    logoDomain: "ocadogroup.com",
  },
  "OR.PA": {
    symbol: "OR.PA",
    name: "L'Oreal S.A.",
    exchange: "Euronext Paris",
    logoDomain: "loreal.com",
  },
  "RCO.PA": {
    symbol: "RCO.PA",
    name: "Remy Cointreau",
    exchange: "Euronext Paris",
    logoDomain: "remy-cointreau.com",
  },
  "REL.L": { symbol: "REL.L", name: "RELX plc", exchange: "LSE", logoDomain: "relx.com" },
  "RMV.L": {
    symbol: "RMV.L",
    name: "Rightmove plc",
    exchange: "LSE",
    logoDomain: "rightmove.co.uk",
  },
  "SBRY.L": {
    symbol: "SBRY.L",
    name: "J Sainsbury plc",
    exchange: "LSE",
    logoDomain: "sainsburys.co.uk",
  },
  "SCT.L": { symbol: "SCT.L", name: "Softcat plc", exchange: "LSE", logoDomain: "softcat.com" },
  "SOLB.BR": {
    symbol: "SOLB.BR",
    name: "Solvay SA",
    exchange: "Euronext Brussels",
    logoDomain: "solvay.com",
  },
  "TATE.L": {
    symbol: "TATE.L",
    name: "Tate & Lyle plc",
    exchange: "LSE",
    logoDomain: "tateandlyle.com",
  },
  "TEP.PA": {
    symbol: "TEP.PA",
    name: "Teleperformance SE",
    exchange: "Euronext Paris",
    logoDomain: "teleperformance.com",
  },
  "UBI.PA": {
    symbol: "UBI.PA",
    name: "Ubisoft Entertainment",
    exchange: "Euronext Paris",
    logoDomain: "ubisoft.com",
  },
  "UTG.L": {
    symbol: "UTG.L",
    name: "Unite Group plc",
    exchange: "LSE",
    logoDomain: "unitegroup.com",
  },
  "VIV.PA": {
    symbol: "VIV.PA",
    name: "Vivendi SE",
    exchange: "Euronext Paris",
    logoDomain: "vivendi.com",
  },
  "VK.PA": {
    symbol: "VK.PA",
    name: "Vallourec S.A.",
    exchange: "Euronext Paris",
    logoDomain: "vallourec.com",
  },
  "WKL.AS": {
    symbol: "WKL.AS",
    name: "Wolters Kluwer N.V.",
    exchange: "Euronext Amsterdam",
    logoDomain: "wolterskluwer.com",
  },
  "WLN.PA": {
    symbol: "WLN.PA",
    name: "Worldline SA",
    exchange: "Euronext Paris",
    logoDomain: "worldline.com",
  },
  "WTB.L": {
    symbol: "WTB.L",
    name: "Whitbread plc",
    exchange: "LSE",
    logoDomain: "whitbread.co.uk",
  },

  // JSE names
  "ABG.JO": {
    symbol: "ABG.JO",
    name: "Absa Group Limited",
    exchange: "JSE",
    logoDomain: "absa.africa",
  },
  "AGL.JO": {
    symbol: "AGL.JO",
    name: "Anglo American plc",
    exchange: "JSE",
    logoDomain: "angloamerican.com",
  },
  "ANG.JO": {
    symbol: "ANG.JO",
    name: "AngloGold Ashanti",
    exchange: "JSE",
    logoDomain: "anglogoldashanti.com",
  },
  "APN.JO": {
    symbol: "APN.JO",
    name: "Aspen Pharmacare",
    exchange: "JSE",
    logoDomain: "aspenpharma.com",
  },
  "ARI.JO": {
    symbol: "ARI.JO",
    name: "African Rainbow Minerals",
    exchange: "JSE",
    logoDomain: "arm.co.za",
  },
  "ATT.JO": {
    symbol: "ATT.JO",
    name: "Attacq Limited",
    exchange: "JSE",
    logoDomain: "attacq.co.za",
  },
  "CLS.JO": {
    symbol: "CLS.JO",
    name: "Clicks Group Limited",
    exchange: "JSE",
    logoDomain: "clicksgroup.co.za",
  },
  "DRD.JO": {
    symbol: "DRD.JO",
    name: "DRDGOLD Limited",
    exchange: "JSE",
    logoDomain: "drdgold.com",
  },
  "HAR.JO": {
    symbol: "HAR.JO",
    name: "Harmony Gold Mining",
    exchange: "JSE",
    logoDomain: "harmony.co.za",
  },
  "IMP.JO": {
    symbol: "IMP.JO",
    name: "Impala Platinum Holdings",
    exchange: "JSE",
    logoDomain: "implats.co.za",
  },
  "INL.JO": {
    symbol: "INL.JO",
    name: "Investec Limited",
    exchange: "JSE",
    logoDomain: "investec.com",
  },
  "MRP.JO": {
    symbol: "MRP.JO",
    name: "Mr Price Group",
    exchange: "JSE",
    logoDomain: "mrpricegroup.com",
  },
  "PIK.JO": {
    symbol: "PIK.JO",
    name: "Pick n Pay Stores",
    exchange: "JSE",
    logoDomain: "pnp.co.za",
  },
  "SOL.JO": { symbol: "SOL.JO", name: "Sasol Limited", exchange: "JSE", logoDomain: "sasol.com" },
  "SSW.JO": {
    symbol: "SSW.JO",
    name: "Sibanye Stillwater",
    exchange: "JSE",
    logoDomain: "sibanyestillwater.com",
  },
  "TFG.JO": {
    symbol: "TFG.JO",
    name: "The Foschini Group",
    exchange: "JSE",
    logoDomain: "tfglimited.co.za",
  },
  "TKG.JO": {
    symbol: "TKG.JO",
    name: "Telkom SA SOC",
    exchange: "JSE",
    logoDomain: "telkom.co.za",
  },
};

export function getStockMetadata(symbol: string): StockMetadata {
  const metadata = STOCK_METADATA[symbol] ?? {
    symbol,
    name: inferCompanyName(symbol),
    exchange: inferExchange(symbol),
  };

  return {
    ...metadata,
    country: metadata.country ?? inferCountry(symbol),
  };
}

export function getLogoUrl(symbol: string): string | null {
  const domain = getStockMetadata(symbol).logoDomain;
  return domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : null;
}

function inferCompanyName(symbol: string): string {
  const root = symbol.replace(/\.(JO|L|PA|AS|MC|BR|LS|DE|SW|CO|MI|ST|HE|VI|OL|WA)$/u, "");
  return `${root} listed company`;
}

function inferExchange(symbol: string): string {
  if (symbol.endsWith(".JO")) return "JSE";
  if (symbol.endsWith(".L")) return "LSE";
  if (symbol.endsWith(".PA")) return "Euronext Paris";
  if (symbol.endsWith(".AS")) return "Euronext Amsterdam";
  if (symbol.endsWith(".MC")) return "BME";
  if (symbol.endsWith(".BR")) return "Euronext Brussels";
  if (symbol.endsWith(".LS")) return "Euronext Lisbon";
  if (symbol.endsWith(".DE")) return "Xetra";
  if (symbol.endsWith(".SW")) return "SIX Swiss Exchange";
  if (symbol.endsWith(".CO")) return "Nasdaq Copenhagen";
  if (symbol.endsWith(".MI")) return "Borsa Italiana";
  if (symbol.endsWith(".ST")) return "Nasdaq Stockholm";
  if (symbol.endsWith(".HE")) return "Nasdaq Helsinki";
  if (symbol.endsWith(".VI")) return "Vienna Stock Exchange";
  if (symbol.endsWith(".OL")) return "Oslo Stock Exchange";
  if (symbol.endsWith(".WA")) return "Warsaw Stock Exchange";
  return "US listed";
}

function inferCountry(symbol: string): string {
  if (symbol.endsWith(".JO")) return "South Africa";
  if (symbol.endsWith(".L")) return "United Kingdom";
  if (symbol.endsWith(".PA")) return "France";
  if (symbol.endsWith(".AS")) return "Netherlands";
  if (symbol.endsWith(".MC")) return "Spain";
  if (symbol.endsWith(".BR")) return "Belgium";
  if (symbol.endsWith(".LS")) return "Portugal";
  if (symbol.endsWith(".DE")) return "Germany";
  if (symbol.endsWith(".SW")) return "Switzerland";
  if (symbol.endsWith(".CO")) return "Denmark";
  if (symbol.endsWith(".MI")) return "Italy";
  if (symbol.endsWith(".ST")) return "Sweden";
  if (symbol.endsWith(".HE")) return "Finland";
  if (symbol.endsWith(".VI")) return "Austria";
  if (symbol.endsWith(".OL")) return "Norway";
  if (symbol.endsWith(".WA")) return "Poland";
  return "United States";
}
