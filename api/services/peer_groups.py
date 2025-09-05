import os
import pandas as pd
from typing import Dict, Any, Optional, List
from api.settings import settings
from api.normalizers import normalize_iso
from api.peer_group_registry import PeerGroupRegistry
from api.utils.country_codes import get_country_search_codes, convert_numeric_to_alpha3


class PeerGroupsService:
    """Service for peer group analysis and resolution using centralized registry"""
    
    def get_complete_peer_group(self, country: str, peer_group: str = "human", year: int = 2023) -> Dict[str, Any]:
        """Get complete peer group information for a country using centralized registry"""
        
        try:
            # Use registry to get human-readable explanation and peer countries
            explanation = PeerGroupRegistry.get_human_readable_explanation(country, peer_group, year)
            
            # Legacy format for backward compatibility
            return {
                "cluster_id": 0,  # Could be extracted from explanation if needed
                "cluster_name": explanation.get("cluster_name"),
                "peer_countries": explanation["peer_countries"],
                "method": peer_group,
                "year": int(year),
                "methodology": {
                    "name": explanation["methodology_name"],
                    "description": explanation["methodology_description"],
                    "explanation": explanation["explanation_text"]
                }
            }
        
        except Exception as e:
            return {"error": f"Failed to get peer group: {str(e)}"}
    
    def debug_peer_groups(self, country: str) -> Dict[str, Any]:
        """Debug peer group data for a country"""
        
        iso3 = normalize_iso(country)
        if not iso3:
            return {"error": f"unknown country '{country}'"}
        
        # Get metrics latest year
        try:
            from api.data_access import get_metrics_cached, metrics_mtime_key
            df = get_metrics_cached(metrics_mtime_key())
            metrics_latest_year = int(df["year"].max())
        except Exception:
            metrics_latest_year = None
        
        pg_path = settings.PEER_GROUPS_STATISTICAL_PATH
        exists = os.path.isfile(pg_path)
        
        if not exists:
            return {
                "exists": False,
                "metrics_latest_year": metrics_latest_year,
                "peer_groups_years": [],
                "has_country_latest_year": False,
                "fallback_year_used": None,
                "combos": [],
                "cluster_row": [],
            }
        
        try:
            pg_all = pd.read_parquet(pg_path)
            years = sorted({int(y) for y in pg_all.get("year", pd.Series(dtype=int)).dropna().unique().tolist()})
            
            has_exact = False
            fallback_year = None
            pg = pd.DataFrame()
            
            if metrics_latest_year is not None:
                pg_exact = pg_all[pg_all["year"] == metrics_latest_year]
                has_exact = not pg_exact.loc[pg_exact["iso3"] == iso3].empty
                if has_exact:
                    pg = pg_exact.copy()
                    fallback_year = metrics_latest_year
            
            if pg.empty:
                cand = pg_all.loc[pg_all["iso3"] == iso3]
                if not cand.empty:
                    fallback_year = int(cand["year"].max())
                    pg = pg_all.loc[pg_all["year"] == fallback_year].copy()
            
            combos = (
                pg[["method", "k"]].drop_duplicates().sort_values(["method", "k"]).to_dict("records")
                if not pg.empty else []
            )
            
            cluster_row = (
                pg.loc[pg["iso3"] == iso3].head(1).to_dict("records")
                if not pg.empty else []
            )
            
            return {
                "exists": True,
                "metrics_latest_year": metrics_latest_year,
                "peer_groups_years": years,
                "has_country_latest_year": has_exact,
                "fallback_year_used": fallback_year,
                "combos": combos,
                "cluster_row": cluster_row,
            }
            
        except Exception as e:
            return {"exists": True, "error": str(e)}
    
    def get_methodology_explanation(self, method: str, country: str = "CZE", year: int = 2023) -> Dict[str, Any]:
        """Get detailed methodology explanation for frontend display"""
        return PeerGroupRegistry.get_human_readable_explanation(country, method, year)