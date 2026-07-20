import pytest
import numpy as np
import cv2
from backend.cv_pipeline import BanknoteCVPipeline
from backend.model_engine import CounterfeitVerificationEngine
from backend.database import init_db, SessionLocal
from backend.models import FlaggedSerial, Base, engine

@pytest.fixture
def cv_engine():
    return BanknoteCVPipeline()

@pytest.fixture
def model_verifier():
    return CounterfeitVerificationEngine()

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_cv_skew_correction(cv_engine):
    # Create synthetic blank image
    img = np.zeros((450, 1000, 3), dtype=np.uint8)
    rectified, is_corrected = cv_engine.correct_skew(img)
    assert rectified.shape == (450, 1000, 3)

def test_microprint_analysis_sharp_vs_blurry(cv_engine):
    # Sharp image
    sharp_crop = np.zeros((50, 200, 3), dtype=np.uint8)
    for y in range(0, 50, 4):
        cv2.line(sharp_crop, (0, y), (200, y), (255, 255, 255), 1)

    sharp_score, sharp_anomalies = cv_engine.analyze_microprint_detail(sharp_crop)

    # Blurry image
    blurry_crop = cv2.GaussianBlur(sharp_crop, (15, 15), 5.0)
    blurry_score, blurry_anomalies = cv_engine.analyze_microprint_detail(blurry_crop)

    assert sharp_score > blurry_score
    assert len(blurry_anomalies) > 0

def test_serial_blacklist_lookup(model_verifier, db_session):
    # Query non-blacklisted serial
    clean_serial, score, is_blacklisted, anomalies = model_verifier.extract_and_validate_serial(
        None, "USD_100", db_session, provided_serial="KB10293847A"
    )
    assert not is_blacklisted
    assert score >= 90.0

    # Add blacklisted serial to DB
    flagged = FlaggedSerial(serial_number="TEST999999", currency="USD", denomination="100", issuing_agency="Test Agency")
    db_session.add(flagged)
    db_session.commit()

    flagged_serial, score_f, is_blacklisted_f, anomalies_f = model_verifier.extract_and_validate_serial(
        None, "USD_100", db_session, provided_serial="TEST999999"
    )
    assert is_blacklisted_f
    assert score_f <= 20.0
