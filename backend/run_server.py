import uvicorn
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("==================================================")
    print("  MedLens Clinical Intelligence Platform Backend  ")
    print("  Running on http://127.0.0.1:8000                ")
    print("  Interactive Docs at http://127.0.0.1:8000/docs  ")
    print("==================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
