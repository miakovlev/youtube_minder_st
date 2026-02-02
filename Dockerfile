FROM python:3.12-slim

# Install system dependencies
# ffmpeg is required for yt-dlp audio extraction
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for yt-dlp JS runtime / EJS challenge)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get update && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first to leverage cache
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-cache

# Use the uv-managed virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Streamlit listens on 8501 by default
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "src/youtube_minder/ui/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
