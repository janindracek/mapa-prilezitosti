#!/usr/bin/env python3
"""
Debug script to trace data inconsistency:
CZ-Belgium HS6 845180 shows bilateral > world export
"""
import pandas as pd
import os

def check_file(path, desc):
    print(f"\n=== {desc} ===")
    print(f"File: {path}")
    if not os.path.exists(path):
        print("❌ FILE NOT FOUND")
        return None
    
    df = pd.read_parquet(path)
    print(f"✅ Rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    return df

def debug_hs6_845180():
    hs6 = "845180"
    partner = "BEL"
    year = 2023
    
    print("🔍 DEBUGGING HS6 845180 (CZ→Belgium)")
    print(f"Expected: World export >= Bilateral export")
    
    # 1. Check fact_base.parquet
    fact_base = check_file("data/out/fact_base.parquet", "1. FACT BASE")
    if fact_base is not None:
        print(f"\n🔎 Filtering for HS6 {hs6}, year {year}")
        filtered = fact_base[(fact_base["hs6"] == hs6) & (fact_base["year"] == year)]
        print(f"Matching rows: {len(filtered)}")
        
        if len(filtered) > 0:
            print(f"\nColumns in filtered data: {list(filtered.columns)}")
            
            # Check bilateral CZ→BEL
            cz_bel = filtered[filtered["partner_iso3"] == partner]
            if len(cz_bel) > 0:
                bilateral = cz_bel["export_cz_to_partner"].iloc[0]
                world_total = cz_bel["export_cz_total_for_hs6"].iloc[0]
                print(f"📊 FACT_BASE DATA:")
                print(f"   CZ→{partner} bilateral: {bilateral:,.0f}")
                print(f"   CZ→World total: {world_total:,.0f}")
                print(f"   Ratio: {bilateral/world_total:.1%} {'✅' if world_total >= bilateral else '❌'}")
                
                # Show all partners for this HS6
                print(f"\n📋 All partners for HS6 {hs6}:")
                all_partners = filtered[["partner_iso3", "export_cz_to_partner", "export_cz_total_for_hs6"]].copy()
                all_partners = all_partners.sort_values("export_cz_to_partner", ascending=False)
                for _, row in all_partners.head(10).iterrows():
                    print(f"   {row['partner_iso3']}: {row['export_cz_to_partner']:,.0f} (world: {row['export_cz_total_for_hs6']:,.0f})")
                    
                # Verify world total calculation
                manual_world_total = filtered["export_cz_to_partner"].sum()
                print(f"\n🧮 VERIFICATION:")
                print(f"   Stored world total: {world_total:,.0f}")  
                print(f"   Manual sum of bilaterals: {manual_world_total:,.0f}")
                print(f"   Match: {'✅' if abs(world_total - manual_world_total) < 1 else '❌'}")
            else:
                print(f"❌ No data for partner {partner}")
        else:
            print(f"❌ No data for HS6 {hs6}, year {year}")
    
    # 2. Check metrics_enriched.parquet
    metrics = check_file("data/out/metrics_enriched.parquet", "2. METRICS ENRICHED")
    if metrics is not None:
        print(f"\n🔎 Filtering for HS6 {hs6}, year {year}")
        filtered = metrics[(metrics["hs6"] == hs6) & (metrics["year"] == year)]
        print(f"Matching rows: {len(filtered)}")
        
        if len(filtered) > 0:
            cz_bel = filtered[filtered["partner_iso3"] == partner]
            if len(cz_bel) > 0:
                bilateral = cz_bel["export_cz_to_partner"].iloc[0]
                world_total = cz_bel["export_cz_total_for_hs6"].iloc[0]
                print(f"📊 METRICS_ENRICHED DATA:")
                print(f"   CZ→{partner} bilateral: {bilateral:,.0f}")
                print(f"   CZ→World total: {world_total:,.0f}")
                print(f"   Ratio: {bilateral/world_total:.1%} {'✅' if world_total >= bilateral else '❌'}")
    
    # 3. Check signals
    signals = check_file("data/out/top_signals.parquet", "3. TOP SIGNALS")  
    if signals is not None:
        signal_match = signals[
            (signals["hs6"] == hs6) & 
            (signals["partner_iso3"] == partner) &
            (signals["year"] == year)
        ]
        if len(signal_match) > 0:
            print(f"📊 SIGNAL DATA:")
            print(f"   Signal value: {signal_match['value'].iloc[0]:,.0f}")
            print(f"   Signal type: {signal_match['type'].iloc[0]}")

if __name__ == "__main__":
    os.chdir("/Users/janindracek/Documents/mapa-prilezitosti")
    debug_hs6_845180()