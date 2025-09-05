#!/usr/bin/env python3
"""
Peer Group Validation Script

Validates that every country is included in exactly one peer group for every peer group type.
Identifies any gaps, duplicates, or inconsistencies in peer group assignments.
"""

import pandas as pd
import pycountry
import os
from collections import defaultdict, Counter
from typing import Dict, Set, List, Tuple

def numeric_to_name(iso_numeric):
    """Convert numeric ISO code to country name"""
    try:
        country = pycountry.countries.get(numeric=str(iso_numeric).zfill(3))
        return country.name if country else f'Unknown({iso_numeric})'
    except:
        return f'Unknown({iso_numeric})'

def alpha3_to_name(iso_alpha3):
    """Convert alpha-3 ISO code to country name"""
    try:
        country = pycountry.countries.get(alpha_3=iso_alpha3)
        return country.name if country else f'Unknown({iso_alpha3})'
    except:
        return f'Unknown({iso_alpha3})'

def validate_peer_groups():
    """Main validation function"""
    print("🔍 PEER GROUP VALIDATION REPORT")
    print("=" * 60)
    
    # Define peer group files and their characteristics
    peer_group_configs = {
        "human": {
            "file": "/Users/janindracek/Documents/mapa-prilezitosti/data/out/peer_groups_human.parquet",
            "country_col": "iso3",
            "cluster_col": "cluster",
            "description": "Curated Regional Groups"
        },
        "trade_structure": {
            "file": "/Users/janindracek/Documents/mapa-prilezitosti/data/out/peer_groups_hs2.parquet", 
            "country_col": "country_name",
            "cluster_col": "cluster_id",
            "description": "Trade Structure Groups"
        },
        "opportunity": {
            "file": "/Users/janindracek/Documents/mapa-prilezitosti/data/out/peer_groups_opportunity.parquet",
            "country_col": "iso", 
            "cluster_col": "cluster",
            "description": "Export Opportunity Peers"
        }
    }
    
    all_results = {}
    
    for method, config in peer_group_configs.items():
        print(f"\n📊 {method.upper()} METHODOLOGY - {config['description']}")
        print("-" * 50)
        
        if not os.path.exists(config["file"]):
            print(f"❌ File not found: {config['file']}")
            continue
            
        try:
            df = pd.read_parquet(config["file"])
            print(f"✅ Loaded {len(df)} records from {config['file']}")
            
            # Basic statistics
            clusters = sorted(df[config["cluster_col"]].unique())
            print(f"📈 Clusters: {len(clusters)} total ({min(clusters)} to {max(clusters)})")
            print(f"🌍 Countries: {len(df[config['country_col']].unique())} unique")
            
            # Check for duplicates
            country_counts = df[config["country_col"]].value_counts()
            duplicates = country_counts[country_counts > 1]
            
            if len(duplicates) > 0:
                print(f"⚠️  DUPLICATES FOUND: {len(duplicates)} countries appear multiple times")
                for country, count in duplicates.items():
                    clusters_for_country = df[df[config["country_col"]] == country][config["cluster_col"]].tolist()
                    print(f"   • {country}: {count} times (clusters: {clusters_for_country})")
            else:
                print("✅ No duplicate countries found")
            
            # Analyze cluster distribution  
            cluster_sizes = df.groupby(config["cluster_col"])[config["country_col"]].nunique().sort_values(ascending=False)
            print(f"📊 Cluster sizes (countries per cluster):")
            for cluster_id, size in cluster_sizes.items():
                print(f"   • Cluster {cluster_id}: {size} countries")
            
            # Check for empty clusters
            expected_clusters = set(range(len(clusters)))
            actual_clusters = set(clusters)
            missing_clusters = expected_clusters - actual_clusters
            if missing_clusters:
                print(f"⚠️  Missing cluster IDs: {sorted(missing_clusters)}")
            
            # Show sample countries for each cluster (first 3)
            print(f"🔍 Sample countries by cluster:")
            for cluster_id in sorted(clusters):
                countries_in_cluster = df[df[config["cluster_col"]] == cluster_id][config["country_col"]].tolist()[:3]
                
                if method == "opportunity":
                    # Convert numeric codes to names for opportunity
                    country_names = [numeric_to_name(c) for c in countries_in_cluster]
                elif method == "human":
                    # Convert alpha-3 codes to names for human
                    country_names = [alpha3_to_name(c) for c in countries_in_cluster]
                else:
                    # trade_structure already has country names
                    country_names = countries_in_cluster
                    
                total_in_cluster = len(df[df[config["cluster_col"]] == cluster_id])
                print(f"   • Cluster {cluster_id}: {', '.join(country_names[:3])}{'...' if total_in_cluster > 3 else ''} ({total_in_cluster} total)")
            
            all_results[method] = {
                "total_countries": len(df[config["country_col"]].unique()),
                "total_clusters": len(clusters),
                "duplicates": len(duplicates),
                "cluster_sizes": dict(cluster_sizes),
                "countries": set(df[config["country_col"]].unique())
            }
            
        except Exception as e:
            print(f"❌ Error processing {method}: {e}")
            import traceback
            traceback.print_exc()
    
    # Cross-methodology comparison
    print(f"\n🔄 CROSS-METHODOLOGY COMPARISON")
    print("-" * 50)
    
    if len(all_results) >= 2:
        methods = list(all_results.keys())
        
        # Compare total country counts
        print("📊 Total countries per methodology:")
        for method in methods:
            print(f"   • {method}: {all_results[method]['total_countries']} countries")
        
        # Check for Belgium specifically (user mentioned issue)
        print(f"\n🔍 BELGIUM ANALYSIS:")
        for method in methods:
            if method == "opportunity":
                # Belgium should be numeric code 056
                belgium_codes = ["056", "56", "BEL"]  # Try different formats
                found = False
                for code in belgium_codes:
                    if code in all_results[method]['countries']:
                        print(f"   • {method}: Belgium found as '{code}' ✅")
                        found = True
                        break
                if not found:
                    print(f"   • {method}: Belgium NOT FOUND ❌")
                    # Show first few countries to debug
                    sample_countries = list(all_results[method]['countries'])[:10]
                    print(f"     Sample countries: {sample_countries}")
            elif method == "human":
                if "BEL" in all_results[method]['countries']:
                    print(f"   • {method}: Belgium found as 'BEL' ✅") 
                else:
                    print(f"   • {method}: Belgium NOT FOUND ❌")
            elif method == "trade_structure":
                belgium_names = ["Belgium", "België", "Belgique"]
                found = False
                for name in belgium_names:
                    if name in all_results[method]['countries']:
                        print(f"   • {method}: Belgium found as '{name}' ✅")
                        found = True
                        break
                if not found:
                    print(f"   • {method}: Belgium NOT FOUND ❌")
                    # Show countries that might be Belgium
                    possible_belgium = [c for c in all_results[method]['countries'] if 'belg' in c.lower()]
                    if possible_belgium:
                        print(f"     Possible Belgium matches: {possible_belgium}")
    
    print(f"\n✨ VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    validate_peer_groups()