import argparse
from typing import Optional, Dict, Any
import pandas as pd
import os, json, logging
from urllib import request, error as urlerror

# Trade values in BACI source data are in thousands of USD, need 1000x scaling
# CORRECTED: BACI values are actually in thousands, confirmed by total Czech exports matching official stats
TRADE_SCALE = int(os.environ.get("TRADE_UNITS_SCALE", "1000"))

def _load_hs6_labels() -> Dict[str, str]:
    """Load HS6 product descriptions from JSON file."""
    try:
        # Try to load from the UI public directory first
        ui_path = os.path.join(os.path.dirname(__file__), "../ui/public/ref/hs6_labels.json")
        if os.path.exists(ui_path):
            with open(ui_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback to UI src directory
        src_path = os.path.join(os.path.dirname(__file__), "../ui/src/ref/hs6_labels.json")
        if os.path.exists(src_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to load HS6 labels: {e}")
    
    return {}

# Load HS6 labels once at module level
_HS6_LABELS = _load_hs6_labels()

def _fmt_usd(x: float) -> str:
    if x is None or pd.isna(x): return "n/a"
    # M4b: values are already in USD (scaled once in etl/01) — do NOT re-scale.
    actual_usd = x
    if actual_usd >= 1e9: return f"{actual_usd/1e9:.1f} mld. USD"
    if actual_usd >= 1e6: return f"{actual_usd/1e6:.1f} mil. USD"
    return f"{actual_usd:,.0f} USD".replace(",", " ")

def _cagr(series: pd.Series) -> Optional[float]:
    s = series.dropna()
    if len(s) < 2: return None
    first, last = s.iloc[0], s.iloc[-1]
    n = len(s) - 1
    if first <= 0 or n <= 0: return None
    return (last / first) ** (1/n) - 1



_INSIGHTS_SYSTEM = (
    "Jsi novinář FT pokrývající byznys a ekonomiku vybrané země. Specializuješ se a porozumění trhu vybraného produktu"
    "Piš česky, poutavě a věcně. "
    "Pracuj POUZE s poskytnutými daty a daty získanými z webu. Pokud nějaký údaj chybí nebo je nejistý, napiš 'neznámé' nebo 'málo dat'. "
    "Výstup strukturovaně: "
    "Uveď HS6 kód (a název, pokud je v promptu). "
    "1) 'Kontext:' příběh vysvětlení kontextu země a produktu, "
    "1) 'Potenciál pro export z Česka (nízký/střední/vysoký): …' + 2–3 konkrétní důvody, "
    "2) 'Bariéry:' 2–4 stručné body, "
    "3) 'To‑do (30–60 dní):' 3–5 akčních kroků "
    "4) 'Poznámky k datům:' 1–2 věty o limitech dat. "
    "Bez marketingových frází, profesionální insight. Maximálně ~3000 znaků mimo odrážky."
)


def _llm_generate(prompt: str, model: str = None, max_tokens: int = 1200) -> Optional[str]:
    """
    Calls Anthropic's Messages API (Claude) using stdlib only — no SDK dependency,
    so the deploy stays light (M6). Returns text or None on failure.
    Controlled by env:
      - ANTHROPIC_API_KEY (required; server-side only, never shipped to the client)
      - INSIGHTS_MODEL (optional, default 'claude-opus-4-8')
    Note: no `temperature` — it is rejected (400) on Opus 4.7/4.8.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    model = model or os.environ.get("INSIGHTS_MODEL", "claude-opus-4-8")
    logging.info(f"Using model: {model}")

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _INSIGHTS_SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = request.Request(
        "https://api.anthropic.com/v1/messages",
        method="POST",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        # Messages API returns content as a list of blocks; join the text blocks.
        blocks = payload.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return text.strip() or None
    except (urlerror.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
        import traceback
        print(f"LLM generation failed: {e}")
        traceback.print_exc()
        return None

def _build_prompt_for_llm(context: Dict[str, Any]) -> str:
    def _fmt_pct(x):
        return "n/a" if x is None else f"{x:.1%}"
    obs_n = context.get("obs_n", None)
    obs_info = f"{obs_n} pozorování" if obs_n else "neznámý počet pozorování"
    
    # Get HS6 product description to avoid LLM confusion
    hs6_code = context['hs6']
    hs6_description = _HS6_LABELS.get(hs6_code, f"HS6 {hs6_code}")
    product_info = f"HS6 {hs6_code} ({hs6_description})" if hs6_code in _HS6_LABELS else f"HS6 {hs6_code}"
    
    return (
        f"Data pro posouzení ({product_info}, země {context['importer_iso3']}, rok {context['year']} — {obs_info} za období ~posledních {5} let):\n"
        f"- Velikost trhu {context['year']}: { _fmt_usd(context['imp_last']) }\n"
        f"- CAGR importu (~5 let): { _fmt_pct(context['imp_cagr']) }\n"
        f"- Top země v datech (aktuální rok): {context['top_suppliers'] or '—'}\n"
        f"- ČR export celkem (HS6): { _fmt_usd(context['cz_global_last']) }\n"
        f"- ČR export do zvolené země: { _fmt_usd(context['cz_to_imp_last']) }\n"
        f"- Podíl ČR na trhu: { _fmt_pct(context['pen_imp']) }\n"
        f"- Medián podílu ČR napříč trhy: { _fmt_pct(context['pen_med']) }\n"
        f"- Top trhy ČR pro HS6: {context['cz_top_list'] or '—'}\n\n"
        f"DŮLEŽITÉ: Produkt je {product_info}. Ujisti se, že správně rozumíš produktu a nepletěš si ho s jiným HS6 kódem.\n\n"
        "Úkol: Vytvoř insight podle pravidel v system message. U každého bodu uveď vysvětlení nebo kontext. Jde i o edukaci.\n"
        "Explicitně dodrž strukturu:\n"
        "Kontext:\n"
        "Potenciál (nízký/střední/vysoký): …\n"
        "Příklady firem na straně importéra: …\n"
        "Příklady firem na straně českých exportérů: …\n"
        "Bariéry:\n"
        "– …\n"
        "– …\n"
        "To‑do (30–60 dní):\n"
        "– …\n"
        "– …\n"
        "– …\n"
        "Poznámky k datům: …\n"
        "Pracuj s výše uvedenými zdroji a dohledej na webu dodatečné informace. Sám si nic nevymýšlej"
    )

def extract_context(df: pd.DataFrame, importer_iso3: str, hs6: str, year: int, lookback: int) -> Dict[str, Any]:
    hs6_z = str(hs6).zfill(6)
    df = df[df["hs6"] == hs6_z]
    years = list(range(max(year - lookback + 1, int(df["year"].min())), year + 1))
    df = df[df["year"].isin(years)]

    # Import market time series and CAGR
    imp_ts = (
        df[df["partner_iso3"] == importer_iso3]
        .groupby("year")["import_partner_total"]
        .sum()
        .sort_index()
    )
    obs_n = int(len(imp_ts))
    imp_cagr = _cagr(imp_ts)
    imp_last = imp_ts.iloc[-1] if len(imp_ts) else None

    # Largest global import markets for this HS6 this year. (The serving layer
    # has no third-country bilateral flows, so we can't compute "who supplies
    # market X" — list the biggest import markets instead, no bogus % vs the
    # selected market. Fixes the old "USA (747%)" output.)
    imp_year = df[df["year"] == year]
    supp = (
        imp_year.groupby("partner_iso3")["import_partner_total"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )
    top_suppliers = ", ".join(str(k) for k in supp.index.tolist()) or "—"

    # Czech exports globally and to importer
    cz_to_imp_ts = (
        df[df["partner_iso3"] == importer_iso3]
        .groupby("year")["export_cz_to_partner"]
        .sum()
        .sort_index()
    )
    # Fix: export_cz_total_for_hs6 is same for all partners, take first value not sum
    cz_global_ts = (
        df.groupby("year")["export_cz_total_for_hs6"]
        .first()
        .sort_index()
    )
    cz_to_imp_last = cz_to_imp_ts.iloc[-1] if len(cz_to_imp_ts) else 0.0
    cz_global_last = cz_global_ts.iloc[-1] if len(cz_global_ts) else 0.0

    # Penetration and median peer penetration
    tot_imp_by_market = imp_year.groupby("partner_iso3")["import_partner_total"].sum()
    cz_to_markets = imp_year.groupby("partner_iso3")["export_cz_to_partner"].sum()
    pen = (cz_to_markets / tot_imp_by_market).dropna()
    
    # CORRECTED: Calculate median based on selected country's peer group, not all countries
    pen_med = None
    try:
        from api.data.loaders import resolve_peers
        # Try different peer group methodologies to find the best match for median calculation
        for method in ["human", "trade_structure", "opportunity"]:
            peer_countries = resolve_peers(importer_iso3, year, method)
            if peer_countries and len(peer_countries) > 1:
                # Filter pen to only include the peer countries  
                peer_pen = pen[pen.index.isin(peer_countries)]
                if len(peer_pen) >= 2:  # Need at least 2 data points for meaningful median
                    pen_med = peer_pen.median()
                    break
        
        # Fallback to all countries median if no peer group found
        if pen_med is None:
            pen_med = pen.median() if len(pen) else None
            
    except Exception as e:
        print(f"Error calculating peer group median for {importer_iso3}: {e}")
        # Fallback to original calculation
        pen_med = pen.median() if len(pen) else None
    
    pen_imp = (cz_to_imp_last / imp_last) if imp_last and imp_last>0 else None

    # Czech top markets
    cz_top = cz_to_markets.sort_values(ascending=False).head(3)
    cz_top_list = ", ".join([f"{k} ({v/cz_global_last:.0%})" if cz_global_last>0 else k for k,v in cz_top.items()]) or "—"

    # Import YoY change (partner's total imports)
    imp_yoy_change = None
    if len(imp_ts) >= 2:
        current_imp = imp_ts.iloc[-1]  # Most recent year
        prev_imp = imp_ts.iloc[-2]     # Previous year
        if prev_imp > 0:
            imp_yoy_change = (current_imp / prev_imp - 1) * 100  # As percentage

    # CZ's OWN export YoY to this importer (distinct from import YoY above).
    cz_export_yoy = None
    if len(cz_to_imp_ts) >= 2 and cz_to_imp_ts.iloc[-2] > 0:
        cz_export_yoy = (cz_to_imp_ts.iloc[-1] / cz_to_imp_ts.iloc[-2] - 1) * 100

    return {
        "cz_export_yoy": cz_export_yoy,
        "importer_iso3": importer_iso3,
        "hs6": hs6_z,
        "year": year,
        "imp_last": imp_last,
        "imp_cagr": imp_cagr,
        "imp_yoy_change": imp_yoy_change,
        "top_suppliers": top_suppliers,
        "cz_to_imp_last": cz_to_imp_last,
        "cz_global_last": cz_global_last,
        "pen_imp": pen_imp,
        "pen_med": pen_med,
        "cz_top_list": cz_top_list,
        "obs_n": obs_n,
    }

def generate_insights(parquet_path: str, importer_iso3: str, hs6: str, year: int, lookback: int = 5) -> str:
    """
    Deterministic or LLM text for INSIGHTS (2–3 paragraphs) from aggregated metrics parquet.
    Expected columns: year, partner_iso3, hs6, import_partner_total, export_cz_to_partner, export_cz_total_for_hs6
    """
    # Load aggregated metrics parquet (simulate cached call). Push the hs6 filter
    # down to the parquet read so we materialize only this product's ~few-thousand
    # rows, not the full 1.78M-row table — extract_context filters by hs6 first
    # anyway, so the result is identical. Without pushdown, reading the object
    # string columns over all rows spiked RSS ~+114 MB per call (toward the
    # 512 MB hosting cap). Identical output, a fraction of the memory.
    df = pd.read_parquet(parquet_path, columns=[
        "year", "partner_iso3", "hs6",
        "import_partner_total", "export_cz_to_partner", "export_cz_total_for_hs6"
    ], filters=[("hs6", "==", str(hs6).zfill(6))])

    context = extract_context(df, importer_iso3, hs6, year, lookback)

    use_llm = os.environ.get("INSIGHTS_USE_LLM", "1") not in ("0", "false", "False")
    if use_llm:
        prompt = _build_prompt_for_llm(context)
        llm_text = _llm_generate(prompt)
        if llm_text:
            return llm_text.strip()

    # Fallback deterministic text — Czech (2 paragraphs), shown when the LLM is
    # off or unavailable. None-guarded so missing metrics don't crash.
    def _pct(x):
        return "neznámé" if x is None else f"{x:.1%}"

    p1 = (
        f"{importer_iso3} dovezl HS6 {context['hs6']} v hodnotě { _fmt_usd(context['imp_last']) } v roce {year}. "
        f"Tempo růstu trhu: {_pct(context['imp_cagr'])} ročně za posledních {lookback} let. "
        f"Největší dovozní trhy pro tuto položku: {context['top_suppliers']}."
    )
    share_line = ""
    if context['pen_imp'] is not None and context['pen_med'] is not None:
        gap = context['pen_imp'] - context['pen_med']
        vztah = "blízko/nad mediánem srovnatelných trhů" if gap >= 0 else "pod mediánem srovnatelných trhů"
        share_line = f" Podíl ČR na trhu {importer_iso3} je {_pct(context['pen_imp'])}, {vztah} ({_pct(context['pen_med'])})."
    p2 = (
        f"ČR vyváží HS6 {context['hs6']} celosvětově za { _fmt_usd(context['cz_global_last']) } v roce {year}; "
        f"z toho { _fmt_usd(context['cz_to_imp_last']) } směřovalo do {importer_iso3}.{share_line} "
        f"Top české trhy pro HS6 v roce {year}: {context['cz_top_list']}."
    )
    return "\n\n".join([p1, p2])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True)
    ap.add_argument("--importer", required=True)
    ap.add_argument("--hs6", required=True)
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    out = generate_insights(args.parquet, args.importer, args.hs6, args.year)
    print(out)