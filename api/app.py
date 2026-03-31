from fastapi import FastAPI

from preprocessing.pipeline import preprocess_all

app = FastAPI(title="Saathi API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/admin/preprocess")
def admin_preprocess():
    """Trigger preprocessing for all 7 aspiration videos."""
    results = preprocess_all()
    return {"status": "ok", "videos_processed": len(results), "results": results}
