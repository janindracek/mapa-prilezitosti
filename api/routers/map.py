import math
import pandas as pd
import pycountry
from fastapi import APIRouter

from api.data import cache

router = APIRouter()


@router.get("/map_v2")
def map_v2(hs6: str, year: int, metric: str = 'delta_export_abs', top: int = 0):
    """Unified map endpoint: returns [{ iso3, name, value }] for the selected metric."""
    df = cache.get_map_data()
    if df.empty:
        return []
    
    try:
        hs6_int = int(hs6)
    except Exception:
        return []
    
    sub = df[(df["hs6"] == hs6_int) & (df["year"] == int(year))]
    if sub.empty:
        # Fallback: use the latest available year for this HS6
        hs6_rows = df[df["hs6"] == hs6_int]
        if hs6_rows.empty:
            return []
        fb_year = int(hs6_rows["year"].max())
        if fb_year != int(year):
            try:
                print(f"/map_v2 fallback: year {year} -> {fb_year} for hs6={hs6_int}")
            except Exception:
                pass
        sub = hs6_rows[hs6_rows["year"] == fb_year]
        if sub.empty:
            return []
    
    # Pick metric column and recompute shares from primitives
    if metric == "partner_share_in_cz_exports":
        vals = (sub["cz_curr"] / sub["cz_world"]).where(sub["cz_world"] > 0, pd.NA)
        out = sub[["iso3", "name"]].copy()
        out["value"] = vals
    elif metric == "cz_share_in_partner_import":
        vals = (sub["cz_curr"] / sub["imp_total"]).where(sub["imp_total"] > 0, pd.NA)
        out = sub[["iso3", "name"]].copy()
        out["value"] = vals
    elif metric == "export_value_usd":
        # Return absolute Czech export values (current year)
        out = sub[["iso3", "name", "cz_curr"]].rename(columns={"cz_curr": "value"})
    else:
        # Default to year-over-year export change
        metric_col = "delta_export_abs"
        out = sub[["iso3", "name", metric_col]].rename(columns={metric_col: "value"})

    out = out.sort_values(["value", "iso3"], ascending=[False, True])
    if isinstance(top, int) and top > 0:
        out = out.head(top)

    rows = []
    for r in out.itertuples(index=False):
        iso3 = str(r.iso3) if r.iso3 is not None else ""
        name = (r.name or "")
        
        # Best-effort enrichment if iso3 looks like alphabetic ISO3
        if not name and len(iso3) == 3 and iso3.isalpha():
            try:
                rec = pycountry.countries.get(alpha_3=iso3)
                if rec:
                    name = rec.name
            except Exception:
                pass
        
        # Robust numeric coerce; treat NA/non-numeric as None
        val_raw = getattr(r, "value", None)
        try:
            fv = float(val_raw)
        except Exception:
            fv = float("nan")
        val = fv if math.isfinite(fv) else None
        
        rows.append({"iso3": iso3, "name": name, "value": val})
    
    return rows


