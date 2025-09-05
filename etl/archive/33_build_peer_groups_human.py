import sys
from pathlib import Path
import pandas as pd
from typing import Tuple, List

OUT_DIR = Path("data/out")
BASE = OUT_DIR / "peer_groups.csv"  # use this to get the numeric iso3 universe present in your data
OUT = OUT_DIR / "peer_groups_human.csv"

METHOD = "human_geo_econ_v2"
YEAR = 2023

# --- Helpers ---

def log(msg: str):
    print(f"[peer-human] {msg}")


def load_base_iso3() -> pd.Series:
    if not BASE.exists():
        log(f"ERROR: {BASE} not found. Run your earlier pipeline first.")
        sys.exit(2)
    df = pd.read_csv(BASE)
    # Expect numeric ISO3 (UN M49) as in your other files
    if "iso3" not in df.columns:
        log("ERROR: 'iso3' column missing in base file.")
        sys.exit(2)
    iso = df["iso3"].astype(str).str.strip()
    return iso.drop_duplicates().sort_values().reset_index(drop=True)


# --- Human-logic groups (alpha-3 lists). We will map numeric->alpha3 via pycountry.
# To avoid a hard dependency, we do mapping lazily and tolerate missing ones.
try:
    import pycountry  # type: ignore
except Exception:
    pycountry = None
    log("WARN: pycountry not installed; some mappings may be skipped. Install with: pip install pycountry")

if pycountry is None:
    log("ERROR: pycountry is required for numeric->alpha3 mapping. Install with: pip install pycountry")
    sys.exit(2)


def num_to_a3(num_str: str) -> str | None:
    if pycountry is None:
        return None
    try:
        rec = pycountry.countries.get(numeric=str(int(num_str)).zfill(3))
        return rec.alpha_3 if rec else None
    except Exception:
        return None


# Define fine-grained groups using alpha-3 codes
G = {
    0: ("EU Core West", [
        "DEU","FRA","NLD","BEL","LUX","IRL"
    ]),
    1: ("EU Nordics", [
        "SWE","FIN","DNK","NOR","ISL"
    ]),
    2: ("Baltics", [
        "EST","LVA","LTU"
    ]),
    3: ("Central Europe (V4+AT+SI+ROU)", [
        "CZE","SVK","POL","HUN","AUT","SVN","ROU"
    ]),
    4: ("Southern EU (Med EU)", [
        "ESP","PRT","ITA","GRC","MLT","CYP","HRV"
    ]),
    5: ("UK & CH", [
        "GBR","CHE"
    ]),
    6: ("Western Balkans", [
        "ALB","BIH","MNE","SRB","MKD","BGR"
    ]),
    7: ("Eastern Partnership & Caucasus", [
        "UKR","MDA","GEO","ARM","AZE","BLR"
    ]),
    8: ("Russia & Central Asia", [
        "RUS","KAZ","KGZ","UZB","TJK","TKM","MNG"
    ]),
    9: ("North America", [
        "USA","CAN","MEX"
    ]),
    10: ("Central America & Caribbean", [
        "GTM","HND","SLV","NIC","CRI","PAN","CUB","DOM","HTI","JAM","TTO","BRB","BHS","GRD","BLZ","ATG","DMA","KNA","LCA","VCT"
    ]),
    11: ("South America", [
        "ARG","BRA","CHL","PER","ECU","URY","PRY","BOL","VEN","GUY","SUR","COL"
    ]),
    12: ("GCC", [
        "SAU","ARE","QAT","KWT","OMN","BHR"
    ]),
    13: ("Levant & Iran/Iraq/Yemen", [
        "ISR","JOR","LBN","SYR","PSE","IRN","IRQ","YEM","TUR"
    ]),
    14: ("North Africa (Med non-EU)", [
        "MAR","DZA","TUN","LBY","EGY","ESH","MRT"
    ]),
    15: ("East Asia Advanced", [
        "JPN","KOR","TWN","HKG","MAC","PRK"
    ]),
    16: ("China", [
        "CHN"
    ]),
    17: ("Southeast Asia", [
        "SGP","MYS","THA","VNM","PHL","IDN","KHM","LAO","MMR","BRN","TLS"
    ]),
    18: ("South Asia", [
        "IND","PAK","BGD","NPL","LKA","MDV","BTN"
    ]),
    19: ("Sub-Saharan Africa – West", [
        "NGA","GHA","CIV","SEN","GMB","SLE","LBR","GIN","GNB","CPV","TGO","BEN","BFA","NER","TCD","MLI"
    ]),
    20: ("Sub-Saharan Africa – East & Horn", [
        "KEN","UGA","TZA","ETH","SSD","SDN","ERI","DJI","SOM","RWA","BDI"
    ]),
    21: ("Sub-Saharan Africa – South", [
        "ZAF","NAM","BWA","LSO","SWZ","MOZ","AGO","ZMB","MWI","ZWE","MDG","COM","MUS","SYC","GAB","COG","GNQ","CMR","CAF","STP"
    ]),
    22: ("Oceania & Pacific", [
        "AUS","NZL","FJI","PNG","VUT","SLB","WSM","TON","KIR","TUV","NRU","MHL","PLW","FSM"
    ]),
}

# --- Build mapping from alpha-3 to cluster id ---
a3_to_cluster: dict[str,int] = {}
for cid, (_name, members) in G.items():
    for a3 in members:
        a3_to_cluster[a3] = cid


def assign_clusters(iso_numeric: pd.Series) -> Tuple[pd.DataFrame, List[str]]:
    rows = []
    missing_a3 = []
    for num in iso_numeric:
        a3 = num_to_a3(num)
        if not a3:
            missing_a3.append(num)
            continue
        cid = a3_to_cluster.get(a3)
        if cid is None:
            # not assigned => skip for now
            missing_a3.append(num)
            continue
        rows.append({
            "iso3": num,
            "cluster": cid,
            "method": METHOD,
            "k": len(G),
            "year": YEAR,
        })
    return pd.DataFrame(rows), sorted(set(missing_a3))


def main():
    iso_numeric = load_base_iso3()
    out_df, missing = assign_clusters(iso_numeric)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT, index=False)
    log(f"Wrote {OUT} with {len(out_df)} rows across {out_df['cluster'].nunique()} clusters.")
    if missing:
        miss_path = OUT_DIR / "peer_groups_human_missing_iso.txt"
        with open(miss_path, "w") as f:
            for m in missing:
                f.write(str(m) + "\n")
        log(f"Unassigned ISO numeric codes written to {miss_path} ({len(missing)} items). You can either add them to a group or ignore.")

if __name__ == "__main__":
    main()
