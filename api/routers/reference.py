"""
Reference data router - serves static reference data files for frontend
"""
import json
import os
from fastapi import APIRouter, HTTPException, Response
from pathlib import Path

router = APIRouter()

# Path to reference files
REF_PATH = Path("ui/public/ref")

@router.get("/ref/country_names_cz.json")
def get_country_names(response: Response):
    """Get Czech country names mapping"""
    file_path = REF_PATH / "country_names_cz.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Country names file not found")
    
    # Cache for 1 hour - reference data rarely changes
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.get("/ref/hs6_labels.json")
def get_hs6_labels(response: Response):
    """Get HS6 product labels"""
    file_path = REF_PATH / "hs6_labels.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="HS6 labels file not found")
    
    # Cache for 1 hour - reference data rarely changes
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.get("/ref/country_continents.json")
def get_country_continents(response: Response):
    """Get country to continent mappings"""
    file_path = REF_PATH / "country_continents.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Country continents file not found")
    
    # Cache for 1 hour - reference data rarely changes
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)