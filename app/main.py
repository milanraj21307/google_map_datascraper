from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    BackgroundTasks,
)
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from io import StringIO
import pandas as pd
import csv

from .database import engine, get_db, SessionLocal
from .models import Company, Base
from .processor import process_company

# -------------------------
# Create database tables
# -------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Google Maps Lead Enrichment System")

# -------------------------
# Serve frontend
# -------------------------
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(500, "Dashboard not found")
    return index_file.read_text(encoding="utf-8")

# -------------------------
# Root health check
# -------------------------
@app.get("/")
def root():
    return {"status": "running"}

# -------------------------
# Helper: safe CSV getter
# -------------------------
def _get(row, *keys):
    for key in keys:
        if key in row and pd.notna(row[key]):
            val = str(row[key]).strip()
            if val:
                return val
    return None

# -------------------------
# BACKGROUND ENRICHMENT
# -------------------------
def enrich_all_companies():
    db = SessionLocal()
    try:
        companies = (
            db.query(Company)
            .filter(Company.processed == False)
            .all()
        )

        for company in companies:
            try:
                process_company(company)
            except Exception:
                company.processing_status = "error"

        db.commit()
    finally:
        db.close()

# -------------------------
# UPLOAD CSV / EXCEL
# -------------------------
@app.post("/upload-csv")
def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = file.filename.lower()

    try:
        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file.file)
        elif filename.endswith(".csv"):
            df = pd.read_csv(
                file.file,
                encoding="latin-1",
                engine="python",
                on_bad_lines="skip",
            )
        else:
            raise HTTPException(400, "Upload CSV or Excel file")
    except Exception as e:
        raise HTTPException(400, str(e))

    df.columns = (
        df.columns.astype(str)
        .str.replace("ï»¿", "")
        .str.strip()
    )

    for _, row in df.iterrows():
        company = Company(
            name=_get(row, "Company name", "Company Name", "Name", "Company"),
            rating=_get(row, "Rating"),
            company_type=_get(row, "Company Type", "Category"),
            phone=_get(row, "Phone Number", "Phone"),
            website=_get(row, "Website", "URL"),
            source=_get(row, "Source") or "google_maps",
            processing_status="pending",
            processed=False,
        )
        db.add(company)

    db.commit()

    background_tasks.add_task(enrich_all_companies)

    return {
        "message": "File uploaded. Enrichment running in background.",
        "rows": len(df),
    }

# -------------------------
# GET COMPANIES
# -------------------------
@app.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.id.desc()).all()

# -------------------------
# PROGRESS
# -------------------------
@app.get("/progress")
def get_progress(db: Session = Depends(get_db)):
    total = db.query(Company).count()
    done = db.query(Company).filter(Company.processing_status == "done").count()
    processing = db.query(Company).filter(Company.processing_status == "processing").count()
    pending = db.query(Company).filter(Company.processing_status == "pending").count()
    error = db.query(Company).filter(Company.processing_status == "error").count()

    percent = int((done / total) * 100) if total else 0

    return {
        "total": total,
        "done": done,
        "processing": processing,
        "pending": pending,
        "error": error,
        "percent": percent,
    }

# -------------------------
# EXPORT CSV
# -------------------------
@app.get("/export-csv")
def export_csv(db: Session = Depends(get_db)):
    companies = db.query(Company).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "State",
        "Name",
        "Address",
        "Phone",
        "Email",
        "Website",
        "Source",
        "CEO/Owner",
        "CEO_Source",
        "Validation_Status",
    ])

    for c in companies:
        writer.writerow([
            c.state,
            c.name,
            c.address,
            c.phone,
            c.email,
            c.website,
            c.source,
            c.ceo,
            c.ceo_source,
            c.validation_status,
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=final_leads.csv"},
    )

# -------------------------
# ACTION ENDPOINTS (Dashboard buttons)
# -------------------------
@app.post("/companies/{company_id}/retry")
def retry_company(company_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")

    company.processed = False
    company.processing_status = "pending"
    db.commit()

    background_tasks.add_task(enrich_all_companies)
    return {"message": "Company re-queued"}

@app.post("/companies/retry-failed")
def retry_failed(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    failed = db.query(Company).filter(Company.processing_status == "error").all()
    for c in failed:
        c.processed = False
        c.processing_status = "pending"
    db.commit()

    background_tasks.add_task(enrich_all_companies)
    return {"message": "Failed companies re-queued", "count": len(failed)}

@app.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")

    db.delete(company)
    db.commit()
    return {"message": "Deleted"}

@app.delete("/companies")
def clear_all(db: Session = Depends(get_db)):
    db.query(Company).delete()
    db.commit()
    return {"message": "All companies deleted"}
