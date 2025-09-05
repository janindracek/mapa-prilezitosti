import os
from typing import Tuple, Dict, Any

# Defaultní popisky metrik a prahy – držme je na jednom místě
DEFAULT_METRIC_LABELS: Dict[str, str] = {
    "podil_cz_na_importu": "CZ share of partner imports",
    "YoY_export_change": "YoY change in CZ→partner exports",
    "partner_share_in_cz_exports": "Partner share in CZ exports (by HS6)",
    "YoY_partner_share_change": "YoY change in partner share",
    "median_peer_share": "Peer-group median share",
    "delta_vs_peer": "Gap vs. peer median (CZ − peer)",
}
DEFAULT_THRESHOLDS: Dict[str, float] = {
    "MIN_EXPORT_USD": 100_000,
    "MIN_IMPORT_USD": 5_000_000,
    "S1_REL_GAP_MIN": 0.20,
    "S2_YOY_THRESHOLD": 0.30,
    "S3_YOY_SHARE_THRESHOLD": 0.20,
    "MAX_TOTAL_SIGNALS": 10,
    "MAX_PER_TYPE": 4,
}
CFG_PATH = "data/config.yaml"

def _safe_load_yaml(path: str) -> Dict[str, Any]:
    """Bezpečně načti YAML; když chybí pyyaml nebo soubor, vrať prázdno."""
    if not os.path.isfile(path):
        return {}
    try:
        import yaml  # import uvnitř funkce, aby app běžela i bez pyyaml
    except Exception:
        return {}
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def load_config() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Vrať (metric_labels, thresholds) s přepsáním z YAML, pokud existuje."""
    labels = DEFAULT_METRIC_LABELS.copy()
    th = DEFAULT_THRESHOLDS.copy()
    cfg = _safe_load_yaml(CFG_PATH)
    if cfg:
        labels.update(cfg.get("metric_labels") or {})
        th.update(cfg.get("thresholds") or {})
    return labels, th
