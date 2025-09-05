from __future__ import annotations
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("data")
SRC = DATA_DIR / "parquet" / "trade_by_hs2.parquet"
SRC_FALLBACK = DATA_DIR / "parquet" / "trade_by_pair.parquet"
HS2_IMPORTS = DATA_DIR / "parquet" / "trade_by_hs2_imports.parquet"
OUT_PARQUET = DATA_DIR / "out" / "peer_groups.parquet"
OUT_CSV = DATA_DIR / "out" / "peer_groups.csv"

def log(msg): 
    print(f"[peer-groups] {msg}")

def load_data():
    # Fast path: if we have pre-aggregated imports by HS2, use that directly
    if HS2_IMPORTS.exists():
        df = pd.read_parquet(HS2_IMPORTS)
        df.columns = [c.lower() for c in df.columns]
        needed = {"reporter_iso3","hs2","trade_value_usd"}
        if not needed.issubset(df.columns):
            log(f"Pre-aggregated {HS2_IMPORTS.name} missing columns; falling back to other sources.")
        else:
            log(f"Using pre-aggregated imports table: {HS2_IMPORTS.name}")
            # proceed to year handling and return
            year_env = os.getenv("YEAR")
            if "year" in df.columns:
                if year_env:
                    try:
                        year = int(year_env)
                    except:
                        log(f"YEAR='{year_env}' is not an int. Exiting.")
                        sys.exit(2)
                    df = df[df["year"] == year]
                    if df.empty:
                        log(f"ERROR: No rows for YEAR={year} in {HS2_IMPORTS.name}.")
                        sys.exit(2)
                else:
                    year = int(df["year"].max())
                    df = df[df["year"] == year]
                log(f"Using YEAR={year} with {len(df):,} rows (pre-aggregated).")
            else:
                year = None
                log("No 'year' column in pre-aggregated table; treating as single period.")
            df = df[["reporter_iso3","hs2","trade_value_usd"]].copy()
            return df, year

    if not SRC.exists():
        log(f"ERROR: {SRC} not found.")
        sys.exit(2)
    cols = None  # read all; some parquet engines need this
    df = pd.read_parquet(SRC, columns=cols)
    # Normalize column names
    df.columns = [c.lower() for c in df.columns]

    # Early fallback: if this is an exporter-only HS2 table, rebuild imports from pair table
    if {"exporter","hs2","value_usd"}.issubset(df.columns) and "flow" not in df.columns:
        log("Detected exporter-only HS2 table; switching to pair fallback for imports.")
        if not SRC_FALLBACK.exists():
            log(f"ERROR: Fallback {SRC_FALLBACK} not found.")
            sys.exit(2)
        dfp = pd.read_parquet(SRC_FALLBACK)
        dfp.columns = [c.lower() for c in dfp.columns]
        # Accept pair table with or without 'flow'; aggregate by importer×hs2 (and year if present)
        # Normalize value column
        if "value" in dfp.columns and "value_usd" not in dfp.columns:
            dfp = dfp.rename(columns={"value": "value_usd"})
        required_min = {"importer", "hs2", "value_usd"}
        if not required_min.issubset(dfp.columns):
            log("ERROR: pair table lacks required columns (need at least: importer, hs2, value_usd).")
            sys.exit(2)
        # Optional filter to imports if flow exists
        if "flow" in dfp.columns:
            mask = dfp["flow"].astype(str).str.lower().str.startswith("i")
            dfp_use = dfp[mask]
            if dfp_use.empty:
                dfp_use = dfp
        else:
            dfp_use = dfp
        keep_cols = [c for c in ["importer","hs2","value_usd","year"] if c in dfp_use.columns]
        dfp_use = dfp_use[keep_cols].copy()
        group_cols = [c for c in ["importer","hs2","year"] if c in dfp_use.columns]
        dfp_agg = dfp_use.groupby(group_cols, as_index=False)["value_usd"].sum()
        df = dfp_agg.rename(columns={"importer": "reporter_iso3", "value_usd": "trade_value_usd"})
        log(f"Built imports by aggregating pair table: {len(df):,} rows.")

    # Sanity columns
    needed_any = [["reporter_iso3","hs2","trade_value_usd"],
                  ["reporter_iso3","hs2","value"],
                  ["iso3","hs2","trade_value_usd"],
                  ["importer","hs2","value_usd"]]
    for candidate in needed_any:
        if set(candidate).issubset(df.columns):
            base = candidate
            break
    else:
        log(f"ERROR: Could not find required columns in {SRC.name}. "
            f"Need something like {needed_any[0]}. Got: {list(df.columns)[:12]}...")
        sys.exit(2)

    # Map to standard names
    rename = {}
    if "iso3" in base: rename["iso3"] = "reporter_iso3"
    if "value" in base: rename["value"] = "trade_value_usd"
    if "importer" in base: rename["importer"] = "reporter_iso3"
    if "value_usd" in base: rename["value_usd"] = "trade_value_usd"
    df = df.rename(columns=dict(rename))

    # Filter imports if flow column exists
    if "flow" in df.columns:
        f = df["flow"].astype(str).str.lower()
        df = df[f.str.startswith("i")]  # "import" or "imports"
        log(f"Filtered to imports using 'flow' column: {len(df):,} rows remain.")
    else:
        # If file looks exporter-based, try fallback to trade_by_pair.parquet
        if {"exporter","hs2","value_usd"}.issubset(df.columns):
            log("Detected exporter-only aggregation in trade_by_hs2.parquet.")
            if not SRC_FALLBACK.exists():
                log(f"ERROR: Need imports but no 'flow' here. Fallback {SRC_FALLBACK} not found.")
                sys.exit(2)
            log(f"Falling back to {SRC_FALLBACK.name} to build imports by HS2.")
            dfp = pd.read_parquet(SRC_FALLBACK)
            dfp.columns = [c.lower() for c in dfp.columns]
            # Accept pair table with or without 'flow'; aggregate by importer×hs2 (and year if present)
            # Normalize value column
            if "value" in dfp.columns and "value_usd" not in dfp.columns:
                dfp = dfp.rename(columns={"value": "value_usd"})
            required_min = {"importer", "hs2", "value_usd"}
            if not required_min.issubset(dfp.columns):
                log("ERROR: pair table lacks required columns (need at least: importer, hs2, value_usd).")
                sys.exit(2)
            # Optional filter to imports if flow exists
            if "flow" in dfp.columns:
                mask = dfp["flow"].astype(str).str.lower().str.startswith("i")
                dfp_use = dfp[mask]
                if dfp_use.empty:
                    dfp_use = dfp
            else:
                dfp_use = dfp
            keep_cols = [c for c in ["importer","hs2","value_usd","year"] if c in dfp_use.columns]
            dfp_use = dfp_use[keep_cols].copy()
            group_cols = [c for c in ["importer","hs2","year"] if c in dfp_use.columns]
            dfp_agg = dfp_use.groupby(group_cols, as_index=False)["value_usd"].sum()
            df = dfp_agg.rename(columns={"importer": "reporter_iso3", "value_usd": "trade_value_usd"})
            log(f"Built imports by aggregating pair table: {len(df):,} rows.")
        else:
            log("No 'flow' column found; assuming this table is imports-only.")

    # Year handling
    year_env = os.getenv("YEAR")
    if "year" in df.columns:
        if year_env:
            try:
                year = int(year_env)
            except:
                log(f"YEAR='{year_env}' is not an int. Exiting.")
                sys.exit(2)
            df = df[df["year"] == year]
            if df.empty:
                log(f"ERROR: No rows for YEAR={year}.")
                sys.exit(2)
        else:
            year = int(df["year"].max())
            df = df[df["year"] == year]
        log(f"Using YEAR={year} with {len(df):,} rows.")
    else:
        year = None
        log("No 'year' column; treating data as a single period.")

    # Keep only needed cols
    df = df[["reporter_iso3","hs2","trade_value_usd"]].copy()
    return df, year

def build_share_matrix(df: pd.DataFrame) -> pd.DataFrame:
    # Defensive cleaning: ensure numeric values and normalized keys
    df = df.copy()
    df["reporter_iso3"] = df["reporter_iso3"].astype(str).str.upper()
    df["hs2"] = df["hs2"].astype(str)
    df["trade_value_usd"] = pd.to_numeric(df["trade_value_usd"], errors="coerce").fillna(0.0)

    piv = df.pivot_table(
        index="reporter_iso3",
        columns="hs2",
        values="trade_value_usd",
        aggfunc="sum",
        fill_value=0.0,
    )
    piv = piv.sort_index()
    row_sums = piv.sum(axis=1)
    piv = piv[row_sums > 0]
    shares = piv.div(piv.sum(axis=1), axis=0).fillna(0.0)
    return shares

def kmeans_cosine(X: np.ndarray, k: int, max_iter: int = 200, seed: int = 42):
    """
    Cosine k-means:
    - assign by max cosine similarity
    - centroids = mean of assigned points, then L2-normalized
    Returns labels (n,) and centroids (k,d).
    """
    rng = np.random.default_rng(seed)
    # Normalize rows to unit norm (avoid div by zero)
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms==0] = 1.0
    Xn = X / norms

    # init: choose k distinct rows
    if k > len(Xn):
        raise ValueError(f"k={k} > number of countries={len(Xn)}")
    init_idx = rng.choice(len(Xn), size=k, replace=False)
    C = Xn[init_idx].copy()

    labels = np.zeros(len(Xn), dtype=int)
    for it in range(max_iter):
        # assign by cosine similarity (dot product on unit vectors)
        sims = Xn @ C.T                  # (n,k)
        new_labels = sims.argmax(axis=1) # highest similarity
        if np.array_equal(new_labels, labels) and it > 0:
            break
        labels = new_labels

        # recompute centroids
        for j in range(k):
            members = Xn[labels == j]
            if len(members) == 0:
                # re-seed empty cluster
                C[j] = Xn[rng.integers(0, len(Xn))]
            else:
                v = members.mean(axis=0)
                n = np.linalg.norm(v)
                C[j] = v / (n if n > 0 else 1.0)

    return labels, C

