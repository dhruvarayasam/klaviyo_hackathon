from fastapi import FastAPI

app = FastAPI(title="FlowDoctor")

@app.get("/")
def root():
    return {"status": "FlowDoctor backend running"}



