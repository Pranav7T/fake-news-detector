import pandas as pd
import numpy as np
import pickle
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

print("🔍 IMPROVEMENT 9: NEWS SOURCE VERIFICATION")
print("=" * 60)

# Trusted and suspicious domain lists
TRUSTED_DOMAINS = {
    # Major international news
    'reuters.com': {'trust_score': 95, 'category': 'International News', 'description': 'Global news agency with strict editorial standards'},
    'ap.org': {'trust_score': 95, 'category': 'International News', 'description': 'Associated Press - Leading news agency'},
    'bbc.com': {'trust_score': 90, 'category': 'International News', 'description': 'British Broadcasting Corporation - Public service broadcaster'},
    'cnn.com': {'trust_score': 85, 'category': 'International News', 'description': 'Cable News Network - Major US news network'},
    'nytimes.com': {'trust_score': 90, 'category': 'International News', 'description': 'The New York Times - Pulitzer-winning newspaper'},
    'washingtonpost.com': {'trust_score': 88, 'category': 'International News', 'description': 'The Washington Post - Major US newspaper'},
    'wsj.com': {'trust_score': 90, 'category': 'International News', 'description': 'The Wall Street Journal - Business-focused news'},
    
    # Indian news (trusted)
    'thehindu.com': {'trust_score': 85, 'category': 'Indian News', 'description': 'The Hindu - Leading Indian newspaper'},
    'timesofindia.indiatimes.com': {'trust_score': 75, 'category': 'Indian News', 'description': 'Times of India - Major Indian newspaper'},
    'indianexpress.com': {'trust_score': 80, 'category': 'Indian News', 'description': 'The Indian Express - Leading Indian newspaper'},
    'hindustantimes.com': {'trust_score': 75, 'category': 'Indian News', 'description': 'Hindustan Times - Major Indian newspaper'},
    'ndtv.com': {'trust_score': 80, 'category': 'Indian News', 'description': 'NDTV - Leading Indian news channel'},
    'economictimes.indiatimes.com': {'trust_score': 85, 'category': 'Indian News', 'description': 'Economic Times - Business news in India'},
    
    # Science and tech (trusted)
    'nature.com': {'trust_score': 95, 'category': 'Science', 'description': 'Nature - Leading scientific journal'},
    'science.org': {'trust_score': 95, 'category': 'Science', 'description': 'Science - Leading scientific journal'},
    'techcrunch.com': {'trust_score': 85, 'category': 'Technology', 'description': 'TechCrunch - Technology news and analysis'},
    'wired.com': {'trust_score': 85, 'category': 'Technology', 'description': 'Wired - Technology and culture magazine'},
    'arstechnica.com': {'trust_score': 90, 'category': 'Technology', 'description': 'Ars Technica - Technology news site'},
    
    # Business (trusted)
    'bloomberg.com': {'trust_score': 90, 'category': 'Business', 'description': 'Bloomberg - Financial news and data'},
    'forbes.com': {'trust_score': 85, 'category': 'Business', 'description': 'Forbes - Business and financial news'},
    'fortune.com': {'trust_score': 85, 'category': 'Business', 'description': 'Fortune - Business magazine'},
    'businessinsider.com': {'trust_score': 80, 'category': 'Business', 'description': 'Business Insider - Business news site'},
    
    # Government and educational (trusted)
    'gov.in': {'trust_score': 95, 'category': 'Government', 'description': 'Indian Government websites'},
    'gov': {'trust_score': 95, 'category': 'Government', 'description': 'US Government websites'},
    'edu': {'trust_score': 90, 'category': 'Education', 'description': 'Educational institutions'},
    'ac.in': {'trust_score': 90, 'category': 'Education', 'description': 'Indian educational institutions'},
    
    # Health (trusted)
    'who.int': {'trust_score': 95, 'category': 'Health', 'description': 'World Health Organization'},
    'cdc.gov': {'trust_score': 95, 'category': 'Health', 'description': 'Centers for Disease Control and Prevention'},
    'nih.gov': {'trust_score': 95, 'category': 'Health', 'description': 'National Institutes of Health'},
    'mayoclinic.org': {'trust_score': 90, 'category': 'Health', 'description': 'Mayo Clinic - Medical research and care'},
}

