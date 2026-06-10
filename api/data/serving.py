"""
Single serving-layer data access (M4b).

Reads ONLY data/serving/*.parquet (built by etl/07_build_serving.py) and shapes
it for the map and product-bar endpoints. Replaces the old DeploymentDataLoader
+ the dead api.shapes path. Signals go through UnifiedSignalsService; peer
groups through api.data.loaders — both also pointed at the serving layer.
"""
import os
from functools import lru_cache
from typing import Dict, List, Optional

import pandas as pd

from api.settings import settings

_MAP_METRIC = {
    "cz_share_in_partner_import": "podil_cz_na_importu",
    "export_value_usd": "export_cz_to_partner",
}

# The map/product shaping below only ever touches these 5 of core_trade's 19
# columns. Reading just these, with the pyarrow dtype backend (compact string
# storage), keeps the single resident copy ~66 MB AND — critically — keeps the
# READ-TIME peak low: the default object-string read explodes the two
# high-cardinality string columns to ~190 MB transient, inflating the RSS
# high-water mark past the 512 MB hosting cap. The pyarrow backend never
# materializes Python str objects, so peak RSS stays ~halved. Loading the full
# 19-col object frame was the cause of the /map_v2 OOM 502s. Output is identical
# to the float64 path (pyarrow doubles are full precision).
_CORE_COLS = ["year", "hs6", "partner_iso3", "podil_cz_na_importu", "export_cz_to_partner"]


class ServingDataLoader:
    def __init__(self):
        self._core = None
        self._countries = None
        self._hs6 = None

    @property
    def core_trade(self) -> pd.DataFrame:
        if self._core is None:
            p = settings.CORE_TRADE_PATH
            if os.path.isfile(p):
                self._core = pd.read_parquet(p, columns=_CORE_COLS, dtype_backend="pyarrow")
            else:
                self._core = pd.DataFrame()
        return self._core

    @lru_cache(maxsize=1)
    def _country_name_maps(self):
        p = settings.COUNTRIES_PATH
        if not os.path.isfile(p):
            return {}, {}
        c = pd.read_parquet(p)
        en = dict(zip(c["iso3"], c["name"].fillna(c["iso3"])))
        cz = dict(zip(c["iso3"], c["name_cz"].fillna(c["name"]).fillna(c["iso3"])))
        return en, cz

    def country_name(self, iso3: str, cz: bool = True) -> str:
        en_map, cz_map = self._country_name_maps()
        return (cz_map if cz else en_map).get(iso3, iso3)

    @lru_cache(maxsize=1)
    def hs6_names(self) -> Dict[str, str]:
        p = settings.HS6_NAMES_PATH
        if not os.path.isfile(p):
            return {}
        h = pd.read_parquet(p)
        return dict(zip(h["hs6"].astype(str), h["name"]))

    def get_map_data(self, hs6: str = None, metric: str = "export_cz_to_partner",
                     year: int = 2023, top: int = 0) -> List[Dict]:
        df = self.core_trade
        if df.empty:
            return []
        col = _MAP_METRIC.get(metric, metric)
        is_share = "podil" in col or "share" in col

        sub = df[df["year"] == int(year)] if year else df
        if hs6:
            sub = sub[sub["hs6"] == str(hs6).zfill(6)]
        if sub.empty or col not in sub.columns:
            return []

        agg = sub.groupby("partner_iso3")[col].sum().reset_index()
        results = []
        for _, r in agg.iterrows():
            v = float(r[col]) if pd.notnull(r[col]) else 0.0
            if is_share:
                value_fmt, unit = f"{v:.2%}", ""
            elif v >= 1e9:
                value_fmt, unit = f"{v/1e9:.1f}B", "USD"
            elif v >= 1e6:
                value_fmt, unit = f"{v/1e6:.1f}M", "USD"
            else:
                value_fmt, unit = f"{v:,.0f}", "USD"
            results.append({
                "iso3": r["partner_iso3"],
                "name": self.country_name(r["partner_iso3"]),
                "value": v, "value_fmt": value_fmt, "unit": unit,
            })
        results.sort(key=lambda x: x["value"], reverse=True)
        return results[:top] if top and top > 0 else results

    def get_products_data(self, country: str = None, top: int = 10, year: int = 2023,
                          hs2: Optional[str] = None) -> List[Dict]:
        df = self.core_trade
        if df.empty:
            return []
        sub = df[df["year"] == int(year)] if year else df
        if country:
            sub = sub[sub["partner_iso3"] == country]
        if hs2:
            sub = sub[sub["hs6"].str.startswith(str(hs2).zfill(2))]
        if sub.empty:
            return []
        prods = (sub.groupby("hs6")["export_cz_to_partner"].sum()
                    .sort_values(ascending=False).head(top).reset_index())
        names = self.hs6_names()
        out = []
        for _, r in prods.iterrows():
            v = float(r["export_cz_to_partner"]) if pd.notnull(r["export_cz_to_partner"]) else 0.0
            value_fmt = f"{v/1e6:.1f}M USD" if v >= 1e6 else f"{v:,.0f} USD"
            out.append({"id": str(r["hs6"]), "name": names.get(str(r["hs6"]), f"HS6 {r['hs6']}"),
                        "value": v, "value_fmt": value_fmt, "unit": "USD"})
        return out


serving_data = ServingDataLoader()
