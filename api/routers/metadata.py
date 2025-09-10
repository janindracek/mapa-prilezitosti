import pandas as pd
from fastapi import APIRouter
import os

from api.config import load_config
from api.services import PeerGroupsService

# Import both systems and choose based on available data
try:
    from api.data.deployment_loader import deployment_data
    DEPLOYMENT_AVAILABLE = os.path.exists("data/deployment/core_trade.csv")
except ImportError:
    DEPLOYMENT_AVAILABLE = False

if not DEPLOYMENT_AVAILABLE:
    from api.data_access import get_metrics_cached, metrics_mtime_key

router = APIRouter()
peer_groups_service = PeerGroupsService()


@router.get("/meta")
def meta():
    """Return metric labels and thresholds from config.yaml"""
    # Re-read on each call so edits to YAML are picked up without restart
    labels, th = load_config()
    return {"metric_labels": labels, "thresholds": th, "status": "ok"}


@router.get("/controls")
def controls_with_labels():
    """
    Return UI controls with metric labels from config.yaml.
    Shape:
      {
        "countries": string[],
        "years": number[],
        "metrics": string[],
        "metric_labels": { [metric]: string }
      }
    """
    # Use appropriate data source
    if DEPLOYMENT_AVAILABLE:
        df = deployment_data.core_trade
    else:
        df = get_metrics_cached(metrics_mtime_key())
    
    countries = sorted(pd.Series(df["partner_iso3"]).dropna().unique().tolist())
    years = sorted(int(y) for y in pd.Series(df["year"]).dropna().unique().tolist())

    metrics = [
        "YoY_export_change",        # S1
        "YoY_partner_share_change", # S2
        "Peer_gap_matching",        # 3b (current setup)
        "Peer_gap_opportunity",     # 3a (opportunity-based)
        "Peer_gap_human",           # 3c (human-defined)
    ]

    labels, _ = load_config()
    return {
        "countries": countries,
        "years": years,
        "metrics": metrics,
        "metric_labels": labels,
    }


@router.get("/peer_groups/complete")
def get_complete_peer_group(country: str, peer_group: str = "human", year: int = 2023):
    """
    Return complete peer group information including all countries in the cluster,
    regardless of whether they have trade data for any specific product.
    """
    return peer_groups_service.get_complete_peer_group(country, peer_group, year)


@router.get("/peer_groups/explanation")
def get_peer_group_explanation(method: str, country: str = "CZE", year: int = 2023):
    """
    Get human-readable peer group methodology explanation for UI display.
    
    Returns:
    - methodology_name: Display name for the methodology
    - methodology_description: Technical description 
    - peer_countries: List of peer country ISO3 codes
    - explanation_text: 2-3 sentence human explanation
    - cluster_name: Cluster name (if applicable)
    - country_count: Number of peer countries
    """
    return peer_groups_service.get_methodology_explanation(method, country, year)


@router.get("/debug/peer_groups")
def debug_peer_groups(country: str):
    """Inspect peer_groups.parquet for a given country.
    Returns: file existence, metrics latest year, available years in parquet,
    whether the country exists in the metrics year, chosen fallback year,
    available (method,k) combos for that year, and the country cluster row.
    """
    return peer_groups_service.debug_peer_groups(country)