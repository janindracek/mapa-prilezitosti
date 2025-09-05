"""
Peer Group Methodology Documentation

This module documents the three distinct peer group methodologies used in the trade data analysis platform.
Each methodology answers a different economic question and generates different types of signals.

## Peer Group Types

### 1. Geographic/Default Peer Groups (`method="default"`)
**Question**: "How do I perform compared to countries in my geographic region?"
**Methodology**: Countries grouped by geographic proximity, EU membership, or manual curation
**Signal Type**: `Peer_gap_below_median`
**Use Case**: Traditional comparative advantage analysis within regional context
**Data Source**: Pre-defined in configuration files

### 2. Export Profile Matching (`method="kmeans_cosine_hs2_shares"`) 
**Question**: "How do I perform compared to countries with similar export structures?"
**Methodology**: K-means clustering based on cosine similarity of HS2-level export shares
**Signal Type**: `Peer_gap_matching`
**Use Case**: Identify markets where structurally similar economies succeed
**Data Source**: Statistical clustering from `peer_groups_statistical.parquet`

### 3. Opportunity-Based Grouping (`method="opportunity"`)
**Question**: "How do I perform compared to countries with similar export opportunities?"
**Methodology**: Grouping based on export opportunity indices and market potential
**Signal Type**: `Peer_gap_opportunity`  
**Use Case**: Find markets with untapped potential for similar economies
**Data Source**: Opportunity-based clustering algorithms

## Signal Generation Process

1. **Data Loading**: Load trade metrics and peer group assignments
2. **Gap Calculation**: For each country-product-partner combination:
   - Calculate Czech Republic's market share
   - Calculate peer group median market share
   - Compute gap: `CZ_share - peer_median_share`
3. **Threshold Application**: Filter gaps below threshold (typically -0.01 or -1 percentage point)
4. **Signal Classification**: Assign signal type based on peer group methodology
5. **Ranking**: Sort by gap magnitude (intensity) for prioritization

## API Response Format

Signals include methodology information:
```json
{
    "type": "Peer_gap_matching",
    "method": "kmeans_cosine_hs2_shares", 
    "peer_group": "cluster_3",
    "peer_group_label": "Export-similar countries (cluster 3)",
    "intensity": 0.025,
    "value": -0.025,
    "hs6": "123456",
    "partner_iso3": "DEU"
}
```

## Configuration

Peer group methodologies are configured in:
- `data/config.yaml` - Signal thresholds and labels
- `data/out/peer_groups_statistical.parquet` - Statistical clustering results
- `data/out/peer_groups.csv` - Complete peer group assignments

## Future Extensions

To add new peer group methodologies:
1. Add new `method` value to peer group data files
2. Update `_classify_peer_gap_type()` in SignalsService
3. Add corresponding label in `data/config.yaml`
4. Update this documentation
"""

# Methodology constants for programmatic access
PEER_GROUP_METHODOLOGIES = {
    "default": {
        "signal_type": "Peer_gap_below_median",
        "description": "Geographic/regional peer comparison",
        "question": "How do I perform compared to countries in my geographic region?"
    },
    "kmeans_cosine_hs2_shares": {
        "signal_type": "Peer_gap_matching", 
        "description": "Export structure similarity clustering",
        "question": "How do I perform compared to countries with similar export structures?"
    },
    "opportunity": {
        "signal_type": "Peer_gap_opportunity",
        "description": "Export opportunity-based grouping", 
        "question": "How do I perform compared to countries with similar export opportunities?"
    }
}

def get_methodology_info(method: str) -> dict:
    """Get methodology information for a given peer group method."""
    return PEER_GROUP_METHODOLOGIES.get(method, {
        "signal_type": "Unknown",
        "description": f"Unknown methodology: {method}",
        "question": "Unknown analytical framework"
    })