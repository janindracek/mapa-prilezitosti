import streamlit as st
import pandas as pd
import sys
from pathlib import Path

PARQ = Path(__file__).resolve().parents[1] / "data" / "parquet"

st.set_page_config(page_title="BACI Explorer", layout="wide")
st.title("BACI Explorer (HS22)")

@st.cache_data
def load_pair():
    p = PARQ / "trade_by_pair.parquet"
    if not p.exists():
        st.error("Missing data/parquet/trade_by_pair.parquet. Run your ETL to create it.")
        return None
    try:
        return pd.read_parquet(p)
    except Exception as e:
        st.error(f"Failed to read {p.name}: {e}. You likely need `pyarrow` or `fastparquet` installed.")
        return None

@st.cache_data
def load_hs2():
    p = PARQ / "trade_by_hs2.parquet"
    if not p.exists():
        st.info("HS2 table not found. Run etl/10_aggregate_metrics.py to create it.")
        return None
    return pd.read_parquet(p)

@st.cache_data
def load_countries():
    p = PARQ / "country_codes.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    # try to discover code/name columns flexibly
    code_col = next((c for c in df.columns if c.lower() in ("code","iso3n","iso_num","iso_num3","numeric")), None)
    name_col = next((c for c in df.columns if c.lower() in ("name","name_en","country","label")), None)
    if code_col and name_col:
        return df[[code_col, name_col]].rename(columns={code_col:"code", name_col:"country"})
    return None

pair = load_pair()
if pair is None:
    st.stop()
hs2 = load_hs2()
cty = load_countries()

# controls
years = sorted(pair["year"].dropna().unique())
exporters = sorted(pair["exporter"].dropna().unique())

# map exporter codes -> names for the select box, if available
if cty is not None:
    # be robust to non-numeric country codes in parquet
    cty_num = cty.copy()
    cty_num["code_num"] = pd.to_numeric(cty_num["code"], errors="coerce").astype("Int64")
    code_to_name = dict(cty_num.dropna(subset=["code_num"]).set_index("code_num")["country"])  # numeric ISO codes
else:
    code_to_name = {}

# ensure exporter codes are integers for select options
exporter_ints = sorted({int(x) for x in exporters if pd.notna(x)})
exp_label_map = {code: f"{code} – {code_to_name.get(code, '')}" for code in exporter_ints}

c1, c2 = st.columns(2)
year = c1.selectbox("Year", years, index=len(years)-1)
exporter = c2.selectbox("Exporter", exporter_ints, format_func=lambda v: exp_label_map.get(v, str(v)))

# filter
filtered = pair[(pair["year"] == year) & (pair["exporter"] == exporter)]

required_cols = {"year","exporter","importer","value_usd"}
missing = required_cols - set(pair.columns)
if missing:
    st.error(f"trade_by_pair.parquet is missing columns: {sorted(missing)}")
    st.stop()

st.subheader("Top partner markets")
if cty is not None and not filtered.empty:
    cty_num = cty.copy()
    cty_num["code_num"] = pd.to_numeric(cty_num["code"], errors="coerce").astype("Int64")
    imp_map = dict(cty_num.dropna(subset=["code_num"]).set_index("code_num")["country"])
    importer_numeric = pd.to_numeric(filtered["importer"], errors="coerce").astype("Int64")
    filtered = filtered.assign(importer_name = importer_numeric.map(imp_map))

filtered = filtered.sort_values("value_usd", ascending=False)
st.dataframe(filtered.head(50), use_container_width=True)

# Download button
st.download_button(
    "Download partners (CSV)",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name=f"partners_y{year}_exp{exporter}.csv",
    mime="text/csv",
)

# HS2 ranking for exporter
if hs2 is not None:
    st.subheader("Top HS2 categories for exporter")
    h = hs2[(hs2["year"] == year) & (hs2["exporter"] == exporter)].copy()
    h = h.sort_values("value_usd", ascending=False).head(50)
    st.dataframe(h, use_container_width=True)
    st.download_button(
        "Download HS2 (CSV)",
        h.to_csv(index=False).encode("utf-8"),
        file_name=f"hs2_y{year}_exp{exporter}.csv",
        mime="text/csv",
    )