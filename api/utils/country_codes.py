"""
Country Code Utilities

Centralized utilities for handling country code conversions and lookups.
Eliminates duplication across peer group and other modules.
"""

from typing import List, Optional
import pycountry


def normalize_country_code(country: str, target_format: str = "alpha3") -> Optional[str]:
    """
    Normalize country code to target format.
    
    Args:
        country: Country code in any format (alpha2, alpha3, numeric, name)
        target_format: Target format ("alpha2", "alpha3", "numeric", "name")
        
    Returns:
        Normalized country code or None if not found
    """
    if not country:
        return None
        
    try:
        # Try different lookup methods
        country_rec = None
        
        # Try alpha-3 first (most common)
        if len(country) == 3 and country.isalpha():
            country_rec = pycountry.countries.get(alpha_3=country.upper())
        
        # Try alpha-2
        if not country_rec and len(country) == 2 and country.isalpha():
            country_rec = pycountry.countries.get(alpha_2=country.upper())
        
        # Try numeric (both padded and unpadded)
        if not country_rec and country.isdigit():
            # Try padded version first
            padded_code = country.zfill(3)
            country_rec = pycountry.countries.get(numeric=padded_code)
            
            # If padded fails and we have unpadded, try unpadded
            if not country_rec and padded_code != country:
                country_rec = pycountry.countries.get(numeric=country)
        
        # Try name lookup (fuzzy matching)
        if not country_rec:
            try:
                country_rec = pycountry.countries.lookup(country)
            except LookupError:
                pass
        
        if not country_rec:
            return None
            
        # Return in target format
        if target_format == "alpha2":
            return country_rec.alpha_2
        elif target_format == "alpha3":
            return country_rec.alpha_3
        elif target_format == "numeric":
            return country_rec.numeric
        elif target_format == "name":
            return country_rec.name
        else:
            return country_rec.alpha_3  # Default to alpha3
            
    except Exception:
        return None


def get_country_search_codes(country: str, peer_group_type: str) -> List[str]:
    """
    Get list of country codes to search for in different peer group data formats.
    
    Args:
        country: Base country code
        peer_group_type: Type of peer group ("opportunity", "human", "statistical", etc.)
        
    Returns:
        List of country codes to try when searching peer group data
    """
    search_codes = [country]
    
    # Opportunity peer groups use numeric codes
    if peer_group_type.lower() == "opportunity":
        numeric_code = normalize_country_code(country, "numeric")
        if numeric_code:
            search_codes = [numeric_code]
    
    # Statistical and human peer groups typically use alpha-3
    elif peer_group_type.lower() in ["statistical", "human", "kmeans_cosine_hs2_shares"]:
        alpha3_code = normalize_country_code(country, "alpha3")
        if alpha3_code:
            search_codes = [alpha3_code]
    
    # Default peer groups may use various formats
    else:
        alpha3_code = normalize_country_code(country, "alpha3")
        alpha2_code = normalize_country_code(country, "alpha2")
        numeric_code = normalize_country_code(country, "numeric")
        
        search_codes = []
        if alpha3_code:
            search_codes.append(alpha3_code)
        if alpha2_code:
            search_codes.append(alpha2_code)
        if numeric_code:
            search_codes.append(numeric_code)
    
    return search_codes


def convert_numeric_to_alpha3(numeric_codes: List[str]) -> List[str]:
    """
    Convert list of numeric ISO codes to alpha-3.
    
    Args:
        numeric_codes: List of numeric country codes
        
    Returns:
        List of alpha-3 country codes
    """
    alpha3_countries = []
    for code in numeric_codes:
        alpha3_code = normalize_country_code(code, "alpha3")
        alpha3_countries.append(alpha3_code or code)  # Keep original if conversion fails
    return alpha3_countries


def get_country_name(country_code: str) -> Optional[str]:
    """
    Get human-readable country name from any country code format.
    
    Args:
        country_code: Country code in any format
        
    Returns:
        Country name or None if not found
    """
    return normalize_country_code(country_code, "name")


def name_to_iso3(country_name: str) -> Optional[str]:
    """
    Convert country name to ISO3 code.
    
    Args:
        country_name: Country name
        
    Returns:
        ISO3 code or None if not found
    """
    return normalize_country_code(country_name, "alpha3")


def bulk_convert_to_alpha3(values: List[str], source_format: str = "auto") -> List[str]:
    """
    Convert a list of country codes/names to alpha-3 format.
    
    Args:
        values: List of country identifiers
        source_format: Source format hint ("auto", "numeric", "names", "alpha3")
        
    Returns:
        List of alpha-3 codes (keeps original if conversion fails)
    """
    result = []
    for value in values:
        if not value:
            result.append(value)
            continue
            
        alpha3_code = normalize_country_code(str(value), "alpha3")
        result.append(alpha3_code or str(value))
    
    return result


def validate_alpha3_code(code: str) -> bool:
    """
    Validate if a code is a valid alpha-3 country code.
    
    Args:
        code: Country code to validate
        
    Returns:
        True if valid alpha-3 code
    """
    if not code or len(code) != 3 or not code.isalpha():
        return False
        
    try:
        return pycountry.countries.get(alpha_3=code.upper()) is not None
    except Exception:
        return False