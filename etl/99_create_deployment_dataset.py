#!/usr/bin/env python3
"""
Create deployment-ready dataset with:
- Full global coverage for map functionality  
- Smart optimization for size constraints
- No functionality loss

Output: ~13MB of optimized data in data/deployment/
"""

import os
import pandas as pd
import yaml
from pathlib import Path

def create_core_trade():
    """
    Full global trade data optimized for deployment
    - Keep: ALL countries × ALL HS6 relationships
    - Filter: 2023 data only (cut 50% of data)
    - Optimize: Use int32 for numbers, category for strings
    - Compress: Use snappy compression
    - Result: ~12MB (from ~23MB original)
    """
    print("📊 Processing core trade data...")
    
    # Load base facts
    df = pd.read_parquet('data/out/fact_base.parquet')
    df = df[df['year'] == 2023].copy()
    print(f"   Base facts: {len(df):,} rows")
    
    # Optimize data types
    df['year'] = df['year'].astype('int32')
    df['export_cz_to_partner'] = df['export_cz_to_partner'].astype('int64')
    df['partner_iso3'] = df['partner_iso3'].astype('category')
    df['hs6'] = df['hs6'].astype('category')
    
    # Add essential computed columns from metrics
    try:
        metrics = pd.read_parquet('data/out/metrics_enriched.parquet')
        metrics_2023 = metrics[metrics['year'] == 2023].copy()
        
        # Select essential metrics columns
        essential_metrics = metrics_2023[[
            'partner_iso3', 'hs6', 'podil_cz_na_importu', 
            'import_partner_total', 'YoY_export_change'
        ]].copy()
        
        # Merge essential metrics
        df = df.merge(essential_metrics, on=['partner_iso3', 'hs6'], how='left')
        print(f"   Added metrics for {len(essential_metrics):,} trade relationships")
        
    except FileNotFoundError:
        print("   Warning: metrics_enriched.parquet not found, using base data only")
    
    # Save optimized
    output_path = 'data/deployment/core_trade.parquet'
    df.to_parquet(output_path, compression='snappy')
    
    # Report results
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    print(f"   ✅ Core trade: {len(df):,} rows")
    print(f"   ✅ Countries: {df['partner_iso3'].nunique()}")
    print(f"   ✅ HS6 codes: {df['hs6'].nunique()}")
    print(f"   ✅ File size: {size_mb:.1f}MB")
    print(f"   ✅ Memory usage: {memory_mb:.1f}MB")
    
    return df

def create_signals_filtered():
    """
    Top 3 signals per type per country
    - Keep: Signal diversity across all countries
    - Filter: Only strongest signals per type
    - Result: ~2,700 signals vs 5,595 original
    """
    print("🎯 Processing signals...")
    
    try:
        df = pd.read_parquet('data/out/signals_comprehensive.parquet')
        print(f"   Original signals: {len(df):,}")
        
        # Top 3 signals per type per country, ordered by intensity
        filtered = []
        signal_types = df['type'].unique()
        print(f"   Signal types: {len(signal_types)}")
        
        for signal_type in signal_types:
            type_df = df[df['type'] == signal_type].copy()
            
            for country in type_df['partner_iso3'].unique():
                country_signals = type_df[type_df['partner_iso3'] == country].copy()
                
                # Sort by intensity (absolute value of relevant metric)
                if 'delta_vs_peer' in country_signals.columns:
                    country_signals = country_signals.reindex(
                        country_signals['delta_vs_peer'].abs().sort_values(ascending=False).index
                    )
                elif 'YoY_export_change' in country_signals.columns:
                    country_signals = country_signals.reindex(
                        country_signals['YoY_export_change'].abs().sort_values(ascending=False).index
                    )
                
                # Take top 3
                top_3 = country_signals.head(3)
                filtered.append(top_3)
        
        if filtered:
            result = pd.concat(filtered, ignore_index=True)
            
            # Optimize data types
            result['partner_iso3'] = result['partner_iso3'].astype('category')
            result['hs6'] = result['hs6'].astype('category')
            result['type'] = result['type'].astype('category')
            
            # Save
            output_path = 'data/deployment/signals_filtered.parquet'
            result.to_parquet(output_path, compression='snappy')
            
            size_kb = os.path.getsize(output_path) / 1024
            print(f"   ✅ Filtered signals: {len(result):,} rows")
            print(f"   ✅ Countries: {result['partner_iso3'].nunique()}")
            print(f"   ✅ File size: {size_kb:.0f}KB")
            
            return result
        else:
            print("   ⚠️ No signals data found")
            return pd.DataFrame()
            
    except FileNotFoundError:
        print("   ⚠️ signals_comprehensive.parquet not found")
        return pd.DataFrame()

def create_peer_relationships():
    """
    All peer group relationships - essential for signal explanations
    """
    print("🤝 Processing peer relationships...")
    
    peer_files = [
        ('data/out/peer_groups_human.parquet', 'human'),
        ('data/out/peer_groups_hs2.parquet', 'hs2'), 
        ('data/out/peer_groups_opportunity.parquet', 'opportunity'),
        ('data/out/peer_groups_statistical.parquet', 'statistical')
    ]
    
    all_peers = []
    for file_path, methodology in peer_files:
        if os.path.exists(file_path):
            df = pd.read_parquet(file_path)
            df['methodology'] = methodology
            all_peers.append(df)
            print(f"   Loaded {methodology}: {len(df)} rows")
        else:
            print(f"   ⚠️ Missing: {file_path}")
    
    if all_peers:
        result = pd.concat(all_peers, ignore_index=True)
        
        # Optimize data types
        if 'country_iso3' in result.columns:
            result['country_iso3'] = result['country_iso3'].astype('category')
        result['methodology'] = result['methodology'].astype('category')
        
        # Save
        output_path = 'data/deployment/peer_relationships.parquet'
        result.to_parquet(output_path, compression='snappy')
        
        size_kb = os.path.getsize(output_path) / 1024
        print(f"   ✅ Peer relationships: {len(result):,} rows")
        print(f"   ✅ Methodologies: {result['methodology'].nunique()}")
        print(f"   ✅ File size: {size_kb:.0f}KB")
        
        return result
    else:
        print("   ⚠️ No peer group data found")
        return pd.DataFrame()

def create_metadata():
    """
    Reference data: countries, HS6 names, configurations
    """
    print("📋 Processing metadata...")
    
    metadata = {}
    
    # Country data
    try:
        countries = pd.read_csv('data/ref/countries.csv')
        metadata['countries'] = countries.to_dict('records')
        print(f"   Countries: {len(countries)}")
    except FileNotFoundError:
        print("   ⚠️ countries.csv not found")
        metadata['countries'] = []
    
    # HS6 names
    try:
        hs6_names = pd.read_csv('data/ref/hs_names.csv')
        metadata['hs6_names'] = dict(zip(hs6_names['hs6'], hs6_names['name']))
        print(f"   HS6 names: {len(hs6_names)}")
    except FileNotFoundError:
        print("   ⚠️ hs_names.csv not found")
        metadata['hs6_names'] = {}
    
    # Configuration from YAML
    try:
        with open('data/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        metadata['config'] = config
        print("   ✅ Config loaded")
    except FileNotFoundError:
        print("   ⚠️ config.yaml not found")
        metadata['config'] = {}
    
    # Save as compressed parquet for consistency
    meta_df = pd.DataFrame([metadata])  # Single row with JSON columns
    output_path = 'data/deployment/metadata.parquet'
    meta_df.to_parquet(output_path, compression='snappy')
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"   ✅ Metadata file size: {size_kb:.0f}KB")
    
    return metadata

def validate_deployment_data():
    """Ensure deployment data maintains functionality"""
    print("✅ Validating deployment data...")
    
    try:
        core = pd.read_parquet('data/deployment/core_trade.parquet')
        
        # Validate map functionality
        countries = core['partner_iso3'].nunique()
        hs6_codes = core['hs6'].nunique()
        
        print(f"   Countries: {countries} (need ≥200)")
        print(f"   HS6 codes: {hs6_codes} (need ≥5000)")
        
        assert countries >= 200, f"Map needs global coverage, got {countries} countries"
        assert hs6_codes >= 5000, f"Map needs full HS6 coverage, got {hs6_codes} codes"
        
        # Validate signals if available
        try:
            signals = pd.read_parquet('data/deployment/signals_filtered.parquet')
            signal_countries = signals['partner_iso3'].nunique()
            signal_types = signals['type'].nunique()
            
            print(f"   Signal countries: {signal_countries}")
            print(f"   Signal types: {signal_types}")
            
        except FileNotFoundError:
            print("   ⚠️ No signals file to validate")
        
        print("   ✅ Data validation passed!")
        
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        raise

def main():
    """Main execution"""
    print("🏗️ Creating deployment dataset...")
    print("=" * 60)
    
    # Create deployment directory
    os.makedirs('data/deployment', exist_ok=True)
    
    # Process all data
    core_trade = create_core_trade()
    signals = create_signals_filtered()
    peers = create_peer_relationships()
    metadata = create_metadata()
    
    # Validate results
    validate_deployment_data()
    
    # Summary
    print("=" * 60)
    print("📊 DEPLOYMENT DATASET SUMMARY:")
    
    total_size = 0
    for file in Path('data/deployment').glob('*.parquet'):
        size_mb = file.stat().st_size / (1024 * 1024)
        total_size += size_mb
        print(f"   {file.name}: {size_mb:.1f}MB")
    
    print(f"   TOTAL SIZE: {total_size:.1f}MB")
    print("✅ Deployment dataset created successfully!")

if __name__ == "__main__":
    main()