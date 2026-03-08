# 🚀 AI Fake News Detector - Deployment Guide

## 📋 Overview
This guide will help you deploy the AI Fake News Detector to Render with GitHub integration. The project is structured to be production-ready with minimal changes while keeping it extensible for future features.

## 🏗️ Architecture
- **Backend**: Flask API with ML models
- **Frontend**: React.js application
- **Deployment**: Render (Backend) + GitHub Pages (Frontend)
- **CI/CD**: GitHub Actions for auto-deployment

## 🚀 Quick Deployment Steps

### 1. Backend Deployment (Render)

#### Step 1: Prepare Your Repository
```bash
# Make sure your code is pushed to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main
```

#### Step 2: Set Up Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Click "New" → "Web Service"
4. Connect your GitHub repository

#### Step 3: Configure Render Service
- **Name**: `fake-news-detector-api`
- **Environment**: `Python 3`
- **Region**: Choose nearest region
- **Branch**: `main`
- **Root Directory**: `.` (root)
- **Build Command**: `pip install -r requirements-deploy.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
- **Instance Type**: `Free`

#### Step 4: Environment Variables
Add these environment variables:
- `PYTHON_VERSION`: `3.11.5`
- `FLASK_ENV`: `production`

### 2. Frontend Deployment (GitHub Pages)

#### Step 1: Install gh-pages
```bash
cd frontend
npm install gh-pages --save-dev
```

#### Step 2: Update API URL
In `frontend/src/App.js`, update the API URL:
```javascript
// Change from localhost to your Render URL
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

#### Step 3: Deploy to GitHub Pages
```bash
cd frontend
npm run deploy
```

## 🔧 Configuration Files

### Backend Configuration
- `app.py` - Production-ready Flask application
- `requirements-deploy.txt` - Python dependencies
- `Dockerfile` - Container configuration (optional)
- `render.yaml` - Render service configuration

### Frontend Configuration
- `package.json` - Updated with deployment scripts
- `homepage: "."` - GitHub Pages configuration

### CI/CD Configuration
- `.github/workflows/deploy.yml` - Auto-deployment workflow
- Requires `RENDER_SERVICE_ID` and `RENDER_API_KEY` secrets

## 🔐 Environment Setup

### Required Secrets for GitHub Actions
1. **Render Service ID**: Get from Render dashboard
2. **Render API Key**: Generate from Render account settings

### Adding Secrets to GitHub
1. Go to repository → Settings → Secrets
2. Click "New repository secret"
3. Add:
   - `RENDER_SERVICE_ID`: Your service ID
   - `RENDER_API_KEY`: Your API key

## 📊 Future-Ready Features

The deployment is structured to easily add:

### 🔐 Authentication
```python
# Add to app.py
from flask_jwt_extended import JWTManager, create_access_token

@app.route('/login', methods=['POST'])
def login():
    # Authentication logic
    return jsonify({'access_token': token})
```

### 🗄️ Database Integration
```python
# Add to requirements-deploy.txt
# psycopg2-binary==2.9.7
# sqlalchemy==2.0.20

# Add to app.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
```

### 📈 Analytics & Monitoring
```python
# Add to app.py
from prometheus_client import Counter, generate_latest

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 🔄 Caching
```python
# Add to requirements-deploy.txt
# redis==4.6.0

# Add to app.py
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

## 🧪 Testing Before Deployment

### Backend Tests
```bash
# Test Flask app locally
python app.py

# Test endpoints
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Test news article"}'
```

### Frontend Tests
```bash
cd frontend
npm test
npm run build
```

## 📱 Monitoring & Logging

### Health Checks
- `/health` endpoint for monitoring
- Automatic health checks configured
- Render provides built-in monitoring

### Logging
```python
# Add to app.py
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Model Loading Errors
```bash
# Ensure model files are in correct location
ls -la backend/model.pkl backend/vectorizer.pkl
```

#### 2. CORS Issues
```python
# Check CORS configuration in app.py
CORS(app, origins=["your-frontend-url"])
```

#### 3. Memory Issues
```python
# Add to render.yaml - increase instance size
plan: starter  # Instead of free
```

#### 4. Build Failures
```bash
# Check build logs on Render dashboard
# Verify requirements-deploy.txt
```

## 🔄 CI/CD Pipeline

### Automatic Deployment
1. Push to `main` branch
2. GitHub Actions runs tests
3. If tests pass, deploys to Render
4. Frontend deploys to GitHub Pages

### Manual Deployment
```bash
# Backend
git push origin main

# Frontend
cd frontend
npm run deploy
```

## 📈 Scaling Considerations

### When to Upgrade
- **Free Tier**: 512MB RAM, 750 hours/month
- **Starter**: 2GB RAM, 750 hours/month
- **Standard**: 4GB RAM, unlimited hours

### Load Balancing
Render automatically handles load balancing for multiple instances.

## 🔒 Security Best Practices

### API Security
- CORS configured for specific origins
- Environment variables for sensitive data
- Rate limiting can be added

### Database Security
- Use connection strings with SSL
- Implement proper user authentication
- Regular security updates

## 📞 Support

### Render Support
- Documentation: [render.com/docs](https://render.com/docs)
- Status page: [status.render.com](https://status.render.com)

### GitHub Pages Support
- Documentation: [pages.github.com](https://pages.github.com)

## 🎉 Success Criteria

✅ **Backend deployed and accessible**
✅ **Frontend deployed and functional**
✅ **All API endpoints working**
✅ **CI/CD pipeline active**
✅ **Health checks passing**
✅ **Ready for future enhancements**

---

## 🚀 Your Live Application

Once deployed, your application will be available at:
- **Backend**: `https://your-app-name.onrender.com`
- **Frontend**: `https://your-username.github.io/your-repo`

The application is now production-ready and can be extended with authentication, database integration, and advanced features!
