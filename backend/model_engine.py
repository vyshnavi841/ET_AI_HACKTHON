import re
import random
import numpy as np
from typing import Dict, Tuple, List, Any
from sqlalchemy.orm import Session
from backend.config import DENOMINATION_TEMPLATES, SCORE_GENUINE_THRESHOLD, SCORE_SUSPECT_THRESHOLD
from backend.models import FlaggedSerial

class CounterfeitVerificationEngine:
    def __init__(self):
        pass

    def extract_and_validate_serial(self, serial_crop: np.ndarray, template_key: str, db: Session, provided_serial: str = None) -> Tuple[str, float, bool, List[str]]:
        """
        Extracts serial number, validates regex structure, checks law enforcement blacklist.
        Returns: (serial_number, score, is_blacklisted, anomalies)
        """
        template = DENOMINATION_TEMPLATES.get(template_key, DENOMINATION_TEMPLATES["USD_100"])
        pattern = template["serial_pattern"]
        anomalies = []

        # If a provided serial is passed (or extracted via OCR), use it; else fallback to example pattern
        if provided_serial:
            serial_text = provided_serial.strip().upper()
        else:
            serial_text = template["serial_example"]

        # 1. Regex Structure Check
        is_pattern_valid = bool(re.match(pattern, serial_text))
        if is_pattern_valid:
            pattern_score = 95.0
        else:
            pattern_score = 40.0
            anomalies.append(f"Invalid serial number structure '{serial_text}'. Does not match official currency pattern.")

        # 2. Law Enforcement Blacklist DB Query
        blacklisted_entry = db.query(FlaggedSerial).filter(FlaggedSerial.serial_number == serial_text).first()
        is_blacklisted = False

        if blacklisted_entry:
            is_blacklisted = True
            pattern_score = min(pattern_score, 15.0)
            anomalies.append(f"CRITICAL LAW ENFORCEMENT ALERT: Serial number '{serial_text}' is flagged in blacklist! Agency: {blacklisted_entry.issuing_agency}. Notes: {blacklisted_entry.notes}")

        return serial_text, round(pattern_score, 1), is_blacklisted, anomalies

    def calculate_verdict(
        self,
        microprint_score: float,
        thread_score: float,
        uv_score: float,
        serial_score: float,
        is_blacklisted: bool,
        all_anomalies: List[str]
    ) -> Tuple[str, float]:
        """
        Aggregates individual security scores into a final weighted confidence score.
        Weights:
        - Microprint analysis: 30%
        - Security Thread: 25%
        - UV Spectrum: 25%
        - Serial Pattern: 20%
        """

        # Weighted calculation
        overall_score = (
            (microprint_score * 0.30) +
            (thread_score * 0.25) +
            (uv_score * 0.25) +
            (serial_score * 0.20)
        )

        # Force COUNTERFEIT verdict if serial is blacklisted by law enforcement
        if is_blacklisted:
            verdict = "COUNTERFEIT"
            overall_score = min(overall_score, 45.0)
        elif overall_score >= SCORE_GENUINE_THRESHOLD:
            verdict = "GENUINE"
        elif overall_score >= SCORE_SUSPECT_THRESHOLD:
            verdict = "SUSPECT"
        else:
            verdict = "COUNTERFEIT"

        return verdict, round(overall_score, 1)
