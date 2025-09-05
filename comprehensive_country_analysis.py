#!/usr/bin/env python3
"""
Comprehensive Country Code Analysis
Analyzes how country codes are used throughout the entire system
"""

import os
import re
import json
from collections import defaultdict

def analyze_file(filepath, content):
    """Analyze country code usage in a single file"""
    findings = []
    
    # Look for country code patterns
    patterns = {
        'alpha3_codes': r'\b[A-Z]{3}\b',  # BEL, DEU, USA
        'numeric_codes': r'\b\d{1,3}\b',  # 56, 203, 276
        'country_names': r'(Belgium|Germany|Czech|France|Italy|United States)',
        'iso_columns': r'(iso|iso3|partner_iso|country_code)',
        'country_params': r'(country=|importer=|partner=)',
    }
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            findings.append({
                'pattern': pattern_name,
                'matches': matches[:10],  # First 10 matches
                'count': len(matches)
            })
    
    return findings

def main():
    print("🔍 COMPREHENSIVE COUNTRY CODE ANALYSIS")
    print("=" * 70)
    
    # Define areas to analyze
    analysis_areas = {
        "API Routers": "/Users/janindracek/Documents/mapa-prilezitosti/api/routers/",
        "API Services": "/Users/janindracek/Documents/mapa-prilezitosti/api/services/",
        "API Core": "/Users/janindracek/Documents/mapa-prilezitosti/api/",
        "ETL Scripts": "/Users/janindracek/Documents/mapa-prilezitosti/etl/",
        "UI Components": "/Users/janindracek/Documents/mapa-prilezitosti/ui/src/components/",
        "UI Core": "/Users/janindracek/Documents/mapa-prilezitosti/ui/src/",
    }
    
    results = defaultdict(list)
    
    for area_name, directory in analysis_areas.items():
        if not os.path.exists(directory):
            continue
            
        print(f"\n📂 {area_name.upper()}")
        print("-" * 50)
        
        # Walk through directory
        for root, dirs, files in os.walk(directory):
            # Skip node_modules, .venv, etc.
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                    filepath = os.path.join(root, file)
                    relative_path = filepath.replace(directory, "")
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        findings = analyze_file(filepath, content)
                        
                        if findings:
                            print(f"  📄 {relative_path}")
                            for finding in findings:
                                if finding['count'] > 2:  # Only show significant usage
                                    print(f"    • {finding['pattern']}: {finding['count']} occurrences")
                                    print(f"      Examples: {finding['matches'][:3]}")
                            
                            results[area_name].append({
                                'file': relative_path,
                                'findings': findings
                            })
                            
                    except Exception as e:
                        print(f"  ❌ {relative_path}: {e}")
    
    # Summary by component type
    print(f"\n📊 SUMMARY BY COMPONENT")
    print("=" * 70)
    
    total_files = sum(len(files) for files in results.values())
    print(f"Total files analyzed: {total_files}")
    
    for area, files in results.items():
        if files:
            print(f"\n{area}: {len(files)} files with country code usage")

if __name__ == "__main__":
    main()