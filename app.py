import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import numpy as np
import pandas as pd
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

# Configure CORS for production
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "https://*.onrender.com", "https://*.github.io"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Load models and vectorizer
try:
    model = pickle.load(open('backend/model.pkl', 'rb'))
    vectorizer = pickle.load(open('backend/vectorizer.pkl', 'rb'))
    print("✅ Models loaded successfully")
except Exception as e:
    print(f"❌ Error loading models: {e}")
    model = None
    vectorizer = None

# Trusted and suspicious domains
TRUSTED_DOMAINS = {
    'reuters.com': {'trust_score': 95, 'category': 'International News', 'description': 'Global news agency with strict editorial standards'},
    'bbc.com': {'trust_score': 92, 'category': 'International News', 'description': 'British public service broadcaster'},
    'cnn.com': {'trust_score': 88, 'category': 'International News', 'description': 'American news-based television channel'},
    'nytimes.com': {'trust_score': 90, 'category': 'International News', 'description': 'American newspaper with high journalistic standards'},
    'thehindu.com': {'trust_score': 85, 'category': 'Indian News', 'description': 'Indian newspaper with long history'},
    'ndtv.com': {'trust_score': 80, 'category': 'Indian News', 'description': 'Indian news television network'},
    'timesofindia.indiatimes.com': {'trust_score': 75, 'category': 'Indian News', 'description': 'Indian newspaper and media company'},
    'nature.com': {'trust_score': 95, 'category': 'Science', 'description': 'Scientific journal publisher'},
    'science.org': {'trust_score': 95, 'category': 'Science', 'description': 'Scientific journal publisher'},
    'techcrunch.com': {'trust_score': 82, 'category': 'Technology', 'description': 'Technology news website'},
    'wired.com': {'trust_score': 85, 'category': 'Technology', 'description': 'Technology and culture magazine'},
    'arstechnica.com': {'trust_score': 88, 'category': 'Technology', 'description': 'Technology news website'},
    'bloomberg.com': {'trust_score': 90, 'category': 'Business', 'description': 'Business and financial news'},
    'forbes.com': {'trust_score': 85, 'category': 'Business', 'description': 'Business magazine'},
    'wsj.com': {'trust_score': 92, 'category': 'Business', 'description': 'Wall Street Journal, business newspaper'},
    'who.int': {'trust_score': 95, 'category': 'Health', 'description': 'World Health Organization'},
    'cdc.gov': {'trust_score': 95, 'category': 'Health', 'description': 'Centers for Disease Control and Prevention'},
    'nih.gov': {'trust_score': 95, 'category': 'Health', 'description': 'National Institutes of Health'},
    'gov.in': {'trust_score': 95, 'category': 'Government', 'description': 'Indian government websites'},
    '.gov': {'trust_score': 95, 'category': 'Government', 'description': 'US government websites'},
    '.edu': {'trust_score': 90, 'category': 'Education', 'description': 'Educational institutions'},
    '.ac.in': {'trust_score': 90, 'category': 'Education', 'description': 'Indian educational institutions'}
}

SUSPICIOUS_DOMAINS = {
    'theonion.com': {'trust_score': 22, 'category': 'Satire', 'description': 'Satirical news organization'},
    'clickhole.com': {'trust_score': 25, 'category': 'Satire', 'description': 'Satirical website from The Onion'},
    'dailycurrant.com': {'trust_score': 15, 'category': 'Fake News', 'description': 'Known fake news site'},
    'empirenews.net': {'trust_score': 18, 'category': 'Fake News', 'description': 'Known fake news site'},
    'worldnewsdailyreport.com': {'trust_score': 20, 'category': 'Fake News', 'description': 'Known fake news site'},
    'nationalreport.net': {'trust_score': 12, 'category': 'Fake News', 'description': 'Known fake news site'}
}

def clean_text(text):
    """Clean and preprocess text for analysis"""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Convert to lowercase and remove extra whitespace
    text = text.lower().strip()
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text

def get_confidence_level(confidence):
    """Convert confidence to descriptive level"""
    if confidence >= 0.80:
        return "Very High"
    elif confidence >= 0.70:
        return "High"
    elif confidence >= 0.60:
        return "Medium"
    elif confidence >= 0.50:
        return "Low"
    else:
        return "Very Low"

def get_credibility_score(confidence, prediction):
    """Calculate credibility score based on confidence and prediction"""
    base_score = confidence * 100
    
    if prediction == "Real News":
        return min(95, base_score + 10)
    else:
        return max(5, base_score - 20)

def extract_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""

