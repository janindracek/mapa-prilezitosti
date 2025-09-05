from __future__ import annotations
import os
import pandas as pd

def build_peer_gap(sub: pd.DataFrame,
                   cur: pd.DataFrame,
                   country_iso3: str,
                   latest_year: int,
                   S1: float,
                   peer_group: str | None = "all") -> pd.DataFrame:
    """
    Vrací DataFrame se sloupci jako v původním kódu (intensity, value, yoy, type, peer_group, peer_group_label, ...)
    pro signál 'Peer_gap_below_median'.
    """
    import pandas as _pd
    peer_gap_blocks: list[pd.DataFrame] = []

    have_default_cols = ("median_peer_share" in sub.columns) and ("delta_vs_peer" in sub.columns)
    wants_all_groups = (peer_group is None) or (peer_group == "all")

    # A) default peer metriky, pokud jsou už v sub
    if have_default_cols and (wants_all_groups or peer_group == "default"):
        _pg = sub[
            sub["median_peer_share"].notna()
            & sub["delta_vs_peer"].notna()
            & (sub["delta_vs_peer"] <= -abs(S1))
        ].copy()
        if not _pg.empty:
            _pg["intensity"] = (-_pg["delta_vs_peer"]).abs()
            _pg["value"] = _pg["delta_vs_peer"]
            _pg["yoy"] = None
            _pg["type"] = "Peer_gap_below_median"
            _pg["peer_group"] = "default"
            _pg["peer_group_label"] = "Peers (default)"
            peer_gap_blocks.append(_pg)

    # B) dopočet z peer_groups.parquet (pokud existuje) a je požadován
    pg_path = "data/out/peer_groups_statistical.parquet"
    if os.path.isfile(pg_path) and (wants_all_groups or (peer_group and peer_group != "default")):
        try:
            pg = pd.read_parquet(pg_path)
            pg = pg[pg["year"] == latest_year].copy()

            combos_all = pg[["method", "k"]].drop_duplicates().to_records(index=False).tolist()

            def pick_combos(allc):
                if wants_all_groups:
                    return allc[:3]
                if ":" in str(peer_group):
                    m, ks = str(peer_group).split(":", 1)
                    try:
                        ks = int(ks)
                    except Exception:
                        pass
                    return [(m, ks)]
                m = str(peer_group)
                rows = pg[pg["method"] == m]
                if not rows.empty:
                    return [(m, int(rows["k"].iloc[0]))]
                return []

            for (m, k) in pick_combos(combos_all):
                sel_mk = pg[(pg["method"] == m) & (pg["k"] == k)].copy()
                if sel_mk.empty:
                    continue

                target_rows = sel_mk.loc[sel_mk["iso3"] == country_iso3]
                if target_rows.empty:
                    continue
                cluster_id = target_rows["cluster"].iloc[0]

                peers_series = pd.Series(sel_mk.loc[sel_mk["cluster"] == cluster_id, "iso3"])
                peers_list = peers_series.dropna().astype(str).tolist()
                peers_wo = [p for p in peers_list if p != country_iso3]
                if not peers_wo:
                    continue

                if "podil_cz_na_importu" not in cur.columns:
                    continue

                peers_df = cur[cur["partner_iso3"].isin(peers_wo)].copy()
                if peers_df.empty:
                    continue

                med = peers_df.groupby("hs6", as_index=True)["podil_cz_na_importu"].median()
                med.name = "median_peer_share"

                joined = sub.merge(med, on="hs6", how="left")
                joined["delta_vs_peer"] = joined["podil_cz_na_importu"] - joined["median_peer_share"]

                cand = joined[(joined["median_peer_share"].notna()) & (joined["delta_vs_peer"] <= -abs(S1))].copy()
                if cand.empty:
                    continue

                cand["intensity"] = (-cand["delta_vs_peer"]).abs()
                cand["value"] = cand["delta_vs_peer"]
                cand["yoy"] = None
                # set specific type by method name (UI needs 3 distinct peer types)
                m_low = str(m).lower()
                if "opportunity" in m_low:
                    cand["type"] = "Peer_gap_opportunity"
                elif "hs2_shares" in m_low or "kmeans_cosine_hs2_shares" in m_low:
                    cand["type"] = "Peer_gap_matching"
                else:
                    cand["type"] = "Peer_gap_below_median"
                cand["peer_group"] = f"{m}:{k}"
                cand["peer_group_label"] = f"Peers ({m}, k={k})"
                peer_gap_blocks.append(cand)
        except Exception:
            # fail-soft
            pass

    return _pd.concat(peer_gap_blocks, axis=0, ignore_index=True) if peer_gap_blocks else _pd.DataFrame(columns=sub.columns)


def build_yoy_exports(sub: pd.DataFrame, S2: float) -> pd.DataFrame:
    yoy_exp = sub[
        (sub["YoY_export_change"].notna()) &
        (sub["export_cz_to_partner"].notna()) &
        (sub["YoY_export_change"].abs() >= abs(S2))
    ].copy()
    if yoy_exp.empty:
        return yoy_exp
    yoy_exp["intensity"] = yoy_exp["YoY_export_change"].abs()
    yoy_exp["value"] = yoy_exp["export_cz_to_partner"]
    yoy_exp["yoy"] = yoy_exp["YoY_export_change"]
    yoy_exp["type"] = "YoY_export_change"
    return yoy_exp


def build_yoy_share(sub: pd.DataFrame, S3: float) -> pd.DataFrame:
    yoy_share = sub[
        (sub["YoY_partner_share_change"].notna()) &
        (sub["partner_share_in_cz_exports"].notna()) &
        (sub["YoY_partner_share_change"].abs() >= abs(S3))
    ].copy()
    if yoy_share.empty:
        return yoy_share
    yoy_share["intensity"] = yoy_share["YoY_partner_share_change"].abs()
    yoy_share["value"] = yoy_share["partner_share_in_cz_exports"]
    yoy_share["yoy"] = yoy_share["YoY_partner_share_change"]
    yoy_share["type"] = "YoY_partner_share_change"
    return yoy_share
