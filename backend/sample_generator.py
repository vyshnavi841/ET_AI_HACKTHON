import cv2
import numpy as np
from pathlib import Path
from backend.config import SAMPLES_DIR

def generate_sample_banknotes():
    """Generates synthetic high-resolution sample banknotes for testing."""
    print("Generating synthetic banknote samples in:", SAMPLES_DIR)

    # 1. $100 USD Genuine Banknote
    img_usd_genuine = create_banknote_base("UNITED STATES OF AMERICA", "$100", "KB10293847A", (195, 215, 205), is_counterfeit=False)
    cv2.imwrite(str(SAMPLES_DIR / "usd_100_genuine.jpg"), img_usd_genuine)

    # 2. $100 USD Counterfeit Banknote (Blurry microprint, broken thread, blacklisted serial)
    img_usd_counterfeit = create_banknote_base("UNITED STATES OF AMERICA", "$100", "KB77391204B", (195, 215, 205), is_counterfeit=True)
    cv2.imwrite(str(SAMPLES_DIR / "usd_100_counterfeit.jpg"), img_usd_counterfeit)

    # 3. $50 USD Suspect Banknote
    img_usd_suspect = create_banknote_base("UNITED STATES OF AMERICA", "$50", "MB12948572A", (200, 220, 210), is_counterfeit=False, force_suspect=True)
    cv2.imwrite(str(SAMPLES_DIR / "usd_50_suspect.jpg"), img_usd_suspect)

    # 4. ₹500 INR Counterfeit Banknote
    img_inr_counterfeit = create_banknote_base("RESERVE BANK OF INDIA", "₹500", "7AB123456", (210, 210, 200), is_counterfeit=True)
    cv2.imwrite(str(SAMPLES_DIR / "inr_500_counterfeit.jpg"), img_inr_counterfeit)

    print("Sample generation complete. Files saved successfully.")

def create_banknote_base(header: str, denomination: str, serial: str, bg_color: tuple, is_counterfeit: bool = False, force_suspect: bool = False) -> np.ndarray:
    w, h = 1000, 450
    img = np.full((h, w, 3), bg_color, dtype=np.uint8)

    # Add guilloche/pattern border
    cv2.rectangle(img, (15, 15), (w - 15, h - 15), (60, 100, 60), 3)
    cv2.rectangle(img, (25, 25), (w - 25, h - 25), (120, 160, 120), 1)

    # Micro-lines background texture
    for y in range(30, h - 30, 8):
        cv2.line(img, (30, y), (w - 30, y), (bg_color[0] - 15, bg_color[1] - 10, bg_color[2] - 15), 1)

    # Header & Denomination Text
    cv2.putText(img, header, (220, 60), cv2.FONT_HERSHEY_TRIPLEX, 0.9, (30, 70, 30), 2, cv2.LINE_AA)
    cv2.putText(img, denomination, (50, 110), cv2.FONT_HERSHEY_DUPLEX, 1.8, (20, 80, 20), 3, cv2.LINE_AA)
    cv2.putText(img, denomination, (w - 160, h - 50), cv2.FONT_HERSHEY_DUPLEX, 1.8, (20, 80, 20), 3, cv2.LINE_AA)

    # Portrait Circle (Watermark)
    cv2.circle(img, (550, 225), 100, (160, 180, 160), -1)
    cv2.circle(img, (550, 225), 100, (40, 80, 40), 2)
    cv2.putText(img, "PORTRAIT ROI", (485, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 80, 40), 1, cv2.LINE_AA)

    # Microprint Region
    micro_x1, micro_y1 = 450, 225
    micro_x2, micro_y2 = 850, 245
    cv2.rectangle(img, (micro_x1, micro_y1), (micro_x2, micro_y2), (220, 230, 220), -1)
    
    if is_counterfeit:
        # Blurry / smudged microprint simulation
        blur_box = np.full((micro_y2 - micro_y1, micro_x2 - micro_x1, 3), (170, 180, 170), dtype=np.uint8)
        cv2.putText(blur_box, "MICROPRINT BLUR INKJET FAKE 100 USA", (10, 15), cv2.FONT_HERSHEY_PLAIN, 0.7, (100, 110, 100), 1)
        blur_box = cv2.GaussianBlur(blur_box, (9, 9), 4.0)
        img[micro_y1:micro_y2, micro_x1:micro_x2] = blur_box
    else:
        # Ultra-sharp microprint text
        cv2.putText(img, "THE UNITED STATES OF AMERICA 100 USA 100 USA 100 USA", (micro_x1 + 5, micro_y1 + 14), cv2.FONT_HERSHEY_PLAIN, 0.7, (10, 40, 10), 1, cv2.LINE_AA)

    # Security Thread Band (Vertical)
    thread_x = 380
    if is_counterfeit:
        # Broken / faint thread
        cv2.line(img, (thread_x, 30), (thread_x, 150), (140, 140, 140), 3)
        cv2.line(img, (thread_x, 280), (thread_x, 420), (140, 140, 140), 3)
    else:
        # Continuous dark metallic security thread
        cv2.line(img, (thread_x, 30), (thread_x, 420), (30, 50, 30), 4)
        cv2.putText(img, "USA 100", (thread_x - 12, 200), cv2.FONT_HERSHEY_PLAIN, 0.6, (200, 255, 200), 1, cv2.LINE_AA)

    # Serial Number Block
    cv2.putText(img, f"SERIAL: {serial}", (650, 80), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (180, 30, 30), 2, cv2.LINE_AA)

    # UV Luminescent Feature Simulation
    if not is_counterfeit and not force_suspect:
        cv2.rectangle(img, (100, 300), (280, 380), (150, 220, 180), -1)
        cv2.putText(img, "UV FLUORESCENT BAND", (105, 345), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 100, 0), 1)

    return img

if __name__ == "__main__":
    generate_sample_banknotes()
