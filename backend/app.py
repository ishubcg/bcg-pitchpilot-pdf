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

# product PDFs folder
if os.path.exists("/data/product_folder"):
    PRODUCT_FOLDER = "/data/product_folder"
else:
    PRODUCT_FOLDER = os.path.join(BASE_DIR, "product_folder")

# lead tracker (prefer persistent disk if available)
if os.path.exists("/data"):
    LEAD_BASE = "/data"
else:
    LEAD_BASE = BASE_DIR

LEAD_TRACKER_DIR = os.path.join(LEAD_BASE, "lead_tracker")
LEAD_TRACKER_FILE = os.path.join(LEAD_TRACKER_DIR, "leads.csv")

SKELETON_FILE = "skeleton.pdf"  # skeleton PDF (first+last pages used)


# ---------- Pydantic models ----------

class RecommendRequest(BaseModel):
    industry: str
    budget_band: str  # "Low", "Medium", "High"
    bandwidth_mbps: int = Field(100, ge=1)   # kept for compatibility
    size: Optional[int] = Field(None, ge=0)
    products_already_sold: List[str] = Field(default_factory=list)
    client_name: Optional[str] = None
    nam_name: Optional[str] = None


class GenerateRequest(RecommendRequest):
    pass


# ---------- Lead tracker helpers ----------

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
                    "budget_band",
                    "size",
                    "products_already_sold",
                    "recommended_products",
                    "combined_pitch_generated",
                ]
            )


def log_lead(
    req: GenerateRequest,
    budget_band: str,
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
        budget_band,
        req.size if req.size is not None else "",
        sold_ids,
        recommended_ids,
        1 if combined_generated else 0,
    ]
    with open(LEAD_TRACKER_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


# ---------- API endpoints ----------

@app.get("/api/catalog")
def catalog():
    """
    Used by the frontend to populate:
      - Industry dropdown
      - Products already sold dropdown (with full names)
    """
    return {
        "products": [
            {"id": pid, "name": p.name}
            for pid, p in PRODUCTS.items()
        ],
        "industries": INDUSTRIES,
        # for "already sold" selector we send id + name pairs
        "product_ids": [
            {"id": pid, "name": PRODUCTS[pid].name}
            for pid in ALL_PRODUCT_IDS
        ],
        # static budget bands for the UI
        "budget_bands": ["Low", "Medium", "High"],
    }


@app.post("/api/recommend")
def api_recommend(req: RecommendRequest):
    try:
        result = recommend_products(
            industry=req.industry,
            budget_band=req.budget_band,
            bandwidth_mbps=req.bandwidth_mbps,
            size=req.size,
            sold_ids=req.products_already_sold,
            top_n=3,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result["recommended"]:
        raise HTTPException(status_code=400, detail="No suitable products for given inputs.")

    return {
        "recommended": result["recommended"],
        "industry": result["industry"],
        "budget_band": result["budget_band"],
        "logic": result["logic"],
        "industry_talk_track": result["industry_talk_track"],
    }


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        result = recommend_products(
            industry=req.industry,
            budget_band=req.budget_band,
            bandwidth_mbps=req.bandwidth_mbps,
            size=req.size,
            sold_ids=req.products_already_sold,
            top_n=3,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    recs = result["recommended"]
    if not recs:
        raise HTTPException(status_code=400, detail="No suitable products for given inputs.")

    # Collect product PDF filenames
    product_files = [r["pdf"] for r in recs if r.get("pdf")]
    if not product_files:
        raise HTTPException(status_code=500, detail="No PDF files mapped for recommendations.")

    skeleton_full = os.path.join(PRODUCT_FOLDER, SKELETON_FILE)
    if not os.path.exists(skeleton_full):
        raise HTTPException(status_code=500, detail=f"Skeleton PDF not found at {skeleton_full}.")

    # At the moment, no separate industry PDF is passed. You can add later.
    industry_full = None

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

    log_lead(req, result["budget_band"], recs, combined_generated=True)

    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename="final_recommended_pitch.pdf",
        background=BackgroundTask(lambda: os.remove(tmp_path)),
    )


@app.get("/api/product-pitch/{product_id}")
def download_product_pitch(product_id: str):
    pid = product_id.strip().upper()

    if pid not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Invalid product ID")

    pdf_name = PRODUCTS[pid].pdf
    pdf_path = os.path.join(PRODUCT_FOLDER, pdf_name)

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Product PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{PRODUCTS[pid].name}.pdf"
    )

