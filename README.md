# Counterfeit Currency Identification Agent

### Digital Public Safety & Real-Time Currency Verification Engine

An advanced, end-to-end computer vision and intelligent heuristic system designed for real-time banknote inspection, verification, and forensic audit logging. Built with **FastAPI** on the backend and a premium, responsive **Cyber HUD Dashboard** on the frontend, this application provides field operators and banking terminals with instant counterfeit detection and geographic hotspot tracking.

---

## 🚀 Key Features

*   **Computer Vision Skew Rectification**: Detects outer banknote borders and applies perspective correction to align skewed or poorly-rotated scans into a standardized template format.
*   **Security Feature Inspection (ROI Extraction)**: Extracts specific Regions of Interest (ROIs) according to currency-specific templates (USD, INR, etc.):
    *   **Microprint Sharpness Analysis**: Evaluates high-frequency edges and print texture using Laplacian variance and Sobel edge magnitude density to differentiate between genuine sharp printing and blurry inkjet counterfeits.
    *   **Security Thread Continuity Verification**: Evaluates vertical line continuity and contrast profiles to verify the presence of embedded security threads.
    *   **UV Fluorescence Verification**: Evaluates the color spectrum and intensity of fluorescent bands under UV simulations.
*   **Blacklist Serial OCR & Database Verification**: Cross-references detected serial numbers against a law enforcement database populated with flagged/blacklisted serial numbers.
*   **Weighted Heuristic Scoring Engine**: Combines individual analysis scores (Microprint, Thread, UV, and Serial Structure) into an aggregated confidence score.
*   **Interactive Cyber HUD Dashboard**:
    *   **Live Scanner HUD**: Perform inspections on preset test banknotes or upload custom scans.
    *   **Microprint & UV Analysis Viewport**: Explores extracted features using an interactive optical zoom lens.
    *   **Seizure GeoMap**: Visualizes geographical clusters and regional risk distributions of counterfeit currency.
    *   **Audit & Blacklist Registries**: View audit trails of past scans and add new flagged serial numbers to the blacklist.

---

## 🛠️ Technology Stack

*   **Backend Framework**: FastAPI (Python 3)
*   **Computer Vision & Image Processing**: OpenCV (Headless), NumPy, Pillow
*   **Database & ORM**: SQLAlchemy with SQLite (pre-seeded with default data for easy local execution)
*   **Frontend**: Single Page Application (SPA) using HTML, premium Vanilla CSS (ambient glows, glassmorphism, responsive grids, scan line animations), and Vanilla JavaScript
*   **Testing**: Pytest & FastAPI TestClient

---

## 📁 Project Directory Structure

```text
ET_AI_HACKTHON/
├── backend/
│   ├── config.py              # Configuration thresholds, denomination template ROIs & database URLs
│   ├── cv_pipeline.py         # Skew correction, ROI extraction, and feature analysis algorithms
│   ├── database.py            # SQLite session management and database seeding
│   ├── main.py                # FastAPI app definitions, routing, static mounting, and middleware
│   ├── model_engine.py        # Verdict heuristic engine and serial blacklist validation logic
│   ├── models.py              # SQLAlchemy database model definitions (ScanLogs, FlaggedSerials, etc.)
│   ├── requirements.txt       # Python project dependencies
│   └── sample_generator.py    # Synthetic image generator for authentic, fake, and suspect banknotes
├── frontend/
│   ├── index.html             # Dashboard layout (Live HUD, Microprint Zoom, GeoMap, Registry)
│   ├── styles.css             # Cyberpunk-inspired glassmorphism & responsive layouts
│   └── app.js                 # API communications, state management, and HUD event handlers
├── tests/
│   ├── test_api.py            # API endpoint test cases (stats, scan, logs, seizures)
│   └── test_vision.py         # Core CV pipeline and model validation tests
├── run_server.py              # Unified entry point script to boot database and API server
└── .gitignore                 # Standard file exclusion rules
```

---

## ⚙️ Setup and Installation

### 1. Prerequisites
Make sure you have **Python 3.9+** installed on your system.

### 2. Create a Virtual Environment
Create and activate a virtual environment to isolate project dependencies:

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries specified in the backend configuration:
```bash
pip install -r backend/requirements.txt
```

---

## 🏃 Running the Application

To boot up the database, seed test data, generate synthetic banknote samples, and start the local FastAPI web server, run the unified entry script:

```bash
python run_server.py
```

Once the server initializes, you can access the application in your browser:
*   **Dashboard Frontend**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
*   **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📊 Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the main frontend dashboard SPA |
| `POST` | `/api/v1/scan` | Submits image bytes/presets for full computer vision and blacklist inspection |
| `GET` | `/api/v1/stats` | Retrieves high-level analytics summary data (detection rates, total scans) |
| `GET` | `/api/v1/logs` | Fetches recent scan logs for the historical audit registry |
| `GET` | `/api/v1/seizures` | Returns geographic coordinate hotspots for regional map displays |
| `GET` | `/api/v1/serials` | Lists all currently blacklisted serial numbers registered in the system |
| `POST` | `/api/v1/serials` | Registers a new flagged serial number into the law enforcement blacklist |

---

## 🧪 Testing

The codebase includes automated tests to verify API endpoints, computer vision math, and model logic. Run the tests using `pytest` from the root directory:

```bash
pytest
```