def check_domain_trust(domain):
    """Check if domain is trusted or suspicious"""
    domain_info = {
        'is_trusted': False,
        'is_suspicious': False,
        'trust_score': 50,
        'category': 'Unknown',
        'description': 'No information available'
    }
    
    # Check trusted domains
    for trusted_domain, info in TRUSTED_DOMAINS.items():
        if trusted_domain in domain or domain.endswith(trusted_domain):
            domain_info.update({
                'is_trusted': True,
                'trust_score': info['trust_score'],
                'category': info['category'],
                'description': info['description']
            })
            return domain_info
    
    # Check suspicious domains
    for suspicious_domain, info in SUSPICIOUS_DOMAINS.items():
        if suspicious_domain in domain or domain.endswith(suspicious_domain):
            domain_info.update({
                'is_suspicious': True,
                'trust_score': info['trust_score'],
                'category': info['category'],
                'description': info['description']
            })
            return domain_info
    
    # Check for suspicious patterns
    suspicious_patterns = ['news-', '-news', 'news24', 'breakingnews', 'daily', 'weekly']
    for pattern in suspicious_patterns:
        if pattern in domain:
            domain_info.update({
                'is_suspicious': True,
                'trust_score': 35,
                'category': 'Suspicious Pattern',
                'description': 'Domain contains suspicious patterns commonly used by fake news sites'
            })
            return domain_info
    
    return domain_info

