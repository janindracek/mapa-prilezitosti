#!/usr/bin/env python3
"""
Convert deployment parquet files to CSV to avoid PyArrow dependency
"""

import pandas as pd
import os

def convert_parquet_to_csv():
    """Convert all deployment parquet files to CSV format"""
    
    parquet_files = [
        'data/deployment/core_trade.parquet',
        'data/deployment/signals_filtered.parquet', 
        'data/deployment/peer_relationships.parquet',
        'data/deployment/metadata.parquet'
    ]
    
    for parquet_path in parquet_files:
        if os.path.exists(parquet_path):
            csv_path = parquet_path.replace('.parquet', '.csv')
            
            print(f"Converting {parquet_path} to {csv_path}")
            
            try:
                df = pd.read_parquet(parquet_path)
                df.to_csv(csv_path, index=False)
                
                # Check sizes
                parquet_size = os.path.getsize(parquet_path) / 1024
                csv_size = os.path.getsize(csv_path) / 1024
                
                print(f"  Parquet: {parquet_size:.1f}KB -> CSV: {csv_size:.1f}KB")
                
            except Exception as e:
                print(f"  Error converting {parquet_path}: {e}")
        else:
            print(f"  Missing: {parquet_path}")
    
    print("\nConversion complete!")

if __name__ == "__main__":
    convert_parquet_to_csv()