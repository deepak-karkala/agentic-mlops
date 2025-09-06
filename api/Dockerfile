FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and uv.lock first for better caching
COPY pyproject.toml uv.lock* ./

# Install uv
RUN pip install uv

# Install Python dependencies
RUN uv sync --no-dev

# Copy source code
COPY api/ ./api/
COPY libs/ ./libs/

# Set Python path to include the current directory
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Use uv to run the application
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]