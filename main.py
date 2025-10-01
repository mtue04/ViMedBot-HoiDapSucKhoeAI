from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
import os
import mimetypes

app = FastAPI(
    title="ViMedBot API",
    description="Hỏi đáp sức khỏe AI cho người Việt",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["chat"])

BASE_DIR = os.path.dirname(__file__)
static_dir = os.path.join(BASE_DIR, "src", "static")
templates_dir = os.path.join(BASE_DIR, "src", "templates")
assets_dir = os.path.join(BASE_DIR, "assets")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
async def root():
    index_path = os.path.join(templates_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ViMedBot API is running. Visit /docs for API documentation."}

@app.get("/favicon.ico")
async def favicon():
    ico_path = os.path.join(assets_dir, "favicon.ico")
    alt_path = os.path.join(assets_dir, "ViMedBot_logo.jpg")
    path = ico_path if os.path.exists(ico_path) else alt_path
    media_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=media_type or "image/x-icon")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ViMedBot"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
