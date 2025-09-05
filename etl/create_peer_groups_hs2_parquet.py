#!/usr/bin/env python3
"""
Convert peer_groups_hs2_explained.csv to peer_groups_hs2.parquet format
for the trade structure peer groups methodology.

Updated to output alpha-3 ISO codes for consistency across the system.
"""

import pandas as pd
import os
from pathlib import Path
import sys

# Add API utils to path for country code conversion
sys.path.append(str(Path(__file__).parent.parent / "api"))
from utils.country_codes import name_to_iso3

def main():
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "out"
    input_file = data_dir / "peer_groups_hs2_explained.csv"
    output_file = data_dir / "peer_groups_hs2.parquet"
    
    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    
    # Read the explained CSV
    df = pd.read_csv(input_file)
    
    # Expand countries from comma-separated strings to individual rows
    expanded_rows = []
    
    for _, row in df.iterrows():
        countries_str = row['countries']
        group_no = row['grouping_no']
        group_name = row['grouping_name']
        
        # Split countries by comma and clean up
        if pd.notna(countries_str):
            countries = [c.strip() for c in countries_str.split(',')]
            
            for country in countries:
                # Skip numeric codes that might be artifacts
                if country.isdigit():
                    continue
                
                # Convert country name to alpha-3 ISO code
                iso3_code = name_to_iso3(country)
                if not iso3_code:
                    print(f"Warning: Could not convert '{country}' to ISO3 code, skipping")
                    continue
                    
                expanded_rows.append({
                    'iso3': iso3_code,
                    'cluster': group_no,
                    'cluster_name': group_name,
                    'methodology': 'trade_structure'
                })
    
    # Create the final dataframe
    result_df = pd.DataFrame(expanded_rows)
    
    # Save as parquet
    result_df.to_parquet(output_file, index=False)
    
    print(f"Created {output_file} with {len(result_df)} country-cluster mappings")
    print(f"Unique clusters: {result_df['cluster'].nunique()}")
    print(f"Sample data:")
    print(result_df.head(10))
    
    # Validate that all codes are proper alpha-3
    invalid_codes = result_df[~result_df['iso3'].str.match(r'^[A-Z]{3}$', na=False)]
    if len(invalid_codes) > 0:
        print(f"Warning: Found {len(invalid_codes)} invalid ISO3 codes:")
        print(invalid_codes[['iso3']].head())
    else:
        print("✅ All ISO3 codes are valid alpha-3 format")

if __name__ == "__main__":
    main()