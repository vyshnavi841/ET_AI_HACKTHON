import datetime
from backend.models import Base, engine, SessionLocal, FlaggedSerial, SeizureLocation, BanknoteScanLog

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed Blacklisted Serial Numbers if empty
    if db.query(FlaggedSerial).count() == 0:
        seed_serials = [
            FlaggedSerial(serial_number="KB77391204B", currency="USD", denomination="100", risk_level="CRITICAL", issuing_agency="Secret Service Syndicate Registry", notes="Cloned master plate identified in Operation Paper Trail."),
            FlaggedSerial(serial_number="MB12948572A", currency="USD", denomination="50", risk_level="HIGH", issuing_agency="Interpol Cyber Crimes", notes="Repeated double-print anomaly batch."),
            FlaggedSerial(serial_number="7AB123456", currency="INR", denomination="500", risk_level="CRITICAL", issuing_agency="Reserve Bank Enforcement", notes="High-quality offset counterfeit print series."),
            FlaggedSerial(serial_number="FX99182371C", currency="USD", denomination="100", risk_level="HIGH", issuing_agency="Federal Reserve Police", notes="Identified in regional transit node seizure."),
        ]
        db.add_all(seed_serials)

    # Seed Seizure Hotspots for Geo Mapping if empty
    if db.query(SeizureLocation).count() == 0:
        seed_locations = [
            SeizureLocation(city_region="New York Financial District", latitude=40.7074, longitude=-74.0113, seizure_count=142, total_face_value=14200.0, risk_zone="RED"),
            SeizureLocation(city_region="Los Angeles Commercial Port", latitude=33.7423, longitude=-118.2704, seizure_count=98, total_face_value=9800.0, risk_zone="RED"),
            SeizureLocation(city_region="Chicago Transit Hub", latitude=41.8781, longitude=-87.6298, seizure_count=45, total_face_value=4500.0, risk_zone="AMBER"),
            SeizureLocation(city_region="Miami International Gateway", latitude=25.7959, longitude=-80.2870, seizure_count=210, total_face_value=21000.0, risk_zone="RED"),
            SeizureLocation(city_region="Dallas Logistics Terminal", latitude=32.7767, longitude=-96.7970, seizure_count=32, total_face_value=3200.0, risk_zone="GREEN"),
        ]
        db.add_all(seed_locations)

    # Seed Sample Initial Logs if empty
    if db.query(BanknoteScanLog).count() == 0:
        seed_logs = [
            BanknoteScanLog(
                scan_id="SCAN-90812-A",
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
                currency="USD", denomination="100", verdict="GENUINE", confidence_score=94.5,
                microprint_score=95.0, security_thread_score=96.0, uv_fluorescence_score=92.0, serial_pattern_score=95.0,
                serial_number="KB10293847A", serial_is_blacklisted=False, device_id="MOBILE_OFFICER_12", operator_id="AGENT_SMITH",
                latitude=40.7128, longitude=-74.0060, location_name="NYC Sub-Station 4", anomalies_detected="None"
            ),
            BanknoteScanLog(
                scan_id="SCAN-90813-B",
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1, minutes=15),
                currency="USD", denomination="100", verdict="COUNTERFEIT", confidence_score=38.2,
                microprint_score=25.0, security_thread_score=40.0, uv_fluorescence_score=30.0, serial_pattern_score=58.0,
                serial_number="KB77391204B", serial_is_blacklisted=True, device_id="POS_TERMINAL_88", operator_id="TELLER_JONES",
                latitude=40.7074, longitude=-74.0113, location_name="Wall St Bank Branch", anomalies_detected="Microprint blurry; Security thread broken; Blacklisted serial number."
            ),
            BanknoteScanLog(
                scan_id="SCAN-90814-C",
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                currency="USD", denomination="50", verdict="SUSPECT", confidence_score=68.4,
                microprint_score=62.0, security_thread_score=70.0, uv_fluorescence_score=65.0, serial_pattern_score=76.0,
                serial_number="MB12948572A", serial_is_blacklisted=True, device_id="MOBILE_OFFICER_05", operator_id="OFFICER_DAVIS",
                latitude=33.7423, longitude=-118.2704, location_name="LA Harbor Customs", anomalies_detected="Low UV luminescence intensity; Blacklisted serial flag."
            )
        ]
        db.add_all(seed_logs)

    db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
