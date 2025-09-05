import os
import json
import pandas as pd
from typing import Dict, Optional, Set
from api.settings import settings


def load_json(path: str) -> list:
    """Load JSON file with error handling"""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def load_hs6_names() -> Dict[str, str]:
    """Load HS6 product names from reference CSV"""
    if not os.path.isfile(settings.HS6_REF_PATH):
        return {}
    
    try:
        df = pd.read_csv(settings.HS6_REF_PATH)
        return dict(zip(df["hs6"], df["name"]))
    except Exception:
        return {}


def load_peer_groups(peer_type: str, year: int, country_iso3: str) -> Optional[pd.DataFrame]:
    """Load peer group data based on type"""
    
    # Choose data source based on peer group type
    peer_type = peer_type.strip().lower()
    if peer_type == "human":
        path = settings.PEER_GROUPS_HUMAN_PATH
    elif peer_type == "opportunity":
        path = settings.PEER_GROUPS_OPPORTUNITY_PATH
    elif peer_type == "trade_structure":
        path = settings.PEER_GROUPS_HS2_PATH
    else:
        path = settings.PEER_GROUPS_STATISTICAL_PATH
    
    if not os.path.isfile(path):
        return None
    
    try:
        df = pd.read_parquet(path)
        if df.empty:
            return None
        
        # All peer group data now uses consistent iso3 column with alpha-3 codes
        iso_col = 'iso3'
        
        # Validate that the expected column exists
        if iso_col not in df.columns:
            print(f"Warning: Expected column '{iso_col}' not found in {peer_type} data. Available columns: {df.columns.tolist()}")
            return None
        
        # All peer group types now use alpha-3 codes
        search_codes = [country_iso3]
        
        # Handle year filtering - trade_structure doesn't have year column
        if "year" in df.columns:
            # Filter by year and find country
            year_data = df[df["year"] == year]
            found_country_code = None
            
            for code in search_codes:
                if not year_data.loc[year_data[iso_col].astype(str) == str(code)].empty:
                    found_country_code = str(code)
                    break
            
            if found_country_code is None:
                # Try fallback years
                for code in search_codes:
                    country_data = df.loc[df[iso_col].astype(str) == str(code)]
                    if not country_data.empty:
                        fallback_year = int(country_data["year"].max())
                        year_data = df[df["year"] == fallback_year]
                        found_country_code = str(code)
                        break
            
            if found_country_code is None:
                return None
                
            return year_data
        else:
            # No year filtering for trade_structure - return all data
            return df
        
    except Exception:
        return None


def resolve_peers(country_iso3: str, year: int, peer_group: Optional[str]) -> Optional[Set[str]]:
    """Resolve peer countries for a given country/year/peer_group"""
    
    if not peer_group:
        return None
        
    peer_data = load_peer_groups(peer_group, year, country_iso3)
    if peer_data is None or peer_data.empty:
        return None
    
    try:
        peer_req = peer_group.strip().lower()
        
        # Handle trade_structure peer groups (different structure)
        if peer_req == "trade_structure":
            # Find Czech Republic by iso3 code
            country_row = peer_data.loc[peer_data["iso3"] == country_iso3].head(1)
            if country_row.empty:
                return None
            
            cluster_id = country_row.iloc[0]["cluster"]
            peer_codes = peer_data.loc[peer_data["cluster"] == cluster_id, "iso3"].dropna().unique().tolist()
            
            # Exclude Czech Republic from peer countries (can't trade with itself)
            peer_codes = [code for code in peer_codes if code != country_iso3]
            return set(peer_codes)
        
        # Handle other peer group types - all now use consistent alpha-3 format
        iso_col = 'iso3'
        
        # Handle method:k format
        if ":" in peer_req:
            method, k = peer_req.split(":", 1)
            method = method.strip()
            try:
                k_str = str(int(float(k.strip())))
            except Exception:
                return None
            peer_data = peer_data[
                (peer_data["method"].astype(str).str.lower() == method) & 
                (peer_data["k"].astype(str) == k_str)
            ]
        elif peer_req in ("default", "all", ""):
            if "method" in peer_data.columns:
                peer_data = peer_data[peer_data["method"].astype(str).str.lower() == "default"]
        
        # Find country's cluster using alpha-3 code
        country_row = peer_data.loc[peer_data[iso_col] == country_iso3].head(1)
        if country_row.empty:
            return None
        
        cluster_id = country_row.iloc[0]["cluster"]
        peers = peer_data.loc[peer_data["cluster"] == cluster_id, iso_col].dropna().unique().tolist()
        
        # Exclude Czech Republic from peer countries (can't trade with itself)
        peers = [code for code in peers if code != country_iso3]
        return set(peers)
        
    except Exception:
        return None