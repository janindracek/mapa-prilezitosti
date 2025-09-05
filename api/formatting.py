from typing import Tuple

def to_json_safe(v):
    """
    Convert pandas/NumPy NaN/Inf and similar to JSON-safe Python values (None/float/int/str).
    Importy řešíme uvnitř, aby modul neměl tvrdé závislosti.
    """
    try:
        import math
        import pandas as _pd  # type: ignore
        if v is None:
            return None
        # pandas NA/NaN/NAType a podobně
        if _pd.isna(v):
            return None
        # floats: nan/inf
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return None
            return float(v)
    except Exception:
        pass
    return v

def fmt_value(val: float, metric: str = "") -> Tuple[str, str]:
    """
    Vrací (formatted_string, unit). Jednoduchá heuristika podle typu metriky.
    """
    if val is None:
        return ("", "")
    try:
        if "share" in metric or "delta" in metric:
            return (f"{val*100:.1f}%", "%")
        if "YoY" in metric:
            return (f"{val*100:.1f}%", "%")
        if abs(val) >= 1_000_000:
            return (f"{val/1_000_000:.1f}M", "USD")
        if abs(val) >= 1_000:
            return (f"{val/1_000:.1f}k", "USD")
        return (f"{val:.2f}", "")
    except Exception:
        # Defenzivně: kdyby přišel nečíselný vstup, vrať prosté str()
        return (str(val), "")
