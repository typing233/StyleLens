from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import css_analyzer, llm_config

app = FastAPI(
    title="StyleLens - CSS Analysis and Visualization Tool",
    description="A tool for analyzing CSS styles from web pages, visualizing relationships, and generating optimization reports",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(css_analyzer.router, prefix="/api/v1", tags=["CSS Analyzer"])
app.include_router(llm_config.router, prefix="/api/v1", tags=["LLM Configuration"])

@app.get("/")
def root():
    return {"message": "StyleLens API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
