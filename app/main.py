from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.utils import predict
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="AI Text Detection API")

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, include_in_schema=True)

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    prediction: int  # 0 = Human, 1 = AI
    confidence: float
    probabilities: dict

@app.get("/")
def read_root():
    return {"message": "AI Text Detector is live!"}

@app.post("/predict", response_model=PredictResponse)
def predict_text(request: PredictRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    return predict(request.text)
