import datetime
import uuid
import base64
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.config import SAMPLES_DIR, BASE_DIR, DENOMINATION_TEMPLATES
from backend.database import init_db, get_db
from backend.models import BanknoteScanLog, FlaggedSerial, SeizureLocation
from backend.cv_pipeline import BanknoteCVPipeline
from backend.model_engine import CounterfeitVerificationEngine
from backend.sample_generator import generate_sample_banknotes

app = FastAPI(
    title="Counterfeit Currency Identification Agent API",
    description="Real-time computer vision & deep learning engine for fake currency verification",
    version="1.0.0"
)

# Enable CORS for cross-platform app & web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CV & AI engines
cv_pipeline = BanknoteCVPipeline()
model_engine = CounterfeitVerificationEngine()

@app.on_event("startup")
def startup_event():
    init_db()
    # Generate sample test banknotes if none exist
    if not (SAMPLES_DIR / "usd_100_genuine.jpg").exists():
        generate_sample_banknotes()

# Serve static frontend dashboard if requested
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def read_root():
    """Serves the frontend SPA index html."""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Counterfeit Currency Identification Agent API operational."}

@app.post("/api/v1/scan")
async def scan_banknote(
    file: Optional[UploadFile] = File(None),
    sample_key: Optional[str] = Form(None),
    template_key: str = Form("USD_100"),
    provided_serial: Optional[str] = Form(None),
    device_id: str = Form("MOBILE_SCANNER_01"),
    operator_id: str = Form("OFFICER_482"),
    latitude: Optional[float] = Form(40.7128),
    longitude: Optional[float] = Form(-74.0060),
    db: Session = Depends(get_db)
):
    """
    Main inspection endpoint: Processes image through skew correction, ROI cropping,
    microprint sharpness analysis, thread verification, UV fluorescence check, and serial OCR validation.
    """
    try:
        # Load image bytes from upload file or sample preset
        if file is not None:
            image_bytes = await file.read()
        elif sample_key:
            sample_path = SAMPLES_DIR / f"{sample_key}.jpg"
            if not sample_path.exists():
                raise HTTPException(status_code=404, detail=f"Sample file {sample_key}.jpg not found.")
            with open(sample_path, "rb") as f:
                image_bytes = f.read()
        else:
            # Fallback default sample
            sample_path = SAMPLES_DIR / "usd_100_counterfeit.jpg"
            if not sample_path.exists():
                generate_sample_banknotes()
            with open(sample_path, "rb") as f:
                image_bytes = f.read()

        # 1. Decode & Skew Correct
        img_raw = cv_pipeline.decode_image(image_bytes)
        img_rectified, skew_corrected = cv_pipeline.correct_skew(img_raw)

        # 2. Extract Regions of Interest (ROI)
        rois = cv_pipeline.extract_rois(img_rectified, template_key)

        # 3. Analyze Microprint Sharpness
        microprint_score, microprint_anomalies = cv_pipeline.analyze_microprint_detail(rois["microprint"])

        # 4. Verify Security Thread Continuity
        thread_score, thread_anomalies = cv_pipeline.verify_security_thread(rois["security_thread"])

        # 5. Evaluate UV Spectrum Response
        uv_score, uv_anomalies, uv_vis_img = cv_pipeline.evaluate_uv_spectrum(img_rectified)

        # 6. Serial Number OCR & Blacklist Database Lookup
        serial_number, serial_score, is_blacklisted, serial_anomalies = model_engine.extract_and_validate_serial(
            rois["serial_number"], template_key, db, provided_serial
        )

        # 7. Decision Aggregation
        all_anomalies = microprint_anomalies + thread_anomalies + uv_anomalies + serial_anomalies
        verdict, overall_confidence = model_engine.calculate_verdict(
            microprint_score, thread_score, uv_score, serial_score, is_blacklisted, all_anomalies
        )

        # 8. Generate Visual Annotations & Data URLs for UI
        annotated_img = cv_pipeline.generate_annotated_scan(img_rectified, template_key, verdict, rois)
        
        annotated_b64 = cv_pipeline.encode_image_to_base64(annotated_img)
        microprint_b64 = cv_pipeline.encode_image_to_base64(rois["microprint"])
        uv_vis_b64 = cv_pipeline.encode_image_to_base64(uv_vis_img)
        thread_b64 = cv_pipeline.encode_image_to_base64(rois["security_thread"])

        # 9. Log Scan to Audit Database
        scan_id = f"SCAN-{uuid.uuid4().hex[:8].upper()}"
        template_info = DENOMINATION_TEMPLATES.get(template_key, DENOMINATION_TEMPLATES["USD_100"])

        scan_log = BanknoteScanLog(
            scan_id=scan_id,
            timestamp=datetime.datetime.utcnow(),
            currency=template_info["currency"],
            denomination=template_info["denomination"],
            verdict=verdict,
            confidence_score=overall_confidence,
            microprint_score=microprint_score,
            security_thread_score=thread_score,
            uv_fluorescence_score=uv_score,
            serial_pattern_score=serial_score,
            serial_number=serial_number,
            serial_is_blacklisted=is_blacklisted,
            device_id=device_id,
            operator_id=operator_id,
            latitude=latitude,
            longitude=longitude,
            location_name="Point of Sale / Mobile Terminal",
            anomalies_detected="; ".join(all_anomalies) if all_anomalies else "None"
        )
        db.add(scan_log)
        db.commit()

        return JSONResponse(content={
            "status": "success",
            "scan_id": scan_id,
            "timestamp": scan_log.timestamp.isoformat(),
            "currency": template_info["currency"],
            "denomination": template_info["denomination"],
            "verdict": verdict,
            "confidence_score": overall_confidence,
            "feature_breakdown": {
                "microprint_score": microprint_score,
                "security_thread_score": thread_score,
                "uv_fluorescence_score": uv_score,
                "serial_pattern_score": serial_score
            },
            "serial_number": serial_number,
            "serial_is_blacklisted": is_blacklisted,
            "anomalies": all_anomalies,
            "visualizations": {
                "annotated_scan_url": annotated_b64,
                "microprint_crop_url": microprint_b64,
                "uv_spectrum_url": uv_vis_b64,
                "security_thread_url": thread_b64
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.get("/api/v1/stats")
def get_stats(db: Session = Depends(get_db)):
    """Returns summary analytics for administrative dashboards."""
    total_scans = db.query(BanknoteScanLog).count()
    counterfeits = db.query(BanknoteScanLog).filter(BanknoteScanLog.verdict == "COUNTERFEIT").count()
    suspects = db.query(BanknoteScanLog).filter(BanknoteScanLog.verdict == "SUSPECT").count()
    genuines = db.query(BanknoteScanLog).filter(BanknoteScanLog.verdict == "GENUINE").count()
    flagged_serials_count = db.query(FlaggedSerial).count()

    detection_rate = round((counterfeits / total_scans * 100.0), 1) if total_scans > 0 else 0.0

    return {
        "total_scans": total_scans,
        "genuine_count": genuines,
        "suspect_count": suspects,
        "counterfeit_count": counterfeits,
        "counterfeit_detection_rate_pct": detection_rate,
        "flagged_serials_registered": flagged_serials_count
    }

@app.get("/api/v1/logs")
def get_scan_logs(limit: int = 20, db: Session = Depends(get_db)):
    """Returns recent scan logs for audit trail verification."""
    logs = db.query(BanknoteScanLog).order_by(BanknoteScanLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "scan_id": log.scan_id,
            "timestamp": log.timestamp.isoformat(),
            "currency": log.currency,
            "denomination": log.denomination,
            "verdict": log.verdict,
            "confidence_score": log.confidence_score,
            "serial_number": log.serial_number,
            "serial_is_blacklisted": log.serial_is_blacklisted,
            "operator_id": log.operator_id,
            "location_name": log.location_name,
            "anomalies": log.anomalies_detected
        }
        for log in logs
    ]

@app.get("/api/v1/seizures")
def get_seizure_locations(db: Session = Depends(get_db)):
    """Returns seizure geographic hotspots for law enforcement mapping."""
    seizures = db.query(SeizureLocation).all()
    return [
        {
            "id": s.id,
            "city_region": s.city_region,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "seizure_count": s.seizure_count,
            "total_face_value": s.total_face_value,
            "risk_zone": s.risk_zone
        }
        for s in seizures
    ]

@app.get("/api/v1/serials")
def get_flagged_serials(db: Session = Depends(get_db)):
    """Returns blacklisted serial numbers registry."""
    serials = db.query(FlaggedSerial).order_by(FlaggedSerial.date_added.desc()).all()
    return [
        {
            "serial_number": s.serial_number,
            "currency": s.currency,
            "denomination": s.denomination,
            "risk_level": s.risk_level,
            "issuing_agency": s.issuing_agency,
            "notes": s.notes,
            "date_added": s.date_added.strftime("%Y-%m-%d")
        }
        for s in serials
    ]

@app.post("/api/v1/serials")
def add_flagged_serial(
    serial_number: str = Form(...),
    currency: str = Form("USD"),
    denomination: str = Form("100"),
    risk_level: str = Form("HIGH"),
    issuing_agency: str = Form("Field Patrol Unit"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Registers a new blacklisted serial number in law enforcement database."""
    existing = db.query(FlaggedSerial).filter(FlaggedSerial.serial_number == serial_number.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Serial number is already blacklisted.")

    new_serial = FlaggedSerial(
        serial_number=serial_number.strip().upper(),
        currency=currency,
        denomination=denomination,
        risk_level=risk_level,
        issuing_agency=issuing_agency,
        notes=notes
    )
    db.add(new_serial)
    db.commit()
    return {"status": "success", "message": f"Serial number '{serial_number}' successfully blacklisted."}
