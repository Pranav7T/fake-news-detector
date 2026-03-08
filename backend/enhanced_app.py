from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import os
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Load trained model
BASE_DIR = os.path.dirname(__name__)

try:
    # Try to load ensemble model first
    model = pickle.load(open(os.path.join(BASE_DIR, "model.pkl"), "rb"))
    print("Using ensemble model")
except:
    # Fall back to single model
    model = pickle.load(open(os.path.join(BASE_DIR, "model.pkl"), "rb"))
    print("Using single model")

vectorizer = pickle.load(open(os.path.join(BASE_DIR, "vectorizer.pkl"), "rb"))

# Source verification data
TRUSTED_DOMAINS = {
    'reuters.com': {'trust_score': 95, 'category': 'International News', 'description': 'Global news agency with strict editorial standards'},
    'ap.org': {'trust_score': 95, 'category': 'International News', 'description': 'Associated Press - Leading news agency'},
    'bbc.com': {'trust_score': 90, 'category': 'International News', 'description': 'British Broadcasting Corporation - Public service broadcaster'},
    'cnn.com': {'trust_score': 85, 'category': 'International News', 'description': 'Cable News Network - Major US news network'},
    'nytimes.com': {'trust_score': 90, 'category': 'International News', 'description': 'The New York Times - Pulitzer-winning newspaper'},
    'washingtonpost.com': {'trust_score': 88, 'category': 'International News', 'description': 'The Washington Post - Major US newspaper'},
    'wsj.com': {'trust_score': 90, 'category': 'International News', 'description': 'The Wall Street Journal - Business-focused news'},
    'thehindu.com': {'trust_score': 85, 'category': 'Indian News', 'description': 'The Hindu - Leading Indian newspaper'},
    'timesofindia.indiatimes.com': {'trust_score': 75, 'category': 'Indian News', 'description': 'Times of India - Major Indian newspaper'},
    'indianexpress.com': {'trust_score': 80, 'category': 'Indian News', 'description': 'The Indian Express - Leading Indian newspaper'},
    'hindustantimes.com': {'trust_score': 75, 'category': 'Indian News', 'description': 'Hindustan Times - Major Indian newspaper'},
    'ndtv.com': {'trust_score': 80, 'category': 'Indian News', 'description': 'NDTV - Leading Indian news channel'},
    'economictimes.indiatimes.com': {'trust_score': 85, 'category': 'Indian News', 'description': 'Economic Times - Business news in India'},
    'nature.com': {'trust_score': 95, 'category': 'Science', 'description': 'Nature - Leading scientific journal'},
    'science.org': {'trust_score': 95, 'category': 'Science', 'description': 'Science - Leading scientific journal'},
    'techcrunch.com': {'trust_score': 85, 'category': 'Technology', 'description': 'TechCrunch - Technology news and analysis'},
    'wired.com': {'trust_score': 85, 'category': 'Technology', 'description': 'Wired - Technology and culture magazine'},
    'arstechnica.com': {'trust_score': 90, 'category': 'Technology', 'description': 'Ars Technica - Technology news site'},
    'bloomberg.com': {'trust_score': 90, 'category': 'Business', 'description': 'Bloomberg - Financial news and data'},
    'forbes.com': {'trust_score': 85, 'category': 'Business', 'description': 'Forbes - Business and financial news'},
    'fortune.com': {'trust_score': 85, 'category': 'Business', 'description': 'Fortune - Business magazine'},
    'businessinsider.com': {'trust_score': 80, 'category': 'Business', 'description': 'Business Insider - Business news site'},
    'gov.in': {'trust_score': 95, 'category': 'Government', 'description': 'Indian Government websites'},
    'gov': {'trust_score': 95, 'category': 'Government', 'description': 'US Government websites'},
    'edu': {'trust_score': 90, 'category': 'Education', 'description': 'Educational institutions'},
    'ac.in': {'trust_score': 90, 'category': 'Education', 'description': 'Indian educational institutions'},
    'who.int': {'trust_score': 95, 'category': 'Health', 'description': 'World Health Organization'},
    'cdc.gov': {'trust_score': 95, 'category': 'Health', 'description': 'Centers for Disease Control and Prevention'},
    'nih.gov': {'trust_score': 95, 'category': 'Health', 'description': 'National Institutes of Health'},
    'mayoclinic.org': {'trust_score': 90, 'category': 'Health', 'description': 'Mayo Clinic - Medical research and care'},
}

