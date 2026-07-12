from fastapi import FastAPI

app = FastAPI(title="VexaPro", version="0.1.0")

@app.get("/")
def root():
    return {"message": "VexaPro API online!", "status": "running"}
