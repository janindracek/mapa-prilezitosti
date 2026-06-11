from fastapi import APIRouter

from api.settings import settings
from api.insights_text import generate_insights, extract_context
from api.data_access import query_core

router = APIRouter()


@router.get("/insights")
def get_insights(importer: str, hs6: str, year: int):
    """Generate the narrative insight text for an (importer, hs6, year)."""
    text = generate_insights(settings.METRICS_PARQUET_PATH, importer, hs6, year)
    return {"insight": text}


@router.get("/insights_data")
def get_insights_data(importer: str, hs6: str, year: int):
    """Structured KeyData tiles for an (importer, hs6, year)."""
    df = query_core(
        ["year", "partner_iso3", "hs6", "import_partner_total",
         "export_cz_to_partner", "export_cz_total_for_hs6"],
        hs6=hs6,
    )
    context = extract_context(df, importer, hs6, year, lookback=5)
    return {
        "c_import_total": context.get("imp_last"),          # partner's total imports
        "cz_share_in_c": context.get("pen_imp"),            # CZ share of partner imports
        "median_peer_share": context.get("pen_med"),        # peer benchmark (request-time median)
        "import_yoy_change": context.get("imp_yoy_change"),  # partner's import YoY %
        "cz_to_c": context.get("cz_to_imp_last"),           # CZ export to partner
        "cz_world_total": context.get("cz_global_last"),    # CZ total world export for HS6
        "cz_delta_pct": context.get("cz_export_yoy"),       # CZ's own export YoY % (fixed: was a dup of import YoY)
    }
