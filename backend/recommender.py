from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
import os

BASE_DIR = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.json")


# -------------------------
# Utility: Professional Title Case
# -------------------------
def clean_title(text: str) -> str:
    """
    Convert talking points into polished Title Case suitable for output.
    Also fixes common acronyms like VPN, WAN, KYC, etc.
    """
    text = text.strip()
    if not text:
        return ""

    # Basic Title Case
    result = text.title()

    # Fix acronyms
    replacements = {
        "Vpn": "VPN",
        "Wan": "WAN",
        "Lan": "LAN",
        "Kyc": "KYC",
        "Erp": "ERP",
        "Crm": "CRM",
        "Iot": "IoT",
        "Sms": "SMS",
        "Cctv": "CCTV",
        "Agvs": "AGVs"
    }

    for wrong, right in replacements.items():
        result = result.replace(wrong, right)

    return result


# -------------------------
# Data Class for Products
# -------------------------
@dataclass
class Product:
    id: str
    name: str
    pdf: str
    talk_track: List[str]


# -------------------------
# Load Schema Once
# -------------------------
def _load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

_schema = _load_schema()


# -------------------------
# Load Products
# -------------------------
PRODUCTS: Dict[str, Product] = {}
for pid, pdata in _schema.get("products", {}).items():
    PRODUCTS[pid] = Product(
        id=pid,
        name=pdata.get("name", pid),
        pdf=pdata.get("pdf", f"{pid}.pdf"),
        talk_track=pdata.get("talk_track", []),
    )


# -------------------------
# Load Industry Budget Matrix
# -------------------------
MATRIX: List[Dict[str, Any]] = _schema.get("industry_budget_matrix", [])


# -------------------------
# For Dropdown Lists
# -------------------------
INDUSTRIES: List[str] = sorted({row["industry"] for row in MATRIX})
ALL_PRODUCT_IDS: List[str] = sorted(PRODUCTS.keys())


# -------------------------
# Helpers
# -------------------------
def find_matrix_row(industry: str, budget_band: str) -> Optional[Dict[str, Any]]:
    ind = industry.strip().lower()
    bud = budget_band.strip().lower()

    for row in MATRIX:
        if row["industry"].strip().lower() == ind and row["budget"].strip().lower() == bud:
            return row

    return None


def industry_to_pdf_name(industry: str) -> str:
    """
    Convert industry name into standardized PDF filename.
    Example:
      'Housing & Real Estate' -> 'Housing_Real_Estate.pdf'
    """
    safe = (industry or "").strip()
    for ch in ["&", ",", "/", "\\"]:
        safe = safe.replace(ch, "")
    safe = "_".join(safe.split())
    return f"{safe}.pdf"


# -------------------------
# Recommendation Core Logic
# -------------------------
def recommend_products(
    industry: str,
    budget_band: str,
    bandwidth_mbps: int,       # kept for compatibility
    size: Optional[int],       # kept for compatibility
    sold_ids: List[str],
    top_n: int = 3,
) -> Dict[str, Any]:

    row = find_matrix_row(industry, budget_band)
    if not row:
        raise ValueError(f"No matrix entry found for Industry='{industry}' and Budget='{budget_band}'")

    # Product order EXACTLY as defined in Excel
    product_order = row.get("product_order", [])

    # Industry + budget specific talking points
    product_talk_tracks = row.get("product_talk_tracks", {})

    logic = row.get("logic", "")

    sold = {s.upper() for s in sold_ids}
    final = []

    for pid in product_order:
        pid_norm = pid.strip()
        if not pid_norm:
            continue

        if pid_norm.upper() in sold:
            continue  # skip already sold

        product = PRODUCTS.get(pid_norm)
        if not product:
            continue

        # 🎯 Industry-specific talking points (Option A)
        if pid_norm in product_talk_tracks and product_talk_tracks[pid_norm]:
            raw_points = product_talk_tracks[pid_norm]
        else:
            # fallback ONLY if missing
            raw_points = product.talk_track

        # Apply Title Case formatting
        talking_points = [clean_title(tp) for tp in raw_points if tp.strip()]

        final.append({
            "id": product.id,
            "name": product.name,
            "pdf": product.pdf,
            "talking_points": talking_points
        })

        if len(final) >= top_n:
            break

    return {
        "industry": industry,
        "budget_band": budget_band,
        "logic": logic,
        "recommended": final
    }
