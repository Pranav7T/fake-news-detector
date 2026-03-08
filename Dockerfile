FROM python:3.11.5-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements-deploy.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy application files
COPY backend/ ./backend/
COPY app.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start the application
CMD gunicorn --bind 0.0.0.0:$PORT app:app
