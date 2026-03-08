from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import os

app = Flask(__name__)

# Complete CORS configuration
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
     methods=["GET", "POST", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

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

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    headline = data.get("headline", "")
    article = data.get("article", "")
    
    if not headline:
        return jsonify({"error": "Headline is required"})
    
    # Combine headline and article
    text = f"{headline} {article}".strip()
    cleaned = clean_text(text)
    
    vector = vectorizer.transform([cleaned])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]
    
    confidence = max(probability)
    
    result = "Real News" if prediction == 1 else "Fake News"
    
    return jsonify({
        "prediction": result,
        "confidence": float(confidence),
        "fake_probability": float(probability[0]),
        "real_probability": float(probability[1])
    })

@app.route("/verify-source", methods=["POST"])
def verify_source():
    data = request.json
    url = data.get("url", "")
    
    if not url:
        return jsonify({"error": "URL is required"})
    
    # Simple source verification (placeholder)
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Basic domain check
        trusted_domains = ["reuters.com", "bbc.com", "cnn.com", "nytimes.com"]
        is_trusted = any(trusted in domain for trusted_domain in trusted_domains)
        
        return jsonify({
            "url": url,
            "domain": domain,
            "is_trusted": is_trusted,
            "trust_score": 85 if is_trusted else 45,
            "verification": "Domain check completed"
        })
    except Exception as e:
        return jsonify({
            "url": url,
            "error": str(e),
            "verification": "Verification failed"
        })

@app.route("/analyze-with-source", methods=["POST"])
def analyze_with_source():
    data = request.json
    headline = data.get("headline", "")
    article = data.get("article", "")
    url = data.get("url", "")
    
    if not headline:
        return jsonify({"error": "Headline is required"})
    
    # Combine text analysis
    text = f"{headline} {article}".strip()
    cleaned = clean_text(text)
    
    vector = vectorizer.transform([cleaned])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]
    
    confidence = max(probability)
    result = "Real News" if prediction == 1 else "Fake News"
    
    # Source verification
    source_info = {"verification": "No URL provided"}
    if url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            trusted_domains = ["reuters.com", "bbc.com", "cnn.com", "nytimes.com"]
            is_trusted = any(trusted in domain for trusted_domain in trusted_domains)
            
            source_info = {
                "url": url,
                "domain": domain,
                "is_trusted": is_trusted,
                "trust_score": 85 if is_trusted else 45,
                "verification": "Domain check completed"
            }
        except Exception as e:
            source_info = {
                "url": url,
                "error": str(e),
                "verification": "Verification failed"
            }
    else:
        source_info = {"verification": "No URL provided"}
    
    return jsonify({
        "text_analysis": {
            "prediction": result,
            "confidence": float(confidence),
            "fake_probability": float(probability[0]),
            "real_probability": float(probability[1])
        },
        "source_verification": source_info
    })

if __name__ == "__main__":
    app.run(debug=True)