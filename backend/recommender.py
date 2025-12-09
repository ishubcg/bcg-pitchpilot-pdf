from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
import os

BASE_DIR = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.json")


@dataclass
class Product:
    id: str
    name: str
    pdf: str
    talk_track: List[str]


# ---------- Load schema ----------

def _load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_schema = _load_schema()

# products is a dict in schema.json
PRODUCTS: Dict[str, Product] = {}
for pid, pdata in _schema.get("products", {}).items():
    PRODUCTS[pid] = Product(
        id=pid,
        name=pdata.get("name", pid),
        pdf=pdata.get("pdf", f"{pid}.pdf"),
        talk_track=pdata.get("talk_track", []),
    )

# matrix is a list of rows
MATRIX: List[Dict[str, Any]] = _schema.get("industry_budget_matrix", [])

# industries for dropdown
INDUSTRIES: List[str] = sorted(
    {row.get("industry") for row in MATRIX if row.get("industry")}
)

# product IDs for “already sold” list
ALL_PRODUCT_IDS: List[str] = sorted(PRODUCTS.keys())


# ---------- Helpers ----------

def find_matrix_row(industry: str, budget_band: str) -> Optional[Dict[str, Any]]:
    """Find the matrix row for (industry, budget_band)."""
    ind_norm = (industry or "").strip().lower()
    bud_norm = (budget_band or "").strip().lower()
    for row in MATRIX:
        if (
            (row.get("industry", "").strip().lower() == ind_norm)
            and (row.get("budget", "").strip().lower() == bud_norm)
        ):
            return row
    return None


def industry_to_pdf_name(industry: str) -> str:
    """
    Convert an industry label into a standard PDF file name.

    Example mappings:
      'Banks' -> 'Banks.pdf'
      'Educational Institutions' -> 'Educational_Institutions.pdf'
      'Housing & Real Estate' -> 'Housing_Real_Estate.pdf'
      'RWAs, Welfare' -> 'RWAs_Welfare.pdf'
    """
    safe = (industry or "").strip()
    # remove special punctuation that shouldn't appear in filenames
    for ch in ["&", ",", "/", "\\"]:
        safe = safe.replace(ch, "")
    # collapse whitespace to underscores
    safe = "_".join(safe.split())
    return f"{safe}.pdf"


# ---------- Recommendation API ----------

def recommend_products(
    industry: str,
    budget_band: str,
    bandwidth_mbps: int,          # kept for compatibility, not used right now
    size: Optional[int],          # kept for compatibility, not used right now
    sold_ids: List[str],
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Returns a dict with:
        {
          "industry": ...,
          "budget_band": "Low/Medium/High",
          "logic": "...",
          "industry_talk_track": [...],
          "recommended": [ {id, name, pdf, talking_points}, ... ]
        }
    """
    row = find_matrix_row(industry, budget_band)
    if row is None:
        raise ValueError(f"No recommendation matrix entry for {industry} / {budget_band}")

    product_order: List[str] = row.get("product_order", [])
    logic: str = row.get("logic", "")
    industry_talk_track: List[str] = row.get("talk_track", [])

    sold_set = {(s or "").strip().upper() for s in sold_ids}

    recommended: List[Dict[str, Any]] = []
    for pid in product_order:
        pid_norm = (pid or "").strip()
        if not pid_norm:
            continue
        if pid_norm.upper() in sold_set:
            continue  # skip already-sold
        p = PRODUCTS.get(pid_norm)
        if not p:
            continue
        entry = {
            "id": p.id,
            "name": p.name,
            "pdf": p.pdf,
            "talking_points": p.talk_track,
        }
        recommended.append(entry)
        if len(recommended) >= top_n:
            break

    return {
        "industry": industry,
        "budget_band": budget_band,
        "logic": logic,
        "industry_talk_track": industry_talk_track,
        "recommended": recommended,
    }
