import os, sys, glob
import pyarrow.parquet as pq
import yaml

def ok(label, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        sys.exit(1)

def warn(msg):
    print(f"[WARN] {msg}")

def main():
    print("=== Config smoke check ===")

    # 1) Load config
    ok("config.yaml exists", os.path.isfile("config.yaml"))
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    # 2) Paths
    paths = cfg.get("paths", {})
    parquet_dir = paths.get("parquet_dir", "data/parquet")
    ref_dir = paths.get("ref_dir", "data/ref")
    out_dir = paths.get("out_dir", "data/out")

    for d in [parquet_dir, ref_dir]:
        ok(f"dir exists: {d}", os.path.isdir(d))

    # ensure out_dir exists
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        print(f"[INFO] created out_dir: {out_dir}")
    ok(f"dir exists: {out_dir}", os.path.isdir(out_dir))

    # 3) Reference files
    pg_file = os.path.join(ref_dir, cfg.get("peer_groups_file", "peer_groups.json"))
    hs_file = os.path.join(ref_dir, cfg.get("hs_names_file", "hs_names.csv"))
    countries_csv = os.path.join(ref_dir, "countries.csv")

    ok("countries.csv present", os.path.isfile(countries_csv))
    ok("peer_groups.json present", os.path.isfile(pg_file))
    ok("hs_names.csv present", os.path.isfile(hs_file))

    # 4) Check datasets & mappings
    cm = cfg.get("columns_map", {})
    ok("columns_map not empty", isinstance(cm, dict) and len(cm) > 0)

    for ds_name, spec in cm.items():
        print("="*80)
        print(f"[DATASET] {ds_name}")
        file_rel = spec.get("file")
        mapping = (spec.get("mapping") or {})
        notes = spec.get("notes")

        if notes:
            print(f"[INFO] notes: {notes}")

        if not file_rel:
            warn("No 'file' specified; skipping file checks.")
            continue

        file_abs = os.path.join(parquet_dir, file_rel)
        ok(f"file exists: {file_rel}", os.path.isfile(file_abs))

        # Read schema with pyarrow
        try:
            pf = pq.ParquetFile(file_abs)
            schema = pf.schema_arrow
            print("[PASS] pyarrow schema read:")
            print(schema)

            # Build a case-insensitive set of column names
            cols_lower = {str(n).lower() for n in schema.names}

            # Validate mapping keys (skip empty targets)
            missing = []
            empties = []
            for canon, actual in mapping.items():
                if actual is None or str(actual).strip() == "":
                    empties.append(canon)
                    continue
                if str(actual).lower() not in cols_lower:
                    missing.append((canon, actual))

            if empties:
                warn(f"mapping has empty targets for: {', '.join(empties)}")
            if missing:
                for canon, actual in missing:
                    warn(f"mapped column not found in file: {canon} -> '{actual}'")
            else:
                if not empties:
                    print("[PASS] all mapped columns found")

        except Exception as e:
            print(f"[FAIL] Unable to read schema for {file_rel}: {e}")
            sys.exit(1)

    print("=== Config smoke complete ===")

if __name__ == "__main__":
    main()
