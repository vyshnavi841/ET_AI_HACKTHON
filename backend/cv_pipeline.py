import cv2
import numpy as np
import base64
from typing import Dict, Tuple, List, Any
from backend.config import DENOMINATION_TEMPLATES

class BanknoteCVPipeline:
    def __init__(self):
        pass

    def decode_image(self, image_bytes: bytes) -> np.ndarray:
        """Decodes image raw bytes into an OpenCV BGR image numpy array."""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes into valid OpenCV matrix.")
        return img

    def encode_image_to_base64(self, img: np.ndarray) -> str:
        """Encodes an OpenCV matrix to JPEG base64 data URL string."""
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        b64_str = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"

    def correct_skew(self, img: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Detects banknote outer border contour and applies perspective transform
        to rectify orientation and skew.
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return img, False

        # Find largest rectangular contour matching bill aspect ratio
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        for cnt in contours[:5]:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4 and cv2.contourArea(cnt) > (0.15 * h * w):
                pts = approx.reshape(4, 2)
                # Sort points: top-left, top-right, bottom-right, bottom-left
                rect = self._order_points(pts)
                (tl, tr, br, bl) = rect

                # Compute width and height of transformed rect
                width_A = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                width_B = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                max_width = max(int(width_A), int(width_B))

                height_A = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                height_B = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                max_height = max(int(height_A), int(height_B))

                dst = np.array([
                    [0, 0],
                    [max_width - 1, 0],
                    [max_width - 1, max_height - 1],
                    [0, max_height - 1]
                ], dtype="float32")

                M = cv2.getPerspectiveTransform(rect.astype("float32"), dst)
                warped = cv2.warpPerspective(img, M, (max_width, max_height))
                return cv2.resize(warped, (1000, 450)), True

        # Fallback to standard resize if rectangle detection is ambiguous
        return cv2.resize(img, (1000, 450)), False

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # Top-left
        rect[2] = pts[np.argmax(s)] # Bottom-right

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # Top-right
        rect[3] = pts[np.argmax(diff)] # Bottom-left
        return rect

    def extract_rois(self, img: np.ndarray, template_key: str = "USD_100") -> Dict[str, np.ndarray]:
        """Extracts key regions of interest (Microprint, Security Thread, Serial, Portrait)."""
        template = DENOMINATION_TEMPLATES.get(template_key, DENOMINATION_TEMPLATES["USD_100"])
        h, w = img.shape[:2]

        def get_crop(ratio_box):
            y1 = int(ratio_box[0] * h)
            x1 = int(ratio_box[1] * w)
            y2 = int(ratio_box[2] * h)
            x2 = int(ratio_box[3] * w)
            return img[y1:y2, x1:x2]

        return {
            "microprint": get_crop(template["microprint_roi"]),
            "security_thread": get_crop(template["security_thread_roi"]),
            "portrait": get_crop(template["portrait_roi"]),
            "serial_number": get_crop(template["serial_roi"])
        }

    def analyze_microprint_detail(self, microprint_crop: np.ndarray) -> Tuple[float, List[str]]:
        """
        Analyzes microprint region using Laplacian variance and high-frequency edge analysis.
        Authentic microprint has extremely sharp high-frequency edges (> 120.0 variance).
        Counterfeit inkjet prints appear blurry (< 60.0 variance).
        """
        anomalies = []
        if microprint_crop is None or microprint_crop.size == 0:
            return 30.0, ["Microprint region unreadable or missing."]

        gray = cv2.cvtColor(microprint_crop, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Sobel high frequency edge density
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.sqrt(sobelx**2 + sobely**2)
        edge_density = float(np.mean(edge_magnitude))

        # Score calculation mapped from 0 to 100
        raw_score = min(100.0, (laplacian_var / 2.5) * 0.6 + (edge_density / 0.8) * 0.4)
        score = round(max(10.0, raw_score), 1)

        if score < 55.0:
            anomalies.append(f"Microprint blur detected (Laplacian Variance: {laplacian_var:.1f}). Ink bleed characteristic of counterfeit printing.")
        elif score < 75.0:
            anomalies.append("Microprint edge sharpness borderline.")

        return score, anomalies

    def verify_security_thread(self, thread_crop: np.ndarray) -> Tuple[float, List[str]]:
        """
        Verifies vertical continuity of security thread band and embedded contrast.
        """
        anomalies = []
        if thread_crop is None or thread_crop.size == 0:
            return 20.0, ["Security thread region missing."]

        gray = cv2.cvtColor(thread_crop, cv2.COLOR_BGR2GRAY)
        # Vertical intensity profile across rows
        vertical_profile = np.mean(gray, axis=1)
        variance = float(np.var(vertical_profile))
        min_val = float(np.min(vertical_profile))
        max_val = float(np.max(vertical_profile))
        contrast_range = max_val - min_val

        # Authentic security thread exhibits solid dark line embedded inside paper
        if contrast_range > 40.0 and variance > 50.0:
            score = 92.0 + min(8.0, contrast_range / 10.0)
        elif contrast_range > 20.0:
            score = 65.0
            anomalies.append("Security thread density variation detected.")
        else:
            score = 30.0
            anomalies.append("Security thread continuity broken or missing metallic element.")

        return round(score, 1), anomalies

    def evaluate_uv_spectrum(self, img: np.ndarray) -> Tuple[float, List[str], np.ndarray]:
        """
        Simulates UV luminescence check (checking fluorescent response in green/blue spectrum).
        Generates simulated UV filter visualization image.
        """
        anomalies = []
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Simulate UV filter image (Dark background with glowing reactive security bands)
        uv_simulated = img.copy()
        # Enhance fluorescent blue/pink band luminescence
        blue_mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
        yellow_mask = cv2.inRange(hsv, np.array([20, 50, 50]), np.array([40, 255, 255]))
        fluorescent_mask = cv2.bitwise_or(blue_mask, yellow_mask)

        # Create glowing UV visual effect
        uv_vis = np.zeros_like(img)
        uv_vis[:, :, 0] = cv2.bitwise_and(img[:, :, 0], img[:, :, 0], mask=fluorescent_mask) # B
        uv_vis[:, :, 1] = cv2.bitwise_and(img[:, :, 1] * 2, img[:, :, 1], mask=fluorescent_mask) # G
        uv_vis[:, :, 2] = cv2.bitwise_and(img[:, :, 2] * 2, img[:, :, 2], mask=fluorescent_mask) # R
        
        # Add background UV glow tint
        uv_vis = cv2.addWeighted(uv_vis, 0.85, (img * 0.15).astype(np.uint8), 0.15, 0)

        glow_pixels = cv2.countNonZero(fluorescent_mask)
        total_pixels = img.size / 3
        fluoresce_ratio = (glow_pixels / total_pixels) * 100.0

        if fluoresce_ratio > 1.2:
            score = 92.5
        elif fluoresce_ratio > 0.4:
            score = 68.0
            anomalies.append("Subdued UV security thread luminescence.")
        else:
            score = 42.0
            anomalies.append("Missing or non-reactive UV fluorescent security elements under UV filter.")

        return round(score, 1), anomalies, uv_vis

    def generate_annotated_scan(self, img: np.ndarray, template_key: str, verdict: str, rois: Dict[str, np.ndarray]) -> np.ndarray:
        """Draws professional bounding boxes and HUD reticles on the banknote image."""
        template = DENOMINATION_TEMPLATES.get(template_key, DENOMINATION_TEMPLATES["USD_100"])
        annotated = img.copy()
        h, w = annotated.shape[:2]

        color_map = {
            "GENUINE": (0, 200, 80),     # Emerald Green
            "SUSPECT": (0, 180, 255),    # Amber
            "COUNTERFEIT": (40, 40, 230) # Crimson
        }
        main_color = color_map.get(verdict, (0, 200, 80))

        # Draw ROI boxes
        boxes = [
            (template["microprint_roi"], "MICROPRINT (0.1mm)", (255, 180, 0)),
            (template["security_thread_roi"], "SECURITY THREAD", (0, 220, 255)),
            (template["serial_roi"], "SERIAL OCR BLOCK", (220, 0, 220)),
            (template["portrait_roi"], "WATERMARK / PORTRAIT", (0, 255, 120))
        ]

        for box_ratio, label, color in boxes:
            y1 = int(box_ratio[0] * h)
            x1 = int(box_ratio[1] * w)
            y2 = int(box_ratio[2] * h)
            x2 = int(box_ratio[3] * w)

            # Draw dashed/corner rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated, label, (x1, max(y1 - 8, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        # Outer reticle frame
        cv2.rectangle(annotated, (5, 5), (w - 5, h - 5), main_color, 3)
        cv2.putText(annotated, f"VERDICT: {verdict}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, main_color, 2, cv2.LINE_AA)

        return annotated
