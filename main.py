from fastapi import FastAPI

app = FastAPI(title="Poll Service")

@app.get("/health")
def health():
    return {"status": "ok"}