SUSPICIOUS_DOMAINS = {
    # Known fake news/spam domains
    'theonion.com': {'trust_score': 20, 'category': 'Satire', 'description': 'The Onion - Satirical news site'},
    'clickhole.com': {'trust_score': 20, 'category': 'Satire', 'description': 'ClickHole - Satirical content'},
    'dailycurrant.com': {'trust_score': 15, 'category': 'Fake News', 'description': 'Daily Currant - Fake news site'},
    'empirenews.net': {'trust_score': 15, 'category': 'Fake News', 'description': 'Empire News - Fake news site'},
    'nationalreport.net': {'trust_score': 15, 'category': 'Fake News', 'description': 'National Report - Fake news site'},
    'worldnewsdailyreport.com': {'trust_score': 15, 'category': 'Fake News', 'description': 'World News Daily Report - Fake news site'},
    
    # Suspicious patterns
    'news-': {'trust_score': 30, 'category': 'Suspicious Pattern', 'description': 'Domain with hyphen in news'},
    '-news': {'trust_score': 30, 'category': 'Suspicious Pattern', 'description': 'Domain with hyphen in news'},
    'news24': {'trust_score': 40, 'category': 'Suspicious Pattern', 'description': 'Generic news24 pattern'},
    'breakingnews': {'trust_score': 35, 'category': 'Suspicious Pattern', 'description': 'Generic breaking news pattern'},
    'daily': {'trust_score': 45, 'category': 'Suspicious Pattern', 'description': 'Generic daily news pattern'},
    
    # Low credibility indicators
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

# Test the verification system
test_urls = [
    "https://www.reuters.com/world/asia-pacific/india-launches-new-satellite-weather-monitoring-2023-03-15/",
    "https://www.bbc.com/news/science-environment-56789012",
    "https://theonion.com/breaking-scientists-discover-earth-actually-flat-1815901234/",
    "https://suspicious-news24.com/fake-breaking-news-conspiracy-12345/",
    "https://www.ndtv.com/india-news/india-launches-new-satellite-weather-monitoring-123456",
    "https://www.who.int/news/item/15-03-2023-covid-19-update",
    "https://invalid-url-that-does-not-exist.com/fake-news"
]

print("\n🔍 TESTING NEWS SOURCE VERIFICATION:")
print("=" * 60)

for i, url in enumerate(test_urls, 1):
    print(f"\n📰 TEST {i}: {url[:60]}...")
    result = comprehensive_source_verification(url)
    
    print(f"🌐 Domain: {result['domain']}")
    print(f"📊 Trust Score: {result['overall_score']}/100")
    print(f"⚠️  Risk Level: {result['risk_level']}")
    print(f"📝 Category: {result['domain_info']['category']}")
    print(f"💬 Description: {result['domain_info']['description']}")
    print(f"✅ Recommendation: {result['recommendation']}")
    
    if result['content_info'].get('title'):
        print(f"📄 Title: {result['content_info']['title'][:50]}...")
    
    if result['content_info'].get('error'):
        print(f"❌ Content Error: {result['content_info']['error']}")
    
    print("-" * 40)

print(f"\n✅ NEWS SOURCE VERIFICATION SYSTEM READY!")
print(f"✅ Trusted domains: {len(TRUSTED_DOMAINS)} sources")
print(f"✅ Suspicious patterns: {len(SUSPICIOUS_DOMAINS)} patterns")
print(f"✅ Content analysis enabled")
print(f"✅ Risk assessment implemented")
print(f"✅ Ready for integration with main system")

# Save the verification system
import json

verification_data = {
    'trusted_domains': TRUSTED_DOMAINS,
    'suspicious_domains': SUSPICIOUS_DOMAINS,
    'version': '1.0',
    'last_updated': pd.Timestamp.now().isoformat()
}

with open('source_verification_data.json', 'w') as f:
    json.dump(verification_data, f, indent=2)

print(f"✅ Verification data saved to source_verification_data.json")