SUSPICIOUS_DOMAINS = {
    'theonion.com': {'trust_score': 20, 'category': 'Satire', 'description': 'The Onion - Satirical news site'},
    'clickhole.com': {'trust_score': 20, 'category': 'Satire', 'description': 'ClickHole - Satirical content'},
    'dailycurrant.com': {'trust_score': 15, 'category': 'Fake News', 'description': 'Daily Currant - Fake news site'},
    'empirenews.net': {'trust_score': 15, 'category': 'Fake News', 'description': 'Empire News - Fake news site'},
    'nationalreport.net': {'trust_score': 15, 'category': 'Fake News', 'description': 'National Report - Fake news site'},
    'worldnewsdailyreport.com': {'trust_score': 15, 'category': 'Fake News', 'description': 'World News Daily Report - Fake news site'},
    'news-': {'trust_score': 30, 'category': 'Suspicious Pattern', 'description': 'Domain with hyphen in news'},
    '-news': {'trust_score': 30, 'category': 'Suspicious Pattern', 'description': 'Domain with hyphen in news'},
    'news24': {'trust_score': 40, 'category': 'Suspicious Pattern', 'description': 'Generic news24 pattern'},
    'breakingnews': {'trust_score': 35, 'category': 'Suspicious Pattern', 'description': 'Generic breaking news pattern'},
    'daily': {'trust_score': 45, 'category': 'Suspicious Pattern', 'description': 'Generic daily news pattern'},
    'blog': {'trust_score': 50, 'category': 'Blog', 'description': 'Blog platform - may contain opinion content'},
    'wordpress.com': {'trust_score': 50, 'category': 'Blog', 'description': 'WordPress blog platform'},
    'blogspot.com': {'trust_score': 50, 'category': 'Blog', 'description': 'Blogspot blog platform'},
    'medium.com': {'trust_score': 60, 'category': 'Blog', 'description': 'Medium - Mixed quality content platform'},
}

def extract_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except:
        return None

def check_domain_trustworthiness(domain):
    """Check if domain is trustworthy"""
    if not domain:
        return {
            'trust_score': 0,
            'category': 'Invalid',
            'description': 'Invalid URL or domain',
            'is_trusted': False,
            'is_suspicious': True
        }
    
    # Check exact matches first
    if domain in TRUSTED_DOMAINS:
        info = TRUSTED_DOMAINS[domain].copy()
        info['is_trusted'] = True
        info['is_suspicious'] = False
        return info
    
    if domain in SUSPICIOUS_DOMAINS:
        info = SUSPICIOUS_DOMAINS[domain].copy()
        info['is_trusted'] = False
        info['is_suspicious'] = True
        return info
    
    # Check partial matches and patterns
    for trusted_domain, info in TRUSTED_DOMAINS.items():
        if domain.endswith(trusted_domain) or trusted_domain in domain:
            result = info.copy()
            result['trust_score'] -= 5  # Slightly lower for subdomains
            result['is_trusted'] = True
            result['is_suspicious'] = False
            result['description'] = f"Subdomain of {trusted_domain}: {info['description']}"
            return result
    
    for suspicious_pattern, info in SUSPICIOUS_DOMAINS.items():
        if suspicious_pattern in domain:
            result = info.copy()
            result['is_trusted'] = False
            result['is_suspicious'] = True
            return result
    
    # Check TLD-based trust
    if domain.endswith('.gov') or domain.endswith('.gov.in') or domain.endswith('.edu') or domain.endswith('.ac.in'):
        return {
            'trust_score': 85,
            'category': 'Official',
            'description': 'Official government or educational domain',
            'is_trusted': True,
            'is_suspicious': False
        }
    
    # Default unknown domain
    return {
        'trust_score': 50,
        'category': 'Unknown',
        'description': 'Unknown domain - verify manually',
        'is_trusted': False,
        'is_suspicious': False
    }

