#!/usr/bin/env python3
"""
Generate comprehensive signals for ALL peer group methodologies.

This script replaces the original signal generation to support all peer group
methodologies in a unified, consistent manner.

Input: metrics_all_peers.parquet + config.yaml
Output: signals_comprehensive.parquet
"""

import os
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Constants
METRICS = "data/out/metrics_all_peers.parquet"
CONFIG = "data/config.yaml"
OUTPUT = "data/out/signals_comprehensive.parquet"

# Fallback paths
LEGACY_METRICS = "data/out/metrics_enriched.parquet"
LEGACY_OUTPUT = "data/out/signals.json"


def load_config():
    """Load configuration with safe defaults"""
    defaults = {
        "MIN_EXPORT_USD": 100_000,
        "MIN_IMPORT_USD": 5_000_000, 
        "S1_REL_GAP_MIN": 0.20,
        "S2_YOY_THRESHOLD": 0.30,
        "S3_YOY_SHARE_THRESHOLD": 0.20,
        "MAX_TOTAL": 10,
        "MAX_PER_TYPE": 4,
    }
    
    if not os.path.isfile(CONFIG):
        print("Warning: config.yaml not found, using defaults")
        return defaults
    
    try:
        with open(CONFIG, "r") as f:
            config = yaml.safe_load(f) or {}
        thresholds = {**defaults, **(config.get("thresholds") or {})}
        return thresholds
    except Exception as e:
        print(f"Warning: Error loading config.yaml ({e}), using defaults")
        return defaults


def load_metrics():
    """Load metrics data with peer group information"""
    if os.path.isfile(METRICS):
        df = pd.read_parquet(METRICS)
        print(f"Loaded comprehensive metrics: {len(df):,} rows")
        use_comprehensive = True
    elif os.path.isfile(LEGACY_METRICS):
        print("Warning: Using legacy metrics (run etl/04b_enrich_metrics_with_all_peers.py for full functionality)")
        df = pd.read_parquet(LEGACY_METRICS)
        use_comprehensive = False
    else:
        raise FileNotFoundError("Missing metrics data. Run ETL pipeline first.")
    
    return df, use_comprehensive


def get_methodology_columns(df):
    """Identify all peer group methodology columns in the dataset"""
    peer_median_cols = [col for col in df.columns if col.startswith('median_peer_share_')]
    methodologies = {}
    
    for col in peer_median_cols:
        method = col.replace('median_peer_share_', '')
        delta_col = f'delta_vs_peer_{method}'
        countries_col = f'peer_countries_{method}'
        
        if delta_col in df.columns:
            methodologies[method] = {
                'median_col': col,
                'delta_col': delta_col,
                'countries_col': countries_col if countries_col in df.columns else None
            }
    
    # Add default methodology if available
    if 'median_peer_share' in df.columns and 'delta_vs_peer' in df.columns:
        methodologies['default'] = {
            'median_col': 'median_peer_share',
            'delta_col': 'delta_vs_peer', 
            'countries_col': None
        }
    
    print(f"Found methodologies: {', '.join(methodologies.keys())}")
    return methodologies


def generate_peer_gap_signals(df, methodologies, thresholds):
    """Generate peer gap signals for all methodologies"""
    print("Generating peer gap signals...")
    
    MIN_EXPORT_USD = thresholds["MIN_EXPORT_USD"]
    MIN_IMPORT_USD = thresholds["MIN_IMPORT_USD"]
    S1_REL_GAP_MIN = thresholds["S1_REL_GAP_MIN"]
    MAX_PER_TYPE = thresholds["MAX_PER_TYPE"]
    
    latest_year = int(df["year"].max())
    current_year_data = df[df["year"] == latest_year].copy()
    
    # Apply significance filter
    significant_data = current_year_data[
        (current_year_data["export_cz_to_partner"] >= MIN_EXPORT_USD) | 
        (current_year_data["import_partner_total"] >= MIN_IMPORT_USD)
    ]
    
    all_signals = []
    
    for method, cols in methodologies.items():
        print(f"  Processing {method} methodology...")
        
        method_data = significant_data[
            significant_data[cols['median_col']].notna() &
            significant_data[cols['delta_col']].notna()
        ].copy()
        
        if method_data.empty:
            continue
        
        # Calculate relative gap
        method_data['rel_gap'] = np.where(
            method_data[cols['median_col']] > 0,
            (method_data[cols['median_col']] - method_data['podil_cz_na_importu']) / method_data[cols['median_col']],
            0
        )
        
        # Filter by threshold
        gap_signals = method_data[method_data['rel_gap'] >= S1_REL_GAP_MIN].copy()
        
        if gap_signals.empty:
            continue
        
        # Ensure balanced distribution: 3 signals per country for this methodology
        balanced_signals = []
        signals_per_country = 3
        
        # Group by partner country and take top 3 signals per country
        # Use methodology-specific ranking strategies to ensure diversity
        for partner, partner_data in gap_signals.groupby('partner_iso3'):
            partner_data_ranked = partner_data.copy()
            
            # Apply methodology-specific ranking strategies
            if method == 'human':
                # Human methodology: prefer markets with higher trade volumes
                partner_data_ranked['methodology_rank'] = (
                    partner_data_ranked[cols['delta_col']].abs() * 0.7 +
                    (partner_data_ranked['import_partner_total'] / 1e9) * 0.3  # Volume factor
                )
            elif method == 'opportunity':  
                # Opportunity methodology: prefer markets with growth potential
                partner_data_ranked['methodology_rank'] = (
                    partner_data_ranked[cols['delta_col']].abs() * 0.8 +
                    partner_data_ranked['YoY_export_change'].fillna(0).abs() * 0.2  # Growth factor
                )
            else:
                # Trade structure: use pure peer gap (original logic)
                partner_data_ranked['methodology_rank'] = partner_data_ranked[cols['delta_col']].abs()
            
            top_partner_signals = partner_data_ranked.sort_values('methodology_rank', ascending=False).head(signals_per_country)
            balanced_signals.append(top_partner_signals)
        
        if balanced_signals:
            gap_signals = pd.concat(balanced_signals, ignore_index=True)
        else:
            gap_signals = pd.DataFrame()
        
        # Format signals
        for _, row in gap_signals.iterrows():
            peer_countries = []
            if cols['countries_col'] and pd.notna(row[cols['countries_col']]):
                try:
                    peer_countries = json.loads(row[cols['countries_col']])
                except:
                    peer_countries = []
            
            # Map method names to UI-expected signal types
            method_to_signal_type = {
                'trade_structure': 'Peer_gap_matching',            # Trade structure peers (HS2 similarity)
                'kmeans_cosine_hs2_shares': 'Peer_gap_matching',   # Legacy name mapping
                'human': 'Peer_gap_human',                         # Geographic/human-curated peers
                'opportunity': 'Peer_gap_opportunity',             # Opportunity-based peers
                'default': 'Peer_gap_below_median'                 # Default methodology
            }
            signal_type = method_to_signal_type.get(method, f"Peer_gap_{method}")
            
            all_signals.append({
                'type': signal_type,
                'year': int(row['year']),
                'hs6': str(row['hs6']).zfill(6),
                'partner_iso3': str(row['partner_iso3']),
                'intensity': float(abs(row[cols['delta_col']])),  # Use methodology-specific delta
                'value': float(row['podil_cz_na_importu']),
                'yoy': None,
                'peer_median': float(row[cols['median_col']]),
                'delta_vs_peer': float(row[cols['delta_col']]),
                'method': method,
                'peer_countries': json.dumps(peer_countries),
                'peer_count': len(peer_countries),
                'methodology_explanation': get_methodology_explanation(method)
            })
    
    print(f"  Generated {len(all_signals)} peer gap signals")
    return all_signals


def generate_yoy_export_signals(df, thresholds):
    """Generate YoY export change signals"""
    print("Generating YoY export signals...")
    
    S2_YOY_THRESHOLD = thresholds["S2_YOY_THRESHOLD"]
    MAX_PER_TYPE = thresholds["MAX_PER_TYPE"]
    
    latest_year = int(df["year"].max())
    current_year_data = df[df["year"] == latest_year].copy()
    
    if 'YoY_export_change' not in current_year_data.columns:
        print("  Warning: YoY_export_change column not found")
        return []
    
    yoy_data = current_year_data[current_year_data['YoY_export_change'].notna()].copy()
    yoy_data['intensity'] = yoy_data['YoY_export_change'].abs()
    
    # Filter by threshold
    yoy_signals = yoy_data[yoy_data['intensity'] >= S2_YOY_THRESHOLD].copy()
    yoy_signals = yoy_signals.sort_values('intensity', ascending=False).head(MAX_PER_TYPE)
    
    signals = []
    for _, row in yoy_signals.iterrows():
        signals.append({
            'type': 'YoY_export_change',
            'year': int(row['year']),
            'hs6': str(row['hs6']).zfill(6),
            'partner_iso3': str(row['partner_iso3']),
            'intensity': float(row['intensity']),
            'value': float(row.get('export_cz_to_partner', 0)),
            'yoy': float(row['YoY_export_change']),
            'peer_median': None,
            'delta_vs_peer': None,
            'method': 'yoy_export',
            'peer_countries': json.dumps([]),
            'peer_count': 0,
            'methodology_explanation': 'Significant year-over-year changes in Czech export values to specific markets.'
        })
    
    print(f"  Generated {len(signals)} YoY export signals")
    return signals


def generate_yoy_share_signals(df, thresholds):
    """Generate YoY partner share change signals"""
    print("Generating YoY share signals...")
    
    S3_YOY_SHARE_THRESHOLD = thresholds["S3_YOY_SHARE_THRESHOLD"]
    MAX_PER_TYPE = thresholds["MAX_PER_TYPE"]
    
    latest_year = int(df["year"].max())
    current_year_data = df[df["year"] == latest_year].copy()
    
    if 'YoY_partner_share_change' not in current_year_data.columns:
        print("  Warning: YoY_partner_share_change column not found")
        return []
    
    share_data = current_year_data[current_year_data['YoY_partner_share_change'].notna()].copy()
    share_data['intensity'] = share_data['YoY_partner_share_change'].abs()
    
    # Filter by threshold
    share_signals = share_data[share_data['intensity'] >= S3_YOY_SHARE_THRESHOLD].copy()
    share_signals = share_signals.sort_values('intensity', ascending=False).head(MAX_PER_TYPE)
    
    signals = []
    for _, row in share_signals.iterrows():
        signals.append({
            'type': 'YoY_partner_share_change',
            'year': int(row['year']),
            'hs6': str(row['hs6']).zfill(6),
            'partner_iso3': str(row['partner_iso3']),
            'intensity': float(row['intensity']),
            'value': float(row.get('podil_cz_na_importu', 0)),
            'yoy': float(row['YoY_partner_share_change']),
            'peer_median': None,
            'delta_vs_peer': None,
            'method': 'yoy_share',
            'peer_countries': json.dumps([]),
            'peer_count': 0,
            'methodology_explanation': 'Significant changes in market importance within Czech export portfolio.'
        })
    
    print(f"  Generated {len(signals)} YoY share signals")
    return signals


def get_methodology_explanation(method):
    """Get human-readable explanation for methodology"""
    explanations = {
        'geographic': 'Czech Republic compared against countries in similar geographic and development context.',
        'default': 'Czech Republic compared against default statistical peer group.',
        'human': 'Czech Republic compared against expert-curated peer group based on economic relationships.',
        'statistical': 'Czech Republic compared against countries with similar export structures identified through machine learning.',
        'opportunity': 'Czech Republic compared against countries with similar export opportunity profiles.'
    }
    
    # Handle k-parameterized methodologies
    if '_k' in method:
        base_method = method.split('_k')[0]
        k_param = method.split('_k')[1]
        base_explanation = explanations.get(base_method, 'Statistical peer group comparison.')
        return f"{base_explanation} Using cluster analysis with k={k_param} parameter."
    
    return explanations.get(method, 'Peer group comparison methodology.')


def main():
    """Main execution function"""
    print("=== Generating Comprehensive Signals ===")
    
    # Load configuration and data
    thresholds = load_config()
    df, use_comprehensive = load_metrics()
    
    if not use_comprehensive:
        print("Warning: Using legacy signal generation. Run full ETL pipeline for comprehensive functionality.")
    
    # Identify available methodologies
    methodologies = get_methodology_columns(df)
    
    if not methodologies:
        print("Error: No peer group methodologies found in data!")
        return
    
    # Generate all signal types
    all_signals = []
    
    # Peer gap signals (multiple methodologies)
    peer_gap_signals = generate_peer_gap_signals(df, methodologies, thresholds)
    all_signals.extend(peer_gap_signals)
    
    # YoY signals
    yoy_export_signals = generate_yoy_export_signals(df, thresholds)
    all_signals.extend(yoy_export_signals)
    
    yoy_share_signals = generate_yoy_share_signals(df, thresholds)
    all_signals.extend(yoy_share_signals)
    
    # Apply global limits
    MAX_TOTAL = thresholds["MAX_TOTAL"]
    
    if all_signals:
        # Convert to DataFrame for easier manipulation
        signals_df = pd.DataFrame(all_signals)
        
        # Sort by intensity and apply global limit
        signals_df = signals_df.sort_values('intensity', ascending=False)
        
        # For peer gap signals, use all generated signals (already balanced per country)
        # For YoY signals, apply per-type limits
        final_signals = []
        
        for _, signal in signals_df.iterrows():
            signal_type = signal['type']
            
            # Peer gap signals: include all (already limited to 3 per country per methodology)
            if signal_type.startswith('Peer_gap_'):
                final_signals.append(signal.to_dict())
            # YoY signals: apply original limits
            else:
                final_signals.append(signal.to_dict())
        
        # Save comprehensive signals
        final_df = pd.DataFrame(final_signals)
        
        Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        final_df.to_parquet(OUTPUT, index=False)
        
        print(f"✅ Saved comprehensive signals: {len(final_df)} signals → {OUTPUT}")
        
        # Summary by signal type
        summary = final_df.groupby('type').size().to_dict()
        for signal_type, count in summary.items():
            print(f"  {signal_type}: {count} signals")
        
        # Summary by methodology
        method_summary = final_df.groupby('method').size().to_dict()
        for method, count in method_summary.items():
            print(f"  Methodology {method}: {count} signals")
        
        print("🎯 Comprehensive signals ready for API consumption!")
    
    else:
        print("⚠️ No signals generated. Check thresholds and data quality.")


if __name__ == "__main__":
    main()