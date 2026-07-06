import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from mcp_server.server import AgriDataMCPServer
from agents_config import AgriGuardOrchestrator

# Initialize core services
mcp_server = AgriDataMCPServer()
orchestrator = AgriGuardOrchestrator(mcp_server)

app = FastAPI(title="AgriGuard - Intelligent & Secure Agronomical Assistant")

# Request Model
class AnalysisRequest(BaseModel):
    user_query: str = Field(..., description="Raw text describing location, name, or comments")
    crop_name: str = Field(..., description="Staple crop name")
    current_n: float = Field(..., ge=0, description="Nitrogen reading in soil")
    current_p: float = Field(..., ge=0, description="Phosphorus reading in soil")
    current_k: float = Field(..., ge=0, description="Potassium reading in soil")
    current_ph: float = Field(..., ge=0, le=14, description="pH of the soil")
    region_id: Optional[str] = Field(None, description="Optional regional override")

# API endpoint for running the secure multi-agent workflow
@app.post("/api/analyze")
async def analyze_crop_soil(request: AnalysisRequest):
    try:
        # Run orchestrator
        res = orchestrator.run_workflow(
            raw_input=request.user_query,
            crop_name=request.crop_name,
            current_n=request.current_n,
            current_p=request.current_p,
            current_k=request.current_k,
            current_ph=request.current_ph,
            region_id=request.region_id
        )
        if not res.get("success", False):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to run analysis."))
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Serve Static Assets on Vercel or Local
app_dir = os.path.dirname(__file__)

# Helper to serve static index.html at root
@app.get("/")
async def get_index():
    index_path = os.path.join(app_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend file index.html not found.")

# Mount other static files (css, js, images)
# We mount this at root to serve style.css, script.js, etc.
app.mount("/", StaticFiles(directory=app_dir, html=False), name="static")

if __name__ == "__main__":
    import uvicorn
    # Start web server
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
