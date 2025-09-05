import os
from typing import Callable, Optional, TypeVar, Any, cast as type_cast

T = TypeVar("T")

def env(name: str, default: Optional[T] = None, caster: Optional[Callable[[str], T]] = None) -> Optional[T]:
    """
    Read environment variable NAME.
    - If missing: return DEFAULT.
    - If present and caster is provided: return caster(value), else the raw string.
    On cast failure, return DEFAULT.
    """
    v = os.environ.get(name)
    if v is None:
        return default
    if caster is None:
        # returning raw string but typed as Optional[T] for the checker
        return type_cast(Optional[T], v)
    try:
        return caster(v)
    except Exception:
        return default