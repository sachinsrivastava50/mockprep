import sys
import os

# Add project root to path so "backend.app.main" resolves correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  MockPrep - AI Mock Interview Platform")
    print("  Web App  :  http://localhost:8000")
    print("  API Docs :  http://localhost:8000/docs")
    print("  Health   :  http://localhost:8000/api/health")
    print("=" * 60 + "\n")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"]
    )
