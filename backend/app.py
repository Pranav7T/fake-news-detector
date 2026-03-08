from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import os

app = Flask(__name__)
CORS(app)

# Load trained model
BASE_DIR = os.path.dirname(__file__)

try:
    # Try to load ensemble model first
    model = pickle.load(open(os.path.join(BASE_DIR, "ensemble_model.pkl"), "rb"))
    print("Using ensemble model")
except:
    # Fall back to single model
    model = pickle.load(open(os.path.join(BASE_DIR, "model.pkl"), "rb"))
    print("Using single model")

vectorizer = pickle.load(open(os.path.join(BASE_DIR, "vectorizer.pkl"), "rb"))

def clean_text(text):
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Remove special characters but keep letters
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove single characters
    text = re.sub(r'\b[a-zA-Z]\b', '', text)
    return text.strip()

@app.route("/")
def home():
    return "Fake News Detection API is running"

@app.route("/predict", methods=["POST"])
def predict():
    
    data = request.json
    news_text = data["text"]

    cleaned = clean_text(news_text)

    vector = vectorizer.transform([cleaned])

    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]

    confidence = max(probability)
    
    # Add confidence interpretation
    if confidence >= 0.90:
        confidence_level = "Very High"
    elif confidence >= 0.75:
        confidence_level = "High"
    elif confidence >= 0.60:
        confidence_level = "Medium"
    elif confidence >= 0.50:
        confidence_level = "Low"
    else:
        confidence_level = "Very Low"

    result = "Real News" if prediction == 1 else "Fake News"

    return jsonify({
        "prediction": result,
        "confidence": float(confidence),
        "confidence_level": confidence_level,
        "fake_probability": float(probability[0]),
        "real_probability": float(probability[1])
    })

if __name__ == "__main__":
    app.run(debug=True)