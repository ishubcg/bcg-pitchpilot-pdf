from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
import os

print("RUNNING RECOMMENDER FROM:", __file__)
BASE_DIR = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.json")



@dataclass
class Product:
    id: str
    name: str
    pdf: str
    talk_track: List[str]


# ---------- Load schema ONCE ----------
def _load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

_schema = _load_schema()



# ---------- Products ----------
PRODUCTS: Dict[str, Product] = {
    pid: Product(
        id=pid,
        name=pdata.get("name", pid),
        pdf=pdata.get("pdf", f"{pid}.pdf"),
        talk_track=pdata.get("talk_track", []),
    )
    for pid, pdata in _schema.get("products", {}).items()
}

# ---------- Matrix ----------
# THIS NOW READS UPDATED MATRIX WITH product_talk_tracks INCLUDED
MATRIX: List[Dict[str, Any]] = _schema.get("industry_budget_matrix", [])

# ---------- Lists ----------
INDUSTRIES: List[str] = sorted({row["industry"] for row in MATRIX})
ALL_PRODUCT_IDS: List[str] = sorted(PRODUCTS.keys())


# ---------- Helper ----------
def find_matrix_row(industry: str, budget_band: str) -> Optional[Dict[str, Any]]:
    ind = industry.strip().lower()
    bud = budget_band.strip().lower()

    for row in MATRIX:
        if row["industry"].strip().lower() == ind and row["budget"].strip().lower() == bud:
            return row
    return None


def industry_to_pdf_name(industry: str) -> str:
    safe = (industry or "").strip()
    for ch in ["&", ",", "/", "\\"]:
        safe = safe.replace(ch, "")
    safe = "_".join(safe.split())
    return f"{safe}.pdf"


# ---------- Recommendation ----------
def recommend_products(
    industry: str,
    budget_band: str,
    bandwidth_mbps: int,
    size: Optional[int],
    sold_ids: List[str],
    top_n: int = 3,
) -> Dict[str, Any]:

    row = find_matrix_row(industry, budget_band)
    if not row:
        raise ValueError(f"No matrix entry for industry={industry}, budget={budget_band}")

    product_order: List[str] = row.get("product_order", [])
    product_talk_tracks: Dict[str, List[str]] = row.get("product_talk_tracks", {})

    sold = {s.upper() for s in sold_ids}
    final_recommendations = []

    for pid in product_order:
        if pid.upper() in sold:
            continue

        product = PRODUCTS.get(pid)
        if not product:
            continue

        # use industry-specific talk if present
        if pid in product_talk_tracks and product_talk_tracks[pid]:
            talk_points = product_talk_tracks[pid]
            print("DEBUG TALK:", pid, talk_points)
        else:
            talk_points = product.talk_track  # fallback only if missing

        final_recommendations.append({
            "id": product.id,
            "name": product.name,
            "pdf": product.pdf,
            "talking_points": talk_points
        })

        if len(final_recommendations) >= top_n:
            break
    

    return {
        "industry": industry,
        "budget_band": budget_band,
        "logic": row.get("logic", ""),
        "recommended": final_recommendations
    }

    

