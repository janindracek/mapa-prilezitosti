from __future__ import annotations
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("data")
PAIR = DATA_DIR / "parquet" / "trade_by_pair.parquet"
OUT_PARQUET = DATA_DIR / "out" / "peer_groups_opportunity.parquet"
OUT_CSV = DATA_DIR / "out" / "peer_groups_opportunity.csv"
FEAT_PARQUET = DATA_DIR / "out" / "peer_features_opportunity.parquet"
FEAT_CSV = DATA_DIR / "out" / "peer_features_opportunity.csv"

def log(msg): print(f"[peer-opp] {msg}")

# --- math helpers ---
def safe_div(a, b, eps=1e-12):
    return a / np.clip(b, eps, None)

def truncated_svd(X: np.ndarray, n_components: int):
    # center columns, then SVD and take top components
    X = X.astype(float, copy=False)
    col_mean = X.mean(axis=0, keepdims=True)
    Xc = X - col_mean
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    k = max(1, min(n_components, min(U.shape[1], Vt.shape[0])))
    return U[:, :k] * S[:k], S[:k], Vt[:k, :], col_mean

def kmeans_cosine(X: np.ndarray, k: int, max_iter: int = 200, seed: int = 42):
    rng = np.random.default_rng(seed)
    # L2-normalize rows
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    Xn = X / norms
    if k > len(Xn):
        raise ValueError(f"k={k} > number of rows={len(Xn)}")
    C = Xn[rng.choice(len(Xn), size=k, replace=False)].copy()
    labels = np.zeros(len(Xn), dtype=int)
    for it in range(max_iter):
        sims = Xn @ C.T
        new_labels = sims.argmax(axis=1)
        if it > 0 and np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for j in range(k):
            members = Xn[labels == j]
            if len(members) == 0:
                C[j] = Xn[rng.integers(0, len(Xn))]
            else:
                v = members.mean(axis=0)
                n = np.linalg.norm(v)
                C[j] = v / (n if n > 0 else 1.0)
    return labels, C

# --- data loading ---
def load_pair(year: int | None, window: int = 4) -> tuple[pd.DataFrame, int]:
    if not PAIR.exists():
        log(f"ERROR: {PAIR} not found.")
        sys.exit(2)
    df = pd.read_parquet(PAIR)
    df.columns = [c.lower() for c in df.columns]
    # normalize names from BACI (i,j,k,t,v) if present
    ren = {}
    if "i" in df.columns: ren["i"] = "exporter"
    if "j" in df.columns: ren["j"] = "importer"
    if "k" in df.columns: ren["k"] = "hs6"
    if "t" in df.columns: ren["t"] = "year"
    if "v" in df.columns: ren["v"] = "value_usd"
    if ren: df = df.rename(columns=ren)

    needed = {"year","exporter","importer","hs6","value_usd"}
    if not needed.issubset(df.columns):
        log(f"ERROR: pair table missing columns. Need {needed}, got {set(df.columns)}")
        sys.exit(2)

    # types
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    df["exporter"] = df["exporter"].astype(str)
    df["importer"] = df["importer"].astype(str)
    df["hs6"] = df["hs6"].astype(str)
    df["value_usd"] = pd.to_numeric(df["value_usd"], errors="coerce").fillna(0.0)

    # choose target year and window
    y_target = year if year is not None else int(df["year"].max())
    y_min = y_target - (window - 1)
    df = df[(df["year"] >= y_min) & (df["year"] <= y_target)].copy()
    if df.empty:
        log(f"ERROR: no data in window {y_min}-{y_target}")
        sys.exit(2)
    log(f"Using years {y_min}-{y_target} (target={y_target}) with {len(df):,} rows")
    return df, y_target, y_min

# --- feature builders ---
def build_hs6_shares(df: pd.DataFrame, y_target: int, top_hs6: int = 500) -> tuple[pd.DataFrame, list[str]]:
    # Target-year totals by importer×hs6
    cur = df[df["year"] == y_target].groupby(["importer","hs6"], as_index=False)["value_usd"].sum()
    # limit dimensionality: take top HS6 by global import in target year
    top_codes = (cur.groupby("hs6")["value_usd"].sum()
                   .sort_values(ascending=False).head(top_hs6).index.tolist())
    cur = cur[cur["hs6"].isin(top_codes)].copy()
    piv = cur.pivot_table(index="importer", columns="hs6", values="value_usd", aggfunc="sum", fill_value=0.0)
    row_sum = piv.sum(axis=1)
    piv = piv[row_sum > 0]
    shares = piv.div(piv.sum(axis=1), axis=0).fillna(0.0)
    return shares, top_codes

def build_hs6_cagr(df: pd.DataFrame, y_min: int, y_target: int, hs6_keep: list[str]) -> pd.DataFrame:
    # 3y CAGR over window for each importer×hs6
    # sum per year then compute CAGR between y_min and y_target
    g = (df[df["hs6"].isin(hs6_keep)]
           .groupby(["importer","hs6","year"], as_index=False)["value_usd"].sum())
    base = g[g["year"] == y_min].set_index(["importer","hs6"])["value_usd"]
    last = g[g["year"] == y_target].set_index(["importer","hs6"])["value_usd"]
    idx = sorted(set(base.index).union(set(last.index)))
    b = base.reindex(idx).fillna(0.0).values
    l = last.reindex(idx).fillna(0.0).values
    years = max(1, (y_target - y_min))
    cagr = (np.power(safe_div(l + 1.0, b + 1.0), 1.0 / years) - 1.0)  # +1 smoothing
    i_imp = [i for (i,_) in idx]
    i_hs6 = [h for (_,h) in idx]
    df_cagr = pd.DataFrame({"importer": i_imp, "hs6": i_hs6, "cagr": cagr})
    piv = df_cagr.pivot_table(index="importer", columns="hs6", values="cagr", aggfunc="mean", fill_value=0.0)
    # clip extreme values
    piv = piv.clip(lower=-1.0, upper=1.0)
    # align columns to hs6_keep order
    for code in hs6_keep:
        if code not in piv.columns: piv[code] = 0.0
    piv = piv[hs6_keep]
    return piv

def build_partner_openness(df: pd.DataFrame, y_target: int) -> pd.DataFrame:
    cur = df[df["year"] == y_target]
    grp = cur.groupby(["importer","exporter"], as_index=False)["value_usd"].sum()
    # shares per importer
    tot = grp.groupby("importer")["value_usd"].transform("sum")
    grp["share"] = safe_div(grp["value_usd"].values, tot.values)
    # HHI = sum(share^2), top_share, n_partners (normalized)
    feats = (grp.groupby("importer")
                .agg(hhi=("share", lambda s: float(np.sum(np.square(s)))),
                     top_share=("share", "max"),
                     n_partners=("exporter", "nunique"))
                .reset_index())
    # normalize n_partners to 0..1 by dividing by max
    maxp = max(1, int(feats["n_partners"].max()))
    feats["n_partners_norm"] = feats["n_partners"] / maxp
    feats = feats.drop(columns=["n_partners"])
    return feats.set_index("importer")

# --- main ---
def main():
    year_env = os.getenv("YEAR")
    year = int(year_env) if year_env else None
    k = int(os.getenv("PEER_K", "10"))
    window = int(os.getenv("WINDOW_YEARS", "4"))
    comps_shares = int(os.getenv("PCA_SHARES", "40"))
    comps_cagr = int(os.getenv("PCA_CAGR", "20"))
    top_hs6 = int(os.getenv("TOP_HS6", "500"))

    df, y_target, y_min = load_pair(year, window=window)

    # features: shares (HS6), growth (CAGR), partner openness
    shares, hs6_keep = build_hs6_shares(df, y_target, top_hs6=top_hs6)
    cagr = build_hs6_cagr(df, y_min, y_target, hs6_keep=hs6_keep)
    openx = build_partner_openness(df, y_target)

    # align indices
    idx = sorted(set(shares.index) & set(cagr.index) & set(openx.index))
    shares = shares.loc[idx]
    cagr = cagr.loc[idx]
    openx = openx.loc[idx]

    # SVD (PCA-like) compression
    Zs, Ss, Vts, mu_s = truncated_svd(shares.values, n_components=min(comps_shares, shares.shape[1]-1 if shares.shape[1]>1 else 1))
    Zg, Sg, Vtg, mu_g = truncated_svd(cagr.values, n_components=min(comps_cagr, cagr.shape[1]-1 if cagr.shape[1]>1 else 1))

    # concatenate features: [shares_pca | cagr_pca | openness]
    X = np.hstack([Zs, Zg, openx[["hhi","top_share","n_partners_norm"]].values])
    # guard against NaN/inf
    X = np.nan_to_num(X, copy=False)

    log(f"Countries in matrix: {len(idx)}; dim={X.shape[1]} (shares_pca={Zs.shape[1]}, cagr_pca={Zg.shape[1]}, openness=3)")
    labels, C = kmeans_cosine(X, k=k, max_iter=200, seed=42)

    out = pd.DataFrame({"iso": idx, "cluster": labels})
    out["method"] = "kmeans_cosine_opportunity(HS6_shares+CAGR+openness)"
    out["k"] = k
    out["year"] = y_target
    # save
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PARQUET, index=False)
    out.to_csv(OUT_CSV, index=False)
    log(f"Wrote: {OUT_PARQUET}")
    log(f"Wrote: {OUT_CSV}")

    # save feature table for inspection
    feat = pd.DataFrame(index=idx)
    # keep the compressed components (small) and openness
    for j in range(Zs.shape[1]):
        feat[f"share_pc{j+1}"] = Zs[:, j]
    for j in range(Zg.shape[1]):
        feat[f"cagr_pc{j+1}"] = Zg[:, j]
    feat[["hhi","top_share","n_partners_norm"]] = openx[["hhi","top_share","n_partners_norm"]]
    feat = feat.reset_index().rename(columns={"index":"iso"})
    feat.to_parquet(FEAT_PARQUET, index=False)
    feat.to_csv(FEAT_CSV, index=False)
    log(f"Wrote features: {FEAT_PARQUET} and {FEAT_CSV}")

    # simple diagnostic: nearest neighbors to Czechia by cosine in X
    iso_idx = {s:i for i,s in enumerate(idx)}
    cand_keys = ["203","CZE"]  # BACI often uses numeric ISO or alpha-3; try both
    for key in cand_keys:
        if key in iso_idx:
            i = iso_idx[key]
            Xn = X / np.clip(np.linalg.norm(X, axis=1, keepdims=True), 1e-12, None)
            sims = Xn @ Xn[i]
            order = np.argsort(-sims)
            log(f"Closest 15 to {key} (opportunity features):")
            for t in order[:15]:
                print(f"  {idx[t]:>4}  sim={float(sims[t]):.4f}  cluster={labels[t]}")
            break
    # smoke checks
    assert len(out["cluster"].unique()) <= k, "More clusters than K?"
    assert len(out) >= k, "Too few countries."
    log("Smoke checks passed.")

if __name__ == "__main__":
    main()