def analyze_url_content(url):
    """Analyze content of the URL"""
    content_info = {
        'title': '',
        'author': '',
        'publish_date': '',
        'content_length': 0,
        'has_author': False,
        'has_publish_date': False,
        'accessible': False
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                content_info['title'] = title_tag.get_text().strip()
            
            # Extract author
            author_patterns = [
                soup.find('meta', {'name': 'author'}),
                soup.find('meta', {'property': 'article:author'}),
                soup.find(class_=re.compile(r'author', re.I)),
                soup.find('a', href=re.compile(r'author', re.I))
            ]
            
            for pattern in author_patterns:
                if pattern and pattern.get('content'):
                    content_info['author'] = pattern.get('content').strip()
                    content_info['has_author'] = True
                    break
                elif pattern and pattern.get_text():
                    content_info['author'] = pattern.get_text().strip()
                    content_info['has_author'] = True
                    break
            
            # Extract publish date
            date_patterns = [
                soup.find('meta', {'property': 'article:published_time'}),
                soup.find('meta', {'name': 'publish_date'}),
                soup.find('meta', {'property': 'published_time'}),
                soup.find(class_=re.compile(r'date|time|publish', re.I))
            ]
            
            for pattern in date_patterns:
                if pattern and pattern.get('content'):
                    content_info['publish_date'] = pattern.get('content').strip()
                    content_info['has_publish_date'] = True
                    break
                elif pattern and pattern.get_text():
                    content_info['publish_date'] = pattern.get_text().strip()
                    content_info['has_publish_date'] = True
                    break
            
            # Calculate content length
            text_content = soup.get_text()
            content_info['content_length'] = len(text_content)
            content_info['accessible'] = True
            
    except Exception as e:
        print(f"Error analyzing URL content: {e}")
    
    return content_info

def comprehensive_source_verification(url):
    """Comprehensive source verification"""
    domain = extract_domain(url)
    domain_info = check_domain_trust(domain)
    content_info = analyze_url_content(url)
    
    # Calculate overall score
    base_score = domain_info['trust_score']
    
    # Adjust score based on content analysis
    if content_info['accessible']:
        if content_info['has_author']:
            base_score += 5
        if content_info['has_publish_date']:
            base_score += 5
        if content_info['content_length'] > 1000:
            base_score += 5
        elif content_info['content_length'] < 200:
            base_score -= 10
    
    overall_score = max(0, min(100, base_score))
    
    # Determine risk level
    if overall_score >= 80:
        risk_level = "Low Risk"
    elif overall_score >= 60:
        risk_level = "Medium Risk"
    elif overall_score >= 40:
        risk_level = "High Risk"
    else:
        risk_level = "Very High Risk"
    
    # Generate recommendation
    if domain_info['is_trusted']:
        recommendation = "Generally trustworthy source"
    elif domain_info['is_suspicious']:
        recommendation = "Likely unreliable, verify with other sources"
    elif overall_score >= 70:
        recommendation = "Moderately trustworthy, but verify important claims"
    else:
        recommendation = "Unreliable source, avoid sharing"
    
    return {
        'domain': domain,
        'domain_info': domain_info,
        'content_info': content_info,
        'overall_score': overall_score,
        'risk_level': risk_level,
        'recommendation': recommendation,
        'verification_timestamp': pd.Timestamp.now().isoformat()
    }

# Routes
@app.route('/')
def home():
    return jsonify({
        'message': 'Enhanced Fake News Detection API - Production Ready',
        'version': '2.0',
        'status': 'healthy',
        'endpoints': [
            'POST /predict - Simple text prediction',
            'POST /analyze - Enhanced analysis with headline/article',
            'POST /verify-source - Source verification',
            'POST /analyze-with-source - Combined analysis'
        ]
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Simple prediction endpoint"""
    if not model or not vectorizer:
        return jsonify({'error': 'Model not loaded'}), 500
    
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Clean and preprocess text
    cleaned_text = clean_text(text)
    
    # Vectorize text
    text_vector = vectorizer.transform([cleaned_text])
    
    # Make prediction
    prediction = model.predict(text_vector)[0]
    prediction_proba = model.predict_proba(text_vector)[0]
    
    # Calculate confidence
    confidence = max(prediction_proba)
    fake_prob = prediction_proba[0] if model.classes_[0] == 'Fake News' else prediction_proba[1]
    real_prob = prediction_proba[1] if model.classes_[1] == 'Real News' else prediction_proba[0]
    
    # Convert prediction to text
    prediction_text = "Fake News" if prediction == 0 else "Real News"
    
    # Calculate credibility score
    credibility_score = get_credibility_score(confidence, prediction_text)
    
    # Generate explanation
    if prediction_text == "Fake News":
        explanation = "This text shows characteristics commonly found in fake news, such as sensational language or lack of credible sources."
    else:
        explanation = "This text appears to be legitimate news with proper structure and credible content."
    
    return jsonify({
        'prediction': prediction_text,
        'confidence': float(confidence),
        'confidence_level': get_confidence_level(confidence),
        'fake_probability': float(fake_prob),
        'real_probability': float(real_prob),
        'credibility_score': credibility_score,
        'explanation': explanation
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """Enhanced analysis endpoint"""
    if not model or not vectorizer:
        return jsonify({'error': 'Model not loaded'}), 500
    
    data = request.json
    headline = data.get('headline', '')
    article = data.get('article', '')
    
    if not headline and not article:
        return jsonify({'error': 'No headline or article provided'}), 400
    
    # Combine headline and article
    combined_text = f"{headline} {article}".strip()
    cleaned_text = clean_text(combined_text)
    
    # Vectorize text
    text_vector = vectorizer.transform([cleaned_text])
    
    # Make prediction
    prediction = model.predict(text_vector)[0]
    prediction_proba = model.predict_proba(text_vector)[0]
    
    # Calculate confidence
    confidence = max(prediction_proba)
    fake_prob = prediction_proba[0] if model.classes_[0] == 'Fake News' else prediction_proba[1]
    real_prob = prediction_proba[1] if model.classes_[1] == 'Real News' else prediction_proba[0]
    
    # Convert prediction to text
    prediction_text = "Fake News" if prediction == 0 else "Real News"
    
    # Calculate credibility score
    credibility_score = get_credibility_score(confidence, prediction_text)
    
    # Generate explanation
    if prediction_text == "Fake News":
        explanation = "This article shows characteristics commonly found in fake news, such as sensational language, lack of credible sources, or emotional appeals."
    else:
        explanation = "This article appears to be legitimate news with proper structure, credible content, and objective reporting."
    
    # Generate credibility reasons
    credibility_reasons = []
    if confidence >= 0.8:
        credibility_reasons.append("High confidence in prediction")
    if len(cleaned_text.split()) > 50:
        credibility_reasons.append("Substantial content length")
    if prediction_text == "Real News":
        credibility_reasons.append("Shows legitimate news characteristics")
    
    return jsonify({
        'prediction': prediction_text,
        'confidence': float(confidence),
        'confidence_level': get_confidence_level(confidence),
        'fake_probability': float(fake_prob),
        'real_probability': float(real_prob),
        'credibility_score': credibility_score,
        'credibility_reasons': credibility_reasons,
        'explanation': explanation
    })

@app.route('/verify-source', methods=['POST'])
def verify_source():
    """Source verification endpoint"""
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    verification_result = comprehensive_source_verification(url)
    return jsonify(verification_result)

@app.route('/analyze-with-source', methods=['POST'])
def analyze_with_source():
    """Combined text analysis + source verification"""
    data = request.json
    headline = data.get('headline', '')
    article = data.get('article', '')
    url = data.get('url', '')
    
    # Analyze text
    text = f"{headline} {article}".strip()
    text_analysis = None
    
    if text and model and vectorizer:
        cleaned_text = clean_text(text)
        text_vector = vectorizer.transform([cleaned_text])
        prediction = model.predict(text_vector)[0]
        prediction_proba = model.predict_proba(text_vector)[0]
        
        confidence = max(prediction_proba)
        fake_prob = prediction_proba[0] if model.classes_[0] == 'Fake News' else prediction_proba[1]
        real_prob = prediction_proba[1] if model.classes_[1] == 'Real News' else prediction_proba[0]
        
        prediction_text = "Fake News" if prediction == 0 else "Real News"
        credibility_score = get_credibility_score(confidence, prediction_text)
        
        text_analysis = {
            'prediction': prediction_text,
            'confidence': float(confidence),
            'confidence_level': get_confidence_level(confidence),
            'fake_probability': float(fake_prob),
            'real_probability': float(real_prob),
            'credibility_score': credibility_score,
            'explanation': "This analysis combines text patterns with source verification for comprehensive assessment."
        }
    
    # Verify source if URL provided
    source_verification = None
    if url:
        source_verification = comprehensive_source_verification(url)
    
    # Combine results
    combined_result = {
        'text_analysis': text_analysis,
        'source_verification': source_verification,
        'has_text': bool(text),
        'has_url': bool(url),
        'analysis_timestamp': pd.Timestamp.now().isoformat()
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'models_loaded': model is not None and vectorizer is not None,
        'timestamp': pd.Timestamp.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
