#!/usr/bin/env python3
"""
Convert peer_groups_opportunity.csv to peer_groups_opportunity.parquet format
for the opportunity peer groups methodology.

Updated to output alpha-3 ISO codes for consistency across the system.
"""

import pandas as pd
import os
from pathlib import Path
import sys

# Add API utils to path for country code conversion
sys.path.append(str(Path(__file__).parent.parent / "api"))
from utils.country_codes import normalize_country_code, bulk_convert_to_alpha3

def main():
    # Paths
    data_dir = Path(__file__).parent.parent / "data" / "out"
    input_file = data_dir / "peer_groups_opportunity.csv"
    output_file = data_dir / "peer_groups_opportunity.parquet"
    
    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist")
        return
    
    # Read the CSV
    df = pd.read_csv(input_file)
    
    print(f"Loaded {len(df)} rows from CSV")
    print("Original columns:", df.columns.tolist())
    print("Sample original data:")
    print(df.head())
    
    # Convert numeric ISO codes to alpha-3
    print("\nConverting numeric ISO codes to alpha-3...")
    
    # Track conversion statistics
    successful_conversions = 0
    failed_conversions = 0
    conversion_log = []
    
    alpha3_codes = []
    for iso_code in df['iso']:
        alpha3_code = normalize_country_code(str(iso_code), "alpha3")
        if alpha3_code:
            alpha3_codes.append(alpha3_code)
            successful_conversions += 1
        else:
            alpha3_codes.append(str(iso_code))  # Keep original if conversion fails
            failed_conversions += 1
            conversion_log.append(f"Failed to convert: {iso_code}")
    
    # Update the dataframe
    df['iso3'] = alpha3_codes
    
    # Remove the old iso column and rename columns for consistency
    df = df.drop('iso', axis=1)
    df = df.rename(columns={'iso3': 'iso3', 'cluster': 'cluster'})
    
    # Reorder columns for consistency with human peer groups
    df = df[['iso3', 'cluster', 'method', 'k', 'year']]
    
    print(f"\nConversion results:")
    print(f"✅ Successful conversions: {successful_conversions}")
    print(f"❌ Failed conversions: {failed_conversions}")
    
    if conversion_log:
        print(f"Failed conversions:")
        for log_entry in conversion_log[:10]:  # Show first 10 failures
            print(f"  {log_entry}")
        if len(conversion_log) > 10:
            print(f"  ... and {len(conversion_log) - 10} more")
    
    # Save as parquet
    df.to_parquet(output_file, index=False)
    
    print(f"\nCreated {output_file} with {len(df)} country-cluster mappings")
    print(f"Unique clusters: {df['cluster'].nunique()}")
    print(f"Unique countries: {df['iso3'].nunique()}")
    
    print(f"\nSample output data:")
    print(df.head(10))
    
    # Validate that all codes are proper alpha-3 where conversion succeeded
    valid_alpha3 = df[df['iso3'].str.match(r'^[A-Z]{3}$', na=False)]
    print(f"\n✅ {len(valid_alpha3)} records have valid alpha-3 codes ({len(valid_alpha3)/len(df)*100:.1f}%)")
    
    # Show cluster distribution
    print(f"\nCluster distribution:")
    cluster_counts = df.groupby('cluster')['iso3'].nunique().sort_values(ascending=False)
    for cluster_id, count in cluster_counts.items():
        print(f"  Cluster {cluster_id}: {count} countries")

if __name__ == "__main__":
    main()