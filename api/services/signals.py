import os
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from api.settings import settings
from api.data_access import get_metrics_cached, metrics_mtime_key
from api.normalizers import normalize_iso
from api.formatting import to_json_safe, fmt_value
from api.signals import build_peer_gap, build_yoy_exports, build_yoy_share
from api.data import load_json, resolve_peers
from api.peer_group_methodology import get_methodology_info


class SignalsService:
    """Service for computing and formatting trade signals"""
    
    def __init__(self):
        pass
    
    def get_precomputed_signals(self, hs6: Optional[str] = None, sig_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get precomputed global signals from JSON"""
        data = load_json(settings.UI_SIGNALS_ENRICHED_PATH)
        
        # Apply filters
        if sig_type:
            data = [d for d in data if d.get("type") == sig_type]
        if hs6:
            hs6 = str(hs6).zfill(6)
            data = [d for d in data if d.get("hs6") == hs6]
        
        return data[:max(1, int(limit))]
    
    def compute_country_signals(
        self, 
        country: str, 
        hs6: Optional[str] = None, 
        sig_type: Optional[str] = None,
        limit: int = 10,
        peer_group: str = "all"
    ) -> List[Dict[str, Any]]:
        """Compute signals on-the-fly for a specific country"""
        
        iso3 = normalize_iso(country)
        if not iso3:
            return []
        
        from api.config import load_config
        labels, thresholds = load_config()
        
        df = get_metrics_cached(metrics_mtime_key())
        latest_year = int(df["year"].max())
        
        cur = df[df["year"] == latest_year].copy()
        sub = cur[cur["partner_iso3"] == iso3].copy()
        
        if sub.empty:
            return []
        
        # Get thresholds
        S1 = float(thresholds.get("S1_REL_GAP_MIN", 0.20))
        S2 = float(thresholds.get("S2_YOY_THRESHOLD", 0.30))
        S3 = float(thresholds.get("S3_YOY_SHARE_THRESHOLD", 0.20))
        MAX_TOTAL = int(thresholds.get("MAX_TOTAL", 10))
        MAX_PER_TYPE = int(thresholds.get("MAX_PER_TYPE", 4))
        
        # Build signals
        all_signals = []
        
        # 1. Peer gap signals
        peer_gap_signals = self._build_peer_gap_signals(sub, cur, iso3, latest_year, S1, peer_group)
        all_signals.extend(peer_gap_signals)
        
        # 2. Human peer gap signals
        human_gap_signals = self._build_human_peer_gap_signals(sub, iso3, latest_year, S1, peer_group)
        all_signals.extend(human_gap_signals)
        
        # 3. YoY export change signals
        yoy_exp_signals = build_yoy_exports(sub, S2)
        if not yoy_exp_signals.empty:
            all_signals.append(yoy_exp_signals)
        
        # 4. YoY partner share change signals
        yoy_share_signals = build_yoy_share(sub, S3)
        if not yoy_share_signals.empty:
            all_signals.append(yoy_share_signals)
        
        # Combine and filter
        if all_signals:
            all_sig = pd.concat(all_signals, axis=0, ignore_index=True)
        else:
            all_sig = pd.DataFrame()
            
        if sig_type:
            all_sig = all_sig[all_sig["type"] == sig_type]
        
        return self._format_signals(all_sig, MAX_PER_TYPE, MAX_TOTAL)
    
    def _build_peer_gap_signals(self, sub: pd.DataFrame, cur: pd.DataFrame, country: str, year: int, threshold: float, peer_group: str) -> List[pd.DataFrame]:
        """Build peer gap signals using legacy function (thin wrapper)"""
        try:
            # Use legacy function directly - it handles all methodologies
            df = build_peer_gap(sub, cur, country, year, threshold, peer_group)
            if not df.empty:
                # Re-label peer gap types based on methodology
                df["type"] = df.apply(self._classify_peer_gap_type, axis=1)
                return [df]
            return []
        except Exception as e:
            print(f"Warning: peer gap signal generation failed: {e}")
            return []
    
    def _build_human_peer_gap_signals(self, sub: pd.DataFrame, country: str, year: int, threshold: float, peer_group: str) -> List[pd.DataFrame]:
        """Build human peer gap signals"""
        if peer_group not in ("human", "all"):
            return []
        
        hp_path = Path(settings.PEER_MEDIANS_HUMAN_PATH)
        if not hp_path.is_file():
            return []
        
        try:
            hp = pd.read_parquet(hp_path)
            hp = hp[(hp["year"] == year) & (hp["country_iso3"] == country)][["hs6", "median_peer_share_human"]]
            if hp.empty:
                return []
            
            hsub = sub.merge(hp, on="hs6", how="left")
            hsub["delta_vs_peer_human"] = hsub["podil_cz_na_importu"] - hsub["median_peer_share_human"]
            hsub = hsub[
                (hsub["median_peer_share_human"].notna()) & 
                (hsub["delta_vs_peer_human"] <= -abs(threshold))
            ].copy()
            
            if not hsub.empty:
                hsub["intensity"] = (-hsub["delta_vs_peer_human"]).abs()
                hsub["value"] = hsub["podil_cz_na_importu"]
                hsub["type"] = "Peer_gap_human"
                hsub["peer_group"] = "human"
                hsub["peer_group_label"] = "Peers (human)"
                return [hsub]
        except Exception:
            pass
        
        return []
    
    
    def _classify_peer_gap_type(self, row) -> str:
        """
        Classify peer gap signal type based on peer group methodology.
        
        Three distinct analytical frameworks:
        - opportunity: Markets where similar-opportunity countries succeed
        - kmeans_cosine_hs2_shares: Markets where countries with similar export profiles succeed  
        - default/geographic: Markets where geographic/default peer group succeeds
        """
        method = row.get("method", "default")
        if method == "opportunity":
            return "Peer_gap_opportunity"
        elif method in ["kmeans_cosine_hs2_shares", "hs2_shares"]:
            return "Peer_gap_matching"
        else:
            return "Peer_gap_below_median"
    
    def _format_signals(self, all_sig: pd.DataFrame, max_per_type: int, max_total: int) -> List[Dict[str, Any]]:
        """Format and rank signals for API response"""
        if all_sig.empty:
            return []
        
        # Ensure required columns exist
        cols = [
            "type", "year", "hs6", "partner_iso3", "intensity", "value", "yoy",
            "podil_cz_na_importu", "median_peer_share", "delta_vs_peer",
            "YoY_export_change", "export_cz_to_partner",
            "YoY_partner_share_change", "partner_share_in_cz_exports",
            "peer_group", "peer_group_label", "method",
        ]
        for c in cols:
            if c not in all_sig.columns:
                all_sig[c] = pd.NA
        
        # Rank per type
        out = []
        for t, grp in all_sig.groupby("type"):
            g = grp.sort_values("intensity", ascending=False).head(max_per_type)
            out.extend(g.to_dict(orient="records"))
        
        # Sort by intensity and apply global limit
        out = sorted(out, key=lambda r: float(r.get("intensity", 0)), reverse=True)[:max_total]
        
        # Enrich with names and formatting
        from api.data import load_hs6_names
        hs6_names = load_hs6_names()
        
        for s in out:
            s["hs6"] = str(s.get("hs6", "")).zfill(6)
            s["value_fmt"], s["unit"] = fmt_value(float(s.get("intensity", 0.0)), s.get("type", ""))
            
            # HS6 name
            if hs6_names:
                s["hs6_name"] = hs6_names.get(s["hs6"], s["hs6"])
            
            # Country name
            iso = s.get("partner_iso3")
            if iso:
                try:
                    import pycountry
                    rec = pycountry.countries.get(alpha_3=str(iso))
                    if rec:
                        s["partner_name"] = rec.name
                except Exception:
                    pass
            
            # Add methodology information
            method = s.get("method", "default")
            methodology_info = get_methodology_info(method)
            s["methodology"] = methodology_info
        
        # Make JSON-safe
        return [{k: to_json_safe(v) for k, v in rec.items()} for rec in out]
    
    def get_top_signals(self, country: str, year: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get precomputed top signals for a country"""
        iso3 = normalize_iso(country)
        if not iso3:
            return []
        
        if not os.path.isfile(settings.TOP_SIGNALS_PATH):
            return []
        
        try:
            df = pd.read_parquet(settings.TOP_SIGNALS_PATH)
            if df.empty:
                return []
            
            if year is None:
                year = int(df["year"].max())
            
            out = df[(df["year"] == int(year)) & (df["country_iso3"] == iso3)].copy()
            
            # Keep expected fields
            keep = ["type", "hs6", "partner_iso3", "intensity", "value", "method", "k", "year"]
            for c in keep:
                if c not in out.columns:
                    out[c] = pd.NA
            
            out["hs6"] = out["hs6"].astype(str).str.zfill(6)
            
            # Sort and group by type
            try:
                out = (
                    out.sort_values(["type", "intensity"], ascending=[True, False])
                       .groupby("type", group_keys=False)
                       .head(3)
                )
            except Exception:
                pass
            
            out = out.head(max(1, int(limit)))
            rows = out.to_dict(orient="records")
            
            # Enrich names and formatting
            from api.data import load_hs6_names
            hs6_names = load_hs6_names()
            
            cleaned = []
            for rec in rows:
                rec["hs6"] = str(rec.get("hs6", "")).zfill(6)
                
                # HS6 name
                if hs6_names:
                    rec["hs6_name"] = hs6_names.get(rec["hs6"], rec["hs6"])
                
                # Partner name
                iso_p = rec.get("partner_iso3")
                if iso_p:
                    try:
                        import pycountry
                        pc = pycountry.countries.get(alpha_3=str(iso_p))
                        if pc:
                            rec["partner_name"] = pc.name
                    except Exception:
                        pass
                
                # Value formatting
                try:
                    rec["value_fmt"], rec["unit"] = fmt_value(
                        float(rec.get("intensity", 0.0)), 
                        rec.get("type", "")
                    )
                except Exception:
                    rec["value_fmt"], rec["unit"] = None, None
                
                cleaned.append({k: to_json_safe(v) for k, v in rec.items()})
            
            return cleaned
            
        except Exception:
            return []