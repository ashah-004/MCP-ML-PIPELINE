from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

# Force use of the same tokenizer as training
tokenizer = RobertaTokenizer.from_pretrained("roberta-base")

# Load model from saved directory
model = RobertaForSequenceClassification.from_pretrained("app/model")
model.eval()

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def predict(text: str, temperature: float = 2.0, threshold: float = 0.6) -> dict:
    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Predict logits
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    # Apply temperature scaling
    scaled_logits = logits / temperature
    probs = torch.softmax(scaled_logits, dim=-1).cpu().numpy()[0]

    # Prediction using threshold
    pred = int(probs[1] > threshold)

    return {
        "prediction": pred,  # 0 = Human, 1 = AI
        "confidence": float(probs[pred]),
        "probabilities": {"human": float(probs[0]), "ai": float(probs[1])}
    }