def main():
    df, year = load_data()
    shares = build_share_matrix(df)

    k = int(os.getenv("PEER_K", "10"))
    log(f"Clustering {len(shares)} countries into K={k} clusters (cosine k-means).")
    labels, _ = kmeans_cosine(shares.values, k=k, max_iter=200, seed=42)

    # Build output
    out = pd.DataFrame({
        "iso3": shares.index,
        "cluster": labels
    }).sort_values(["cluster","iso3"]).reset_index(drop=True)
    out["method"] = "kmeans_cosine_hs2_shares"
    out["k"] = k
    if year is not None:
        out["year"] = year

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PARQUET, index=False)
    out.to_csv(OUT_CSV, index=False)
    log(f"Wrote: {OUT_PARQUET}")
    log(f"Wrote: {OUT_CSV}")

    # Simple diagnostic: top 12 nearest to CZE (if present)
    if "CZE" in shares.index:
        X = shares.values
        # cosine similarity on L2-normalized rows
        Xn = X / np.clip(np.linalg.norm(X, axis=1, keepdims=True), 1e-12, None)
        idx = shares.index.get_loc("CZE")
        sims = Xn @ Xn[idx]
        order = np.argsort(-sims)
        peers = [(shares.index[i], float(sims[i])) for i in order[:12]]
        print("\nClosest to CZE by cosine similarity (beta, structural imports @ HS2):")
        for iso, s in peers:
            print(f"  {iso:>3}  sim={s:0.4f}")
        # Tiny assertions as a smoke test
        assert len(out) >= k, "Too few countries for chosen K."
        assert (out["iso3"] == "CZE").any(), "CZE missing from results."
        log("Smoke checks passed.")
    else:
        log("CZE not found in data; skipping CZE diagnostic.")

if __name__ == "__main__":
    main()
