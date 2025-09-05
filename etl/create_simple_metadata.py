#!/usr/bin/env python3
"""
Create simple CSV metadata files instead of complex JSON structure
"""

import pandas as pd
import os
import yaml

def create_simple_metadata():
    """Create simple CSV files for metadata instead of JSON-in-CSV"""
    
    # Countries - create a simple mapping
    countries_data = []
    
    # Get unique countries from core trade data
    core_df = pd.read_csv('data/deployment/core_trade.csv')
    unique_countries = core_df['partner_iso3'].unique()
    
    for iso3 in unique_countries:
        countries_data.append({'iso3': iso3, 'name': iso3})  # Use ISO3 as name for simplicity
    
    countries_df = pd.DataFrame(countries_data)
    countries_df.to_csv('data/deployment/countries.csv', index=False)
    print(f"Created countries.csv with {len(countries_df)} countries")
    
    # HS6 names - create simple mapping 
    hs6_data = []
    unique_hs6 = core_df['hs6'].unique()
    
    for hs6 in unique_hs6[:100]:  # Limit to first 100 for size
        hs6_data.append({'hs6': hs6, 'name': f'Product {hs6}'})
    
    hs6_df = pd.DataFrame(hs6_data)
    hs6_df.to_csv('data/deployment/hs6_names.csv', index=False)
    print(f"Created hs6_names.csv with {len(hs6_df)} products")
    
    # Config - create a simple YAML config
    config = {
        'version': '1.0',
        'data_source': 'deployment_csv',
        'last_updated': '2025-09-05'
    }
    
    with open('data/deployment/config.yaml', 'w') as f:
        yaml.dump(config, f)
    print("Created config.yaml")

if __name__ == "__main__":
    create_simple_metadata()