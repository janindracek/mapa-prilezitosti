from fastapi import APIRouter

from api.data.serving import serving_data

router = APIRouter()


@router.get("/map_v2")
def map_v2(hs6: str = None, year: int = 2023, metric: str = 'export_cz_to_partner', top: int = 0):
    """Choropleth data from the single serving layer (all importers).

    Returns [{iso3, name, value, value_fmt, unit}].
    """
    try:
        return serving_data.get_map_data(hs6=hs6, metric=metric, year=year, top=top)
    except Exception as e:
        print(f"Error in map_v2: {e}")
        return []


@router.get("/map")
def map_legacy(hs6: str = None, year: int = 2023, metric: str = 'export_cz_to_partner',
               country: str = None, hs2: str = None):
    """Legacy map endpoint — same data as /map_v2."""
    return map_v2(hs6=hs6, year=year, metric=metric)
