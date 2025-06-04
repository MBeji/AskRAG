#!/usr/bin/env python3
"""
Serveur FastAPI minimal pour diagnostic
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Minimal FastAPI server working"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("Starting minimal FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="debug")
