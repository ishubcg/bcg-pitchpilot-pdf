from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import tempfile
from starlette.background import BackgroundTask
from datetime import datetime
import csv

from recommender import (
    PRODUCTS,
    INDUSTRIES,
    ALL_PRODUCT_IDS,
    INDUSTRIES_META,
    recommend_products,
)
from pdf_tools import merge_pitch_pdfs

app = FastAPI(title="BCG PitchPilot API (PDF version)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
PRODUCT_FOLDER = os.path.join(BASE_DIR, "product_folder")
SKELETON_FILE = "skeleton.pdf"

LEAD_TRACKER_DIR = os.path.join(BASE_DIR, "lead_tracker")
LEAD_TRACKER_FILE = os.path.join(LEAD_TRACKER_DIR, "leads.csv")


class RecommendRequest(BaseModel):
    industry: str
    annual_budget_inr: int = Field(..., ge=0)
    bandwidth_mbps: int = Field(..., ge=1)
    size: Optional[int] = Field(None, ge=0)
    products_already_sold: List[str] = Field(default_factory=list)
    client_name: Optional[str] = None
    nam_name: Optional[str] = None


class GenerateRequest(RecommendRequest):
    pass


def ensure_lead_tracker_header() -> None:
    os.makedirs(LEAD_TRACKER_DIR, exist_ok=True)
    if not os.path.exists(LEAD_TRACKER_FILE):
        with open(LEAD_TRACKER_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "client_name",
                    "nam_name",
                    "industry",
                    "size",
                    "annual_budget_inr",
                    "products_already_sold",
                    "recommended_products",
                    "combined_pitch_generated",
                ]
            )


def log_lead(
    req: GenerateRequest,
    recommended_products: List[dict],
    combined_generated: bool,
) -> None:
    ensure_lead_tracker_header()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recommended_ids = ",".join([r.get("id", "") for r in recommended_products])
    sold_ids = ",".join(req.products_already_sold or [])
    row = [
        timestamp,
        (req.client_name or "").strip(),
        (req.nam_name or "").strip(),
        req.industry,
        req.size if req.size is not None else "",
        req.annual_budget_inr,
        sold_ids,
        recommended_ids,
        1 if combined_generated else 0,
    ]
    with open(LEAD_TRACKER_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


@app.get("/api/catalog")
def catalog():
    return {
        "products": [
            {"id": p.id, "name": p.name}
            for p in PRODUCTS.values()
        ],
        "industries": INDUSTRIES,
        "product_ids": ALL_PRODUCT_IDS,
    }


@app.post("/api/recommend")
def api_recommend(req: RecommendRequest):
    recs = recommend_products(
        industry=req.industry,
        annual_budget_inr=req.annual_budget_inr,
        bandwidth_mbps=req.bandwidth_mbps,
        size=req.size,
        sold_ids=req.products_already_sold,
        top_n=3,
    )
    if not recs:
        raise HTTPException(status_code=400, detail="No suitable products for given inputs.")
    return {"recommended": recs}


@app.post("/api/generate")
def generate(req: GenerateRequest):
    recs = recommend_products(
        industry=req.industry,
        annual_budget_inr=req.annual_budget_inr,
        bandwidth_mbps=req.bandwidth_mbps,
        size=req.size,
        sold_ids=req.products_already_sold,
        top_n=3,
    )
    if not recs:
        raise HTTPException(status_code=400, detail="No suitable products for given inputs.")

    product_files = [r["pdf"] for r in recs if r.get("pdf")]
    if not product_files:
        raise HTTPException(status_code=500, detail="No PDF files mapped for recommendations.")

    skeleton_full = os.path.join(PRODUCT_FOLDER, SKELETON_FILE)
    if not os.path.exists(skeleton_full):
        raise HTTPException(status_code=500, detail=f"Skeleton PDF not found at {skeleton_full}.")

    industry_meta = INDUSTRIES_META.get(req.industry)
    industry_full: Optional[str] = None
    if industry_meta and industry_meta.pdf:
        candidate = os.path.join(PRODUCT_FOLDER, industry_meta.pdf)
        if os.path.exists(candidate):
            industry_full = candidate

    product_full_paths = [os.path.join(PRODUCT_FOLDER, p) for p in product_files]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tmp.name
    tmp.close()

    merge_pitch_pdfs(
        skeleton_pdf=skeleton_full,
        industry_pdf=industry_full,
        product_pdfs=product_full_paths,
        out_path=tmp_path,
    )

    log_lead(req, recs, combined_generated=True)

    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename="final_recommended_pitch.pdf",
        background=BackgroundTask(lambda: os.remove(tmp_path)),
    )
