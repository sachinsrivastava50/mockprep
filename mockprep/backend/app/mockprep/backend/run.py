import uvicorn
import os

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" 🚀 Launching MockPrep (FastAPI Backend + Modern Frontend)")
    print(" 🌐 Application URL: http://localhost:8000")
    print(" 📖 Interactive API Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
