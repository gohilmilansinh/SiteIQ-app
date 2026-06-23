from __future__ import annotations

from typing import Any, Dict

import scorer


def score_site(address: str, brand_type: str = "restaurant") -> Dict[str, Any]:
    return scorer.score_site(address, brand_type)