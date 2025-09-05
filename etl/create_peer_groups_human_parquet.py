#!/usr/bin/env python3
"""
Convert peer_groups_human_explained.csv to peer_groups_human.parquet format
for the human peer groups methodology, excluding Czech Republic.
"""

import pandas as pd
import pycountry
from pathlib import Path

def main():
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "out"
    input_file = data_dir / "peer_groups_human_explained.csv"
    output_file = data_dir / "peer_groups_human.parquet"
    
    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    
    # Read the explained CSV
    df = pd.read_csv(input_file)
    
    # Expand countries from comma-separated strings to individual rows
    expanded_rows = []
    
    for _, row in df.iterrows():
        countries_str = row['countries']
        group_no = row['grouping_no']
        
        # Split countries by comma and clean up
        if pd.notna(countries_str):
            countries = [c.strip() for c in countries_str.split(',')]
            
            for country in countries:
                    
                # Convert country name to ISO3 if possible
                iso3_code = None
                try:
                    # Try direct pycountry lookup
                    country_rec = pycountry.countries.search_fuzzy(country.strip())
                    if country_rec:
                        iso3_code = country_rec[0].alpha_3
                except Exception:
                    # Manual mappings for common cases that pycountry might miss
                    manual_mappings = {
                        'Bolivia, Plurinational State of': 'BOL',
                        'Congo': 'COG', 
                        'Congo, The Democratic Republic of the': 'COD',
                        'Côte d\'Ivoire': 'CIV',
                        'Iran, Islamic Republic of': 'IRN',
                        'Korea, Republic of': 'KOR',
                        'Lao People\'s Democratic Republic': 'LAO',
                        'Macao': 'MAC',
                        'Moldova, Republic of': 'MDA',
                        'Palestine, State of': 'PSE',
                        'Russian Federation': 'RUS',
                        'Syrian Arab Republic': 'SYR',
                        'Tanzania, United Republic of': 'TZA',
                        'Venezuela, Bolivarian Republic of': 'VEN'
                    }
                    iso3_code = manual_mappings.get(country.strip())
                
                if iso3_code:
                    expanded_rows.append({
                        'iso3': iso3_code,
                        'cluster': group_no,
                        'method': 'human_geo_econ_v2',
                        'k': 23,  # Total number of clusters
                        'year': 2023
                    })
                else:
                    print(f"Warning: Could not map country '{country}' to ISO3 code")
    
    # Create the final dataframe
    result_df = pd.DataFrame(expanded_rows)
    
    # Save as parquet
    result_df.to_parquet(output_file, index=False)
    
    print(f"Created {output_file} with {len(result_df)} country-cluster mappings")
    print(f"Unique clusters: {result_df['cluster'].nunique()}")
    print(f"Countries per cluster:")
    print(result_df.groupby('cluster').size().sort_index())
    
    # Show sample
    print("Sample data:")
    print(result_df.head(10))

if __name__ == "__main__":
    main()