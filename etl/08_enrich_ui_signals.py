import os, json
import pandas as pd
import pycountry

SRC = "data/out/ui_shapes/signals.json"
DST = "data/out/ui_shapes/signals_enriched.json"
CODES = "data/parquet/product_codes_HS22.parquet"

def iso3_to_name(code):
    c = pycountry.countries.get(alpha_3=code)
    return c.name if c else code

def load_names():
    if os.path.isfile(CODES):
        df = pd.read_parquet(CODES, columns=["code","description"]).copy()
        df["code"] = df["code"].astype("Int64").astype("string").str.pad(6, fillchar="0")
        return dict(zip(df["code"], df["description"]))
    return {}

def main():
    if not os.path.isfile(SRC):
        print(f"[FAIL] Missing {SRC}. Run 31_build_ui_signals.py first.")
        raise SystemExit(1)

    with open(SRC, "r") as f:
        signals = json.load(f)
    if not isinstance(signals, list):
        print("[FAIL] signals.json is not an array")
        raise SystemExit(1)

    hs_names = load_names()

    out = []
    for s in signals:
        hs6 = s.get("hs6")
        iso3 = s.get("partner_iso3")
        p_name = hs_names.get(hs6, hs6)
        c_name = iso3_to_name(iso3)
        label = f"{s['type']} • {hs6} ({p_name}) → {iso3} ({c_name}) • intensity {s['intensity']:.2f}"
        out.append({**s, "product_name": p_name, "country_name": c_name, "label": label})

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[PASS] Wrote {DST} with {len(out)} items")
    for item in out[:3]:
        print(item["label"])

if __name__ == "__main__":
    main()
