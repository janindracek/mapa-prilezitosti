import os, glob
import pyarrow.parquet as pq

SEARCH_DIRS = ["data/parquet", "data/parquet/BACI_HS22_Y2022_V202501", "data/parquet/BACI_HS22_Y2023_V202501"]

CANDIDATE_COL_SETS = [
    {"reporter_iso3", "partner_iso3", "hs6", "year"},
    {"i", "j", "k", "t"},  # BACI canonical: i=exporter, j=importer, k=HS6, t=year
    {"exporter", "importer", "hs6", "year"},
]

def has_all(cols, need):
    cols_lower = {c.lower() for c in cols}
    return all(any(alt == c or alt.lower() == c for alt in cols_lower) for c in need)

def main():
    print("=== Probing for detailed HS6+partner datasets ===")
    checked = 0
    found = []
    for root in SEARCH_DIRS:
        if not os.path.isdir(root):
            continue
        for p in glob.glob(os.path.join(root, "**", "*.parquet"), recursive=True):
            try:
                pf = pq.ParquetFile(p)
                cols = pf.schema_arrow.names
                checked += 1
                cols_lower = {c.lower() for c in cols}
                for need in CANDIDATE_COL_SETS:
                    if need.issubset(cols_lower):
                        found.append((p, cols))
                        print(f"[FOUND] {p}")
                        print("        columns:", cols)
                        break
            except Exception as e:
                print(f"[WARN] Could not read {p}: {e}")

    if not found:
        print("[INFO] No detailed file found (exporter+importer+hs6+year). We will use Path B (partial).")
    else:
        print(f"[INFO] Checked {checked} files. Detailed candidates found: {len(found)}")
        print("Pick one of the FOUND paths above for Path A.")
    print("=== Probe complete ===")

if __name__ == "__main__":
    main()