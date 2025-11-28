from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import os

BASE_DIR = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.json")


@dataclass
class Product:
    id: str
    name: str
    industries: List[str]
    min_bandwidth_mbps: int
    budget_tier: str
    pdf: str
    synergy: List[str] = field(default_factory=list)
    ideal_size_min: Optional[int] = None
    ideal_size_max: Optional[int] = None
    ideal_bandwidth_min: Optional[int] = None
    ideal_bandwidth_max: Optional[int] = None
    talk_track: Optional[str] = None


@dataclass
class IndustryMeta:
    id: str
    name: str
    pdf: Optional[str] = None


def _load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_schema = _load_schema()

PRODUCTS: Dict[str, Product] = {
    p["id"]: Product(
        id=p["id"],
        name=p["name"],
        industries=p.get("industries", []),
        min_bandwidth_mbps=p.get("min_bandwidth_mbps", 0),
        budget_tier=p.get("budget_tier", "").lower(),
        pdf=p.get("pdf", ""),
        synergy=p.get("synergy", []),
        ideal_size_min=p.get("ideal_size_min"),
        ideal_size_max=p.get("ideal_size_max"),
        ideal_bandwidth_min=p.get("ideal_bandwidth_min"),
        ideal_bandwidth_max=p.get("ideal_bandwidth_max"),
        talk_track=p.get("talk_track"),
    )
    for p in _schema.get("products", [])
}

INDUSTRIES_META: Dict[str, IndustryMeta] = {
    i["id"]: IndustryMeta(
        id=i["id"],
        name=i.get("name", i["id"]),
        pdf=i.get("pdf"),
    )
    for i in _schema.get("industries", [])
}

INDUSTRIES = sorted(INDUSTRIES_META.keys())
ALL_PRODUCT_IDS = sorted(PRODUCTS.keys())


def inr_to_tier(annual_inr: int) -> str:
    if annual_inr < 2_000_000:
        return "smb"
    if annual_inr < 10_000_000:
        return "mid"
    return "enterprise"


def score_product(
    p: Product,
    industry: str,
    tier: str,
    bandwidth_mbps: int,
    size: Optional[int],
) -> int:
    industry_l = (industry or "").strip().lower()
    p_industries = {i.lower() for i in p.industries}

    score = 0
    if industry_l in p_industries:
        score += 3
    if bandwidth_mbps >= p.min_bandwidth_mbps:
        score += 2
    if p.budget_tier == tier:
        score += 2

    if size is not None and p.ideal_size_min is not None and p.ideal_size_max is not None:
        if p.ideal_size_min <= size <= p.ideal_size_max:
            score += 1

    return score


def build_talking_points(
    p: Product,
    industry: str,
    size: Optional[int],
    bandwidth_mbps: int,
) -> List[str]:
    points: List[str] = []

    if p.talk_track:
        points.append(p.talk_track)

    if size is not None and p.ideal_size_min is not None and p.ideal_size_max is not None:
        if p.ideal_size_min <= size <= p.ideal_size_max:
            points.append(
                f"Client size ({size}) is within the ideal range ({p.ideal_size_min}–{p.ideal_size_max}) for {p.id}."
            )
        else:
            points.append(
                f"Client size ({size}) is outside the primary target range ({p.ideal_size_min}–{p.ideal_size_max}) but still compatible."
            )

    if p.ideal_bandwidth_min is not None and p.ideal_bandwidth_max is not None:
        if p.ideal_bandwidth_min <= bandwidth_mbps <= p.ideal_bandwidth_max:
            points.append(
                f"Requested bandwidth ({bandwidth_mbps} Mbps) fits the sweet spot ({p.ideal_bandwidth_min}–{p.ideal_bandwidth_max} Mbps) for {p.id}."
            )
        else:
            points.append(
                f"{p.id} can scale for {bandwidth_mbps} Mbps; typical deployments are {p.ideal_bandwidth_min}–{p.ideal_bandwidth_max} Mbps."
            )

    if industry in p.industries:
        points.append(f"{p.id} has strong traction in {industry} accounts.")

    return points


def recommend_products(
    industry: str,
    annual_budget_inr: int,
    bandwidth_mbps: int,
    size: Optional[int],
    sold_ids: List[str],
    top_n: int = 3,
):
    tier = inr_to_tier(annual_budget_inr)
    industry_l = (industry or "").strip().lower()
    sold_l = {(s or "").strip().lower() for s in sold_ids}

    candidates = []
    for p in PRODUCTS.values():
        if p.id.lower() in sold_l:
            continue
        s = score_product(p, industry_l, tier, bandwidth_mbps, size)
        if s > 0:
            candidates.append((s, p))

    candidates.sort(key=lambda x: (x[0], x[1].name.lower()), reverse=True)

    MIN_SCORE = 3
    filtered = [(s, p) for s, p in candidates if s >= MIN_SCORE]

    results = []
    for score_val, p in filtered[:top_n]:
        talking_points = build_talking_points(p, industry, size, bandwidth_mbps)
        results.append(
            {
                "id": p.id,
                "name": p.name,
                "score": score_val,
                "pdf": p.pdf,
                "talking_points": talking_points,
            }
        )
    return results
