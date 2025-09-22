FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

# Start the application with proper configuration
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1