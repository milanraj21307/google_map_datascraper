from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
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
# Root check
# -------------------------
@app.get("/")
def root():
    return {"status": "running"}

# -------------------------
# Helper: safe column getter
# -------------------------
def _get(row, *keys):
    for key in keys:
        if key in row and pd.notna(row[key]) and str(row[key]).strip():
            return str(row[key]).strip()
    return None

# -------------------------
# BACKGROUND ENRICHMENT
# (only pending / unprocessed rows)
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
            process_company(company)

        db.commit()
    finally:
        db.close()

# -------------------------
# UPLOAD CSV
# -------------------------
@app.post("/upload-csv")
def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = file.filename.lower()

    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file.file)
        elif filename.endswith(".csv"):
            df = pd.read_csv(
                file.file,
                encoding="latin-1",
                engine="python",
                on_bad_lines="skip"
            )
        else:
            raise HTTPException(status_code=400, detail="Upload CSV or Excel")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Clean column names
    df.columns = df.columns.astype(str).str.replace("ï»¿", "").str.strip()

    # Insert rows as PENDING
    for _, row in df.iterrows():
        company = Company(
            name=_get(row, "Company name", "Company Name", "Name", "Company"),
            rating=_get(row, "Rating"),
            company_type=_get(row, "Company Type", "Category"),
            phone=_get(row, "Phone Number", "Phone"),
            website=_get(row, "Website", "URL"),
            source=_get(row, "Source") or "google_maps",

            # 🔥 NEW STATUS FIELDS
            processing_status="pending",
            processed=False,
        )
        db.add(company)

    db.commit()

    # 🚀 NON-BLOCKING enrichment
    background_tasks.add_task(enrich_all_companies)

    return {
        "message": "File uploaded. Enrichment running in background.",
        "rows": len(df)
    }

# -------------------------
# View companies (with status)
# -------------------------
@app.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()

# -------------------------
# Export FINAL CSV
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
