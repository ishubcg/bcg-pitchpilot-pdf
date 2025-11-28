import os
from typing import List, Optional
from PyPDF2 import PdfReader, PdfWriter


def merge_pitch_pdfs(
    skeleton_pdf: str,
    industry_pdf: Optional[str],
    product_pdfs: List[str],
    out_path: str,
) -> str:
    """
    Merge PDFs into final pitch in this order:

      1. First 2 pages of skeleton (cover + intro, for example)
      2. All pages of industry_pdf (if provided)
      3. All pages of each product pdf (in order)
      4. Last 2 pages of skeleton (e.g. summary + next steps)

    Assumes skeleton has at least 4 pages.
    """
    if not os.path.exists(skeleton_pdf):
        raise FileNotFoundError(f"Skeleton PDF not found: {skeleton_pdf}")

    writer = PdfWriter()

    # --- Skeleton ---
    skel_reader = PdfReader(skeleton_pdf)
    total_skel_pages = len(skel_reader.pages)
    if total_skel_pages < 4:
        raise ValueError(
            "Skeleton PDF must have at least 4 pages (first 2 + last 2)."
        )

    # 1) First 2 pages
    first_count = min(2, total_skel_pages)  # safety, though we require >=4
    for i in range(first_count):
        writer.add_page(skel_reader.pages[i])

    # 2) Industry deck (all pages)
    if industry_pdf and os.path.exists(industry_pdf):
        ind_reader = PdfReader(industry_pdf)
        for page in ind_reader.pages:
            writer.add_page(page)

    # 3) Product decks (all pages)
    for path in product_pdfs:
        if not os.path.exists(path):
            continue
        prod_reader = PdfReader(path)
        for page in prod_reader.pages:
            writer.add_page(page)

    # 4) Last 2 pages
    last_count = min(2, total_skel_pages)  # normally 2
    for i in range(total_skel_pages - last_count, total_skel_pages):
        writer.add_page(skel_reader.pages[i])

    # Write out merged PDF
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        writer.write(f)

    return out_path
