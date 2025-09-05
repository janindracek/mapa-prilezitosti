import os, json, sys

SRC = "data/out/signals.json"
OUT_DIR = "data/out/ui_shapes"
DST = os.path.join(OUT_DIR, "signals.json")
MAX_TOTAL = 10

def main():
    if not os.path.isfile(SRC):
        print(f"[FAIL] Missing {SRC}. Run etl/40_signals.py first.")
        sys.exit(1)

    with open(SRC, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("[FAIL] signals.json is not a JSON array")
        sys.exit(1)

    # sort by intensity desc, cap to MAX_TOTAL
    data = sorted(data, key=lambda x: x.get("intensity", 0), reverse=True)[:MAX_TOTAL]

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(DST, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[PASS] Wrote {DST} with {len(data)} signals")
    for item in data[:5]:
        print(item)

if __name__ == "__main__":
    main()
