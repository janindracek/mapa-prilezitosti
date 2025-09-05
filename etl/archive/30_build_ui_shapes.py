import os
import pandas as pd
import pycountry
import json

INPUT = "data/out/metrics.parquet"
OUTPUT = "data/out/ui_shapes"
os.makedirs(OUTPUT, exist_ok=True)

df = pd.read_parquet(INPUT)

# Controls
countries = sorted(df["partner_iso3"].dropna().unique().tolist())
years = sorted(df["year"].dropna().unique().tolist())
metrics_list = [
    "podil_cz_na_importu",
    "YoY_export_change",
    "partner_share_in_cz_exports",
    "YoY_partner_share_change"
]
controls = {"countries": countries, "years": years, "metrics": metrics_list}
with open(os.path.join(OUTPUT, "controls.json"), "w") as f:
    json.dump(controls, f)

# Map: for a selected metric and year+hs6, but we demo with 'podil_cz_na_importu' for year=2023
sel_year = years[-1]
metric = metrics_list[0]
sub = df[df["year"] == sel_year][["partner_iso3", metric]].dropna().copy()

# Add country names
def iso3_to_name(code):
    country = pycountry.countries.get(alpha_3=code)
    return country.name if country else code
sub = sub.assign(name=sub["partner_iso3"].apply(iso3_to_name))

world_map = sub.rename(columns={"partner_iso3": "iso3", metric: "value"})\
    [["iso3","name","value"]]
world_map.to_json(os.path.join(OUTPUT, "world_map.json"), orient="records")

# Product bars: top 10 products by export for that year
prod = df[df["year"] == sel_year]
bars = prod.groupby("hs6")["export_cz_to_partner"].sum().nlargest(10).reset_index()
bars = bars.rename(columns={"hs6": "id", "export_cz_to_partner": "value"})
# Add HS names via product_codes file if available
try:
    codes_path = os.path.join("data", "parquet", "product_codes_HS22.parquet")
    if os.path.isfile(codes_path):
        codes = pd.read_parquet(codes_path, columns=["code", "description"]).copy()
        # normalize to zero-padded 6-char strings
        codes["code"] = codes["code"].astype("Int64").astype("string").str.pad(6, fillchar="0")
        codes = codes.rename(columns={"code": "id", "description": "name"})
        bars = bars.merge(codes, on="id", how="left")
        bars["name"] = bars["name"].fillna(bars["id"])  # fallback to HS6 code
    else:
        bars["name"] = bars["id"]
except Exception:
    # On any failure, fallback to HS6 code labels
    bars["name"] = bars["id"]

bars.to_json(os.path.join(OUTPUT, "product_bars.json"), orient="records")

# Trend mini: for one hs6 = bars[0], aggregated across partners (one point per year)
trend_hs6 = bars.loc[0, "id"]
trend = (
    df[df["hs6"] == trend_hs6]
      .groupby("year", as_index=False)["export_cz_to_partner"].sum()
      .rename(columns={"export_cz_to_partner": "value"})
      .sort_values("year")
)
trend.to_json(os.path.join(OUTPUT, "trend_mini.json"), orient="records")

print("[PASS] UI shapes written to data/out/ui_shapes/")
print("Sample controls:", controls)
print("Sample world_map:", world_map.head())
print("Sample product_bars:", bars.head())
print("Sample trend_mini for HS6", trend_hs6, ":", trend.head())