def analyze_url_content(url):
    """Analyze URL content for additional verification"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title and description
        title = soup.find('title')
        title_text = title.text.strip() if title else "No title found"
        
        description = soup.find('meta', attrs={'name': 'description'})
        desc_text = description['content'].strip() if description else "No description found"
        
        # Check for author information
        author = soup.find('meta', attrs={'name': 'author'})
        author_text = author['content'].strip() if author else None
        
        # Check for publish date
        publish_date = soup.find('meta', property='article:published_time')
        date_text = publish_date['content'] if publish_date else None
        
        return {
            'title': title_text,
            'description': desc_text,
            'author': author_text,
            'publish_date': date_text,
            'content_length': len(response.text),
            'status_code': response.status_code
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'title': None,
            'description': None,
            'author': None,
            'publish_date': None,
            'content_length': 0,
            'status_code': None
        }

def comprehensive_source_verification(url):
    """Comprehensive news source verification"""
    
    # Extract domain
    domain = extract_domain(url)
    
    # Check domain trustworthiness
    domain_info = check_domain_trustworthiness(domain)
    
    # Analyze URL content
    content_info = analyze_url_content(url)
    
    # Calculate overall trust score
    base_score = domain_info['trust_score']
    
    # Adjust based on content analysis
    if content_info.get('author'):
        base_score += 5  # Has author
    
    if content_info.get('publish_date'):
        base_score += 3  # Has publish date
    
    if content_info.get('content_length', 0) > 1000:
        base_score += 2  # Substantial content
    
    if content_info.get('status_code') == 200:
        base_score += 2  # Accessible
    
    # Cap the score
    final_score = min(100, max(0, base_score))
    
    # Determine risk level
    if final_score >= 80:
        risk_level = "Low Risk"
        recommendation = "Generally trustworthy source"
    elif final_score >= 60:
        risk_level = "Medium Risk"
        recommendation = "Verify with additional sources"
    elif final_score >= 40:
        risk_level = "High Risk"
        recommendation = "Exercise caution, verify claims"
    else:
        risk_level = "Very High Risk"
        recommendation = "Likely unreliable, avoid sharing"
    
    return {
        'url': url,
        'domain': domain,
        'domain_info': domain_info,
        'content_info': content_info,
        'overall_score': final_score,
        'risk_level': risk_level,
        'recommendation': recommendation,
        'verification_timestamp': pd.Timestamp.now().isoformat()
    }

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

def get_feature_importance(text, model, vectorizer, top_n=10):
    """Get most important features/words that influenced the prediction"""
    
    cleaned = clean_text(text)
    vector = vectorizer.transform([cleaned])
    
    # Get feature names and their values in the text
    feature_names = vectorizer.get_feature_names_out()
    feature_values = vector.toarray()[0]
    
    # Get feature importance from model
    if hasattr(model, 'feature_importances_'):
        feature_importances = model.feature_importances_
    elif hasattr(model, 'estimators_'):  # Ensemble model
        importances = []
        for estimator in model.estimators_:
            if hasattr(estimator, 'feature_importances_'):
                importances.append(estimator.feature_importances_)
        if importances:
            feature_importances = np.mean(importances, axis=0)
        else:
            feature_importances = np.zeros(len(feature_names))
    else:
        feature_importances = np.zeros(len(feature_names))
    
    # Create list of (feature, value, importance) for features present in text
    text_features = []
    for i, value in enumerate(feature_values):
        if value > 0:  # Feature is present in text
            text_features.append((
                feature_names[i],
                value,
                feature_importances[i]
            ))
    
    # Sort by importance
    text_features.sort(key=lambda x: x[2], reverse=True)
    
    return text_features[:top_n]

def get_suspicious_words(text, model, vectorizer, top_n=5):
    """Identify suspicious words that typically indicate fake news"""
    
    fake_news_indicators = [
        "breaking", "shocking", "secret", "leaked", "conspiracy",
        "urgent", "scandal", "exposed", "revealed", "hidden",
        "amazing", "incredible", "unbelievable", "miracle",
        "celebrity", "gossip", "rumor", "speculation", "hoax",
        "bizarre", "strange", "mystery", "alien", "ghost"
    ]
    
    cleaned = clean_text(text)
    vector = vectorizer.transform([cleaned])
    
    feature_names = vectorizer.get_feature_names_out()
    feature_values = vector.toarray()[0]
    
    suspicious_found = []
    for i, value in enumerate(feature_values):
        if value > 0:
            word = feature_names[i]
            if any(indicator in word for indicator in fake_news_indicators):
                suspicious_found.append((word, value))
    
    suspicious_found.sort(key=lambda x: x[1], reverse=True)
    return suspicious_found[:top_n]

def get_credibility_indicators(text, model, vectorizer):
    """Analyze credibility indicators in the text"""
    
    cleaned = clean_text(text)
    
    credibility_score = 100
    reasons = []
    
    # Check for sensational language
    sensational_words = ["breaking", "shocking", "urgent", "incredible", "amazing", "miracle"]
    sensational_count = sum(1 for word in sensational_words if word in cleaned)
    if sensational_count > 0:
        credibility_score -= sensational_count * 10
        reasons.append(f"Contains {sensational_count} sensational words")
    
    # Check for clickbait patterns
    clickbait_patterns = ["!", "???", "you won't believe", "shocking", "incredible"]
    clickbait_count = sum(1 for pattern in clickbait_patterns if pattern in cleaned)
    if clickbait_count > 0:
        credibility_score -= clickbait_count * 15
        reasons.append(f"Contains {clickbait_count} clickbait patterns")
    
    # Check for source credibility indicators
    credible_sources = ["reuters", "associated press", "bbc", "cnn", "nbc", "cbs", "abc"]
    source_found = any(source in cleaned for source in credible_sources)
    if source_found:
        credibility_score += 10
        reasons.append("Contains credible news source")
    
    # Check for scientific/technical language
    technical_words = ["research", "study", "scientists", "university", "journal", "published"]
    technical_count = sum(1 for word in technical_words if word in cleaned)
    if technical_count >= 2:
        credibility_score += 5
        reasons.append("Contains scientific/technical language")
    
    # Ensure score stays within bounds
    credibility_score = max(0, min(100, credibility_score))
    
    return {
        "score": credibility_score,
        "reasons": reasons
    }

def comprehensive_analysis(text, model, vectorizer):
    """Complete explainable AI analysis"""
    
    cleaned = clean_text(text)
    vector = vectorizer.transform([cleaned])
    
    # Get prediction and probabilities
    prediction = model.predict(vector)[0]
    probabilities = model.predict_proba(vector)[0]
    
    result = "Real News" if prediction == 1 else "Fake News"
    confidence = max(probabilities)
    
    # Get explanations
    important_features = get_feature_importance(text, model, vectorizer)
    suspicious_words = get_suspicious_words(text, model, vectorizer)
    credibility = get_credibility_indicators(text, model, vectorizer)
    
    # Generate explanation
    explanation_parts = []
    
    if confidence >= 0.80:
        explanation_parts.append(f"AI is very confident this is {result.lower()}.")
    elif confidence >= 0.70:
        explanation_parts.append(f"AI is fairly confident this is {result.lower()}.")
    elif confidence >= 0.60:
        explanation_parts.append(f"AI thinks this is likely {result.lower()} but is not certain.")
    else:
        explanation_parts.append(f"AI is uncertain about whether this is {result.lower()}.")
    
    if suspicious_words and result == "Fake News":
        suspicious_list = [s[0] for s in suspicious_words[:3]]
        explanation_parts.append(f"AI detected suspicious words: {', '.join(suspicious_list)}.")
        explanation_parts.append("Fake news articles often contain emotional or sensational language.")
    
    if credibility['score'] < 50:
        explanation_parts.append(f"Low credibility score ({credibility['score']}/100) indicates potential issues.")
    elif credibility['score'] > 70:
        explanation_parts.append(f"High credibility score ({credibility['score']}/100) suggests reliability.")
    
    if important_features:
        top_features = [f[0] for f in important_features[:3]]
        explanation_parts.append(f"Key words that influenced this decision: {', '.join(top_features)}.")
    
    explanation = " ".join(explanation_parts)
    
    return {
        'prediction': result,
        'confidence': float(confidence),
        'fake_probability': float(probabilities[0]),
        'real_probability': float(probabilities[1]),
        'important_features': [{"word": f[0], "importance": float(f[2])} for f in important_features],
        'suspicious_words': [{"word": s[0], "value": float(s[1])} for s in suspicious_words],
        'credibility_score': credibility['score'],
        'credibility_reasons': credibility['reasons'],
        'explanation': explanation
    }

@app.route("/")
def home():
    return "Enhanced Fake News Detection API with Explainable AI"

@app.route("/predict", methods=["POST"])
def predict():
    """Original single text prediction endpoint"""
    
    data = request.json
    news_text = data["text"]

    analysis = comprehensive_analysis(news_text, model, vectorizer)

    # Add confidence interpretation
    if analysis['confidence'] >= 0.90:
        confidence_level = "Very High"
    elif analysis['confidence'] >= 0.75:
        confidence_level = "High"
    elif analysis['confidence'] >= 0.60:
        confidence_level = "Medium"
    elif analysis['confidence'] >= 0.50:
        confidence_level = "Low"
    else:
        confidence_level = "Very Low"

    return jsonify({
        "prediction": analysis['prediction'],
        "confidence": analysis['confidence'],
        "confidence_level": confidence_level,
        "fake_probability": analysis['fake_probability'],
        "real_probability": analysis['real_probability'],
        "credibility_score": analysis['credibility_score'],
        "important_features": analysis['important_features'],
        "suspicious_words": analysis['suspicious_words'],
        "explanation": analysis['explanation']
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    """Enhanced headline + article analysis endpoint"""
    
    data = request.json
    headline = data.get("headline", "")
    article = data.get("article", "")
    
    # Combine headline and article for analysis
    combined_text = f"{headline} {article}".strip()
    
    if not combined_text:
        return jsonify({"error": "No text provided"}), 400
    
    # Analyze combined text
    combined_analysis = comprehensive_analysis(combined_text, model, vectorizer)
    
    # Analyze headline separately if provided
    headline_analysis = None
    if headline:
        headline_analysis = comprehensive_analysis(headline, model, vectorizer)
    
    # Analyze article separately if provided
    article_analysis = None
    if article:
        article_analysis = comprehensive_analysis(article, model, vectorizer)
    
    # Confidence interpretation
    if combined_analysis['confidence'] >= 0.90:
        confidence_level = "Very High"
        risk_level = "Low Risk"
    elif combined_analysis['confidence'] >= 0.75:
        confidence_level = "High"
        risk_level = "Medium Risk"
    elif combined_analysis['confidence'] >= 0.60:
        confidence_level = "Medium"
        risk_level = "High Risk"
    else:
        confidence_level = "Low"
        risk_level = "Very High Risk"
    
    response = {
        "prediction": combined_analysis['prediction'],
        "confidence": combined_analysis['confidence'],
        "confidence_level": confidence_level,
        "risk_level": risk_level,
        "fake_probability": combined_analysis['fake_probability'],
        "real_probability": combined_analysis['real_probability'],
        "credibility_score": combined_analysis['credibility_score'],
        "important_features": combined_analysis['important_features'],
        "suspicious_words": combined_analysis['suspicious_words'],
        "explanation": combined_analysis['explanation'],
        "headline_analysis": headline_analysis,
        "article_analysis": article_analysis,
        "text_lengths": {
            "headline_length": len(headline),
            "article_length": len(article),
            "combined_length": len(combined_text)
        }
    }
    
    return jsonify(response)

@app.route("/explain", methods=["POST"])
def explain():
    """Detailed explainable AI endpoint"""
    
    data = request.json
    text = data["text"]
    
    analysis = comprehensive_analysis(text, model, vectorizer)
    
    return jsonify({
        "text": text,
        "prediction": analysis['prediction'],
        "confidence": analysis['confidence'],
        "credibility_score": analysis['credibility_score'],
        "credibility_reasons": analysis['credibility_reasons'],
        "important_features": analysis['important_features'],
        "suspicious_words": analysis['suspicious_words'],
        "explanation": analysis['explanation'],
        "fake_probability": analysis['fake_probability'],
        "real_probability": analysis['real_probability']
    })

@app.route("/verify-source", methods=["POST"])
def verify_source():
    """News source verification endpoint"""
    
    data = request.json
    url = data.get("url", "")
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Perform comprehensive source verification
    verification_result = comprehensive_source_verification(url)
    
    return jsonify(verification_result)

@app.route("/analyze-with-source", methods=["POST"])
def analyze_with_source():
    """Combined text analysis + source verification"""
    
    data = request.json
    headline = data.get("headline", "")
    article = data.get("article", "")
    url = data.get("url", "")
    
    # Analyze text
    text = f"{headline} {article}".strip()
    text_analysis = None
    
    if text:
        text_analysis = comprehensive_analysis(text, model, vectorizer)
    
    # Verify source if URL provided
    source_verification = None
    if url:
        source_verification = comprehensive_source_verification(url)
    
    # Combine results
    combined_result = {
        "text_analysis": text_analysis,
        "source_verification": source_verification,
        "has_text": bool(text),
        "has_url": bool(url),
        "analysis_timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Calculate overall trust score combining both analyses
    if text_analysis and source_verification:
        text_score = text_analysis['credibility_score']
        source_score = source_verification['overall_score']
        
        # Weighted average (70% text analysis, 30% source verification)
        overall_trust_score = (text_score * 0.7) + (source_score * 0.3)
        
        combined_result["overall_trust_score"] = round(overall_trust_score, 1)
        
        # Determine final recommendation
        if overall_trust_score >= 75:
            combined_result["final_recommendation"] = "Highly credible - Trust this source"
        elif overall_trust_score >= 60:
            combined_result["final_recommendation"] = "Moderately credible - Verify important claims"
        elif overall_trust_score >= 40:
            combined_result["final_recommendation"] = "Low credibility - Exercise extreme caution"
        else:
            combined_result["final_recommendation"] = "Not credible - Avoid sharing this content"
    
    return jsonify(combined_result)

if __name__ == "__main__":
    app.run(debug=True)
