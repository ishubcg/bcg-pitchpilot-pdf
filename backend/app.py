from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import os
import tempfile
from datetime import datetime
import csv
from starlette.background import BackgroundTask

from recommender import (
    PRODUCTS,
    INDUSTRIES,
    ALL_PRODUCT_IDS,
    recommend_products,
    industry_to_pdf_name,
)
from pdf_tools import merge_pitch_pdfs

app = FastAPI(title="PitchBot Backend (PDF Generator)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)

# Product folder
PRODUCT_FOLDER = (
    "/data/product_folder"
    if os.path.exists("/data/product_folder")
    else os.path.join(BASE_DIR, "product_folder")
)

# Lead tracker
LEAD_BASE = "/data" if os.path.exists("/data") else BASE_DIR
LEAD_TRACKER_DIR = os.path.join(LEAD_BASE, "lead_tracker")
LEAD_TRACKER_FILE = os.path.join(LEAD_TRACKER_DIR, "leads.csv")

SKELETON_FILE = "skeleton.pdf"


# ---------- MODELS ----------

class RecommendRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)

    client_email: Optional[str] = None  # Optional now

    nam_name: str = Field(..., min_length=1)
    nam_circle: str = Field(..., min_length=1)

    industry: str = Field(..., min_length=1)
    budget_band: str = Field(..., min_length=1)

    size: Optional[int] = Field(None, ge=0)

    products_already_sold: List[str] = Field(default_factory=list)

    bandwidth_mbps: int = 100


class GenerateRequest(RecommendRequest):
    pass


# ---------- LEAD TRACKING ----------

def ensure_lead_tracker_header():
    os.makedirs(LEAD_TRACKER_DIR, exist_ok=True)
    if not os.path.exists(LEAD_TRACKER_FILE):
        with open(LEAD_TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "client_name",
                "company_name",
                "client_email",
                "nam_name",
                "nam_circle",
                "industry",
                "budget_band",
                "size",
                "products_already_sold",
                "recommended_products",
                "combined_pitch_generated"
            ])


def log_lead(req: GenerateRequest, recommended_products: List[dict], combined_generated: bool):
    ensure_lead_tracker_header()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        req.client_name,
        req.company_name,
        req.client_email or "",
        req.nam_name,
        req.nam_circle,
        req.industry,
        req.budget_band,
        req.size or "",
        ",".join(req.products_already_sold or []),
        ",".join([r["id"] for r in recommended_products]),
        1 if combined_generated else 0,
    ]

    with open(LEAD_TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


# ---------- API ----------

@app.get("/api/catalog")
def catalog():
    return {
        "products": [
            {"id": pid, "name": p.name}
            for pid, p in PRODUCTS.items()
        ],
        "industries": INDUSTRIES,
        "product_ids": [
            {"id": pid, "name": PRODUCTS[pid].name}
            for pid in ALL_PRODUCT_IDS
        ],
        "budget_bands": ["Low", "Medium", "High"]
    }
    print("PRODUCT IDS:", list(PRODUCTS.keys()))


@app.post("/api/recommend")
def api_recommend(req: RecommendRequest):
    result = recommend_products(
        req.industry,
        req.budget_band,
        req.bandwidth_mbps,
        req.size,
        req.products_already_sold
    )
    if not result["recommended"]:
        raise HTTPException(400, "No suitable products for given inputs.")

    return result


@app.post("/api/generate")
def generate(req: GenerateRequest):
    result = recommend_products(
        req.industry,
        req.budget_band,
        req.bandwidth_mbps,
        req.size,
        req.products_already_sold
    )

    recs = result["recommended"]
    if not recs:
        raise HTTPException(400, "No recommended products found.")

    skeleton_full = os.path.join(PRODUCT_FOLDER, SKELETON_FILE)

    # Industry page
    industry_pdf_name = industry_to_pdf_name(result["industry"])
    industry_full = os.path.join(PRODUCT_FOLDER, industry_pdf_name)
    if not os.path.exists(industry_full):
        industry_full = None

    product_paths = [
        os.path.join(PRODUCT_FOLDER, r["pdf"])
        for r in recs
    ]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tmp.name
    tmp.close()

    merge_pitch_pdfs(
        skeleton_pdf=skeleton_full,
        industry_pdf=industry_full,
        product_pdfs=product_paths,
        out_path=tmp_path
    )

    log_lead(req, recs, True)

    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename="final_recommended_pitch.pdf",
        background=BackgroundTask(lambda: os.remove(tmp_path)),
    )


@app.get("/api/product-pitch/{product_id}")
def download_pitch(product_id: str):
    pid = product_id.strip()
    if pid not in PRODUCTS:
        raise HTTPException(404, "Invalid product ID")

    pdf_path = os.path.join(PRODUCT_FOLDER, PRODUCTS[pid].pdf)
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{PRODUCTS[pid].name}.pdf"
    )
