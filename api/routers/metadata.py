import pandas as pd
from fastapi import APIRouter

from api.config import load_config
from api.services import PeerGroupsService
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
    # /controls only needs the distinct countries + years. Read just those two
    # columns (the UI hits this on every load) instead of the full fact frame.
    import pandas as _pd
    from api.settings import settings as _settings
    cdf = _pd.read_parquet(_settings.CORE_TRADE_PATH, columns=["partner_iso3", "year"],
                           dtype_backend="pyarrow")
    countries = sorted(_pd.Series(cdf["partner_iso3"]).dropna().unique().tolist())
    years = sorted(int(y) for y in _pd.Series(cdf["year"]).dropna().unique().tolist())

    # Live signal types (opportunity retired in M3).
    metrics = [
        "YoY_export_change",
        "YoY_partner_share_change",
        "Peer_gap_matching",
        "Peer_gap_human",
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