import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration (SQLite default for zero-setup execution, MySQL capable)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'counterfeit.db'}")

# Verification Thresholds
SCORE_GENUINE_THRESHOLD = 82.0   # Score >= 82 => Genuine
SCORE_SUSPECT_THRESHOLD = 55.0   # 55 <= Score < 82 => Suspect; < 55 => Counterfeit

# Supported Denominations & Security Feature Specifications
DENOMINATION_TEMPLATES = {
    "USD_100": {
        "name": "$100 USD Note (Benjamin Franklin)",
        "denomination": "100",
        "currency": "USD",
        "serial_pattern": r"^[A-Z]{2}[0-9]{8}[A-Z]{1}$",
        "serial_example": "KB77391204B",
        "microprint_text": "THE UNITED STATES OF AMERICA 100 USA",
        "microprint_roi": [0.15, 0.45, 0.85, 0.55], # y1, x1, y2, x2 ratios
        "security_thread_roi": [0.0, 0.38, 1.0, 0.42],
        "portrait_roi": [0.2, 0.4, 0.8, 0.7],
        "serial_roi": [0.1, 0.65, 0.25, 0.95],
        "uv_feature_color": "PINK_BLUE_SHIMMER"
    },
    "USD_50": {
        "name": "$50 USD Note (Ulysses S. Grant)",
        "denomination": "50",
        "currency": "USD",
        "serial_pattern": r"^[A-Z]{2}[0-9]{8}[A-Z]{1}$",
        "serial_example": "MB12948572A",
        "microprint_text": "FIFTY USA 50",
        "microprint_roi": [0.20, 0.40, 0.80, 0.50],
        "security_thread_roi": [0.0, 0.48, 1.0, 0.52],
        "portrait_roi": [0.2, 0.35, 0.8, 0.65],
        "serial_roi": [0.1, 0.65, 0.25, 0.95],
        "uv_feature_color": "YELLOW_GREEN_GLOW"
    },
    "INR_500": {
        "name": "₹500 INR Note (Mahatma Gandhi)",
        "denomination": "500",
        "currency": "INR",
        "serial_pattern": r"^[0-9]{1}[A-Z]{2}[0-9]{6}$",
        "serial_example": "7AB123456",
        "microprint_text": "RBI 500 INDIA",
        "microprint_roi": [0.18, 0.42, 0.82, 0.52],
        "security_thread_roi": [0.0, 0.45, 1.0, 0.49],
        "portrait_roi": [0.2, 0.45, 0.8, 0.75],
        "serial_roi": [0.75, 0.6, 0.92, 0.95],
        "uv_feature_color": "GREEN_YELLOW_FLUORESCENCE"
    }
}
