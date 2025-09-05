from typing import Optional
import pycountry

def normalize_iso(code: str) -> Optional[str]:
    """
    Accepts ISO2, ISO3, or common aliases; returns ISO3 or None if not resolvable.
    
    Handles common country code aliases like GER→DEU, UK→GBR
    """
    if not code:
        return None
    c = code.strip().upper()
    
    # Common aliases mapping (most frequently used non-standard codes)
    COUNTRY_ALIASES = {
        'GER': 'DEU',  # Germany (commonly used instead of DEU)
        'UK': 'GBR',   # United Kingdom (commonly used instead of GBR)
        'USA': 'USA',  # United States (already ISO3, but commonly expected)
    }
    
    # Check aliases first
    if c in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[c]
    
    # ISO3 direct lookup
    if len(c) == 3:
        rec = pycountry.countries.get(alpha_3=c)
        return rec.alpha_3 if rec else None
        
    # ISO2 lookup
    if len(c) == 2:
        rec = pycountry.countries.get(alpha_2=c)
        if rec:
            return getattr(rec, "alpha_3", None)
            
    # By English name (best-effort)
    rec = pycountry.countries.get(name=c.title())
    if rec:
        return getattr(rec, "alpha_3", None)
        
    return None

def norm_hs2(v: Optional[str | int]) -> Optional[str]:
    """
    Normalize HS2: keep digits only, take first two, pad to 2 chars or return None.
    """
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    s = "".join(ch for ch in s if ch.isdigit())[:2]
    return s.zfill(2) if s else None
