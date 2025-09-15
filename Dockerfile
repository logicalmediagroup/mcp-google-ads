# Dockerfile
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Debug: List files to verify they're there
RUN ls -la /app/harry-714-key.json || echo "Key file not found during build"
RUN ls -la /app/ | head -20

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Debug: Verify files are accessible as appuser
RUN ls -la /app/harry-714-key.json || echo "Key file not accessible as appuser"

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Set default PORT for local testing
ENV PORT=8080

# Start the MCP server
CMD ["python", "google_ads_server.py"]