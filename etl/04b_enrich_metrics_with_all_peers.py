#!/usr/bin/env python3
"""
Enhanced metrics enrichment with ALL peer group methodologies.

This script replaces the original 04_enrich_metrics_with_peers.py to support
multiple peer group methodologies in a single comprehensive dataset.

Input: metrics.parquet + peer_medians_comprehensive.parquet  
Output: metrics_all_peers.parquet
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Constants
METRICS = "data/out/metrics.parquet"
PEER_MEDIANS = "data/out/peer_medians_comprehensive.parquet"
OUTPUT = "data/out/metrics_all_peers.parquet"

# Fallback to original for backward compatibility
LEGACY_PEERS = "data/out/peer_medians_statistical.parquet"
LEGACY_OUTPUT = "data/out/metrics_enriched.parquet"


def load_data():
    """Load metrics and peer medians data - NO FALLBACKS PERMITTED"""
    if not os.path.isfile(METRICS):
        raise FileNotFoundError(f"Missing {METRICS}. Run etl/02_compute_trade_metrics.py first.")
    
    if not os.path.isfile(PEER_MEDIANS):
        raise FileNotFoundError(f"Missing {PEER_MEDIANS}. Run etl/03b_compute_all_peer_medians.py first. NO FALLBACKS PERMITTED.")
    
    metrics = pd.read_parquet(METRICS)
    peer_medians = pd.read_parquet(PEER_MEDIANS)
    
    print(f"Loaded metrics: {len(metrics):,} rows")
    print(f"Loaded comprehensive peer medians: {len(peer_medians):,} rows")
    
    return metrics, peer_medians


def enrich_with_comprehensive_peers(metrics, peer_medians):
    """Enrich metrics with all peer group methodologies"""
    print("Enriching metrics with comprehensive peer group data...")
    
    # Get list of all methodologies
    methodologies = peer_medians['method'].unique()
    print(f"Found methodologies: {', '.join(methodologies)}")
    
    # Start with base metrics
    enriched = metrics.copy()
    
    # Add peer data for each methodology
    for method in methodologies:
        print(f"  Processing {method} methodology...")
        
        method_peers = peer_medians[peer_medians['method'] == method].copy()
        
        # Create methodology-specific column names
        method_safe = method.replace('-', '_').replace(':', '_')
        median_col = f'median_peer_share_{method_safe}'
        delta_col = f'delta_vs_peer_{method_safe}'
        countries_col = f'peer_countries_{method_safe}'
        count_col = f'peer_count_{method_safe}'
        
        # Merge peer data
        method_data = method_peers[['year', 'hs6', 'partner_iso3', 'peer_median_share', 'peer_countries', 'peer_count']].rename(columns={
            'peer_median_share': median_col,
            'peer_countries': countries_col, 
            'peer_count': count_col
        })
        
        enriched = enriched.merge(method_data, on=['year', 'hs6', 'partner_iso3'], how='left')
        
        # Compute deltas
        enriched[delta_col] = enriched['podil_cz_na_importu'] - enriched[median_col]
        
        # Count non-null values
        non_null = enriched[median_col].notna().sum()
        print(f"    Added {non_null:,} peer median values for {method}")
    
    # Add backward compatibility columns (use geographic as default)
    if 'median_peer_share_geographic' in enriched.columns:
        enriched['median_peer_share'] = enriched['median_peer_share_geographic']
        enriched['delta_vs_peer'] = enriched['delta_vs_peer_geographic']
        print("Added backward compatibility columns using geographic methodology")
    
    return enriched


def enrich_with_legacy_peers(metrics, peer_medians):
    """Fallback enrichment with legacy peer medians"""
    print("Enriching metrics with legacy peer group data...")
    
    # Simple merge like original script
    enriched = metrics.merge(peer_medians, on=["year", "hs6", "partner_iso3"], how="left")
    
    # Compute delta vs peer  
    enriched["delta_vs_peer"] = enriched["podil_cz_na_importu"] - enriched["median_peer_share"]
    
    return enriched


def main():
    """Main execution function"""
    print("=== Enriching Metrics with All Peer Groups ===")
    
    # Load data - NO FALLBACKS
    metrics, peer_medians = load_data()
    
    # Enrich with comprehensive peers only
    enriched = enrich_with_comprehensive_peers(metrics, peer_medians)
    
    # Save enriched metrics
    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    enriched.to_parquet(OUTPUT, index=False)
    
    # Validation summary
    total_rows = len(enriched)
    print(f"✅ Saved enriched metrics: {total_rows:,} rows → {OUTPUT}")
    
    # Summary by methodology columns
    peer_median_cols = [col for col in enriched.columns if col.startswith('median_peer_share')]
    for col in peer_median_cols:
        non_null = enriched[col].notna().sum()
        methodology = col.replace('median_peer_share_', '')
        print(f"  {methodology}: {non_null:,}/{total_rows:,} ({100*non_null/total_rows:.1f}%) rows with peer data")
    
    print(f"📊 Dataset ready for signal generation with comprehensive peer group support!")


if __name__ == "__main__":
    main()