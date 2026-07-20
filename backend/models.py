import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BanknoteScanLog(Base):
    __tablename__ = "banknote_scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(50), unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    currency = Column(String(10), default="USD")
    denomination = Column(String(20), default="100")
    verdict = Column(String(20)) # GENUINE, SUSPECT, COUNTERFEIT
    confidence_score = Column(Float)
    
    # Micro scores
    microprint_score = Column(Float)
    security_thread_score = Column(Float)
    uv_fluorescence_score = Column(Float)
    serial_pattern_score = Column(Float)
    
    serial_number = Column(String(50), index=True)
    serial_is_blacklisted = Column(Boolean, default=False)
    
    device_id = Column(String(50), default="SCANNER_FIELD_01")
    operator_id = Column(String(50), default="OFFICER_482")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(100), default="Point of Sale / Field Patrol")
    anomalies_detected = Column(Text, nullable=True)

class FlaggedSerial(Base):
    __tablename__ = "flagged_serials"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String(50), unique=True, index=True)
    currency = Column(String(10))
    denomination = Column(String(20))
    risk_level = Column(String(20), default="HIGH") # CRITICAL, HIGH, MEDIUM
    issuing_agency = Column(String(100), default="Federal Reserve / Interpol")
    date_added = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)

class SeizureLocation(Base):
    __tablename__ = "seizure_locations"

    id = Column(Integer, primary_key=True, index=True)
    city_region = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    seizure_count = Column(Integer, default=1)
    total_face_value = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    risk_zone = Column(String(20), default="RED") # RED, AMBER, GREEN
