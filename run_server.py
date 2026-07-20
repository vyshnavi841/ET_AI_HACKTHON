import uvicorn
import os
import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.sample_generator import generate_sample_banknotes
from backend.database import init_db

if __name__ == "__main__":
    print("===============================================================")
    print(" COUNTERFEIT CURRENCY IDENTIFICATION AGENT SERVER")
    print(" Digital Public Safety & Real-time Verification Engine")
    print("===============================================================")
    
    init_db()
    generate_sample_banknotes()

    port = int(os.getenv("PORT", 8000))
    print(f"Starting server at: http://127.0.0.1:{port}")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=True)
