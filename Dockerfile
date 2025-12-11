FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# ffmpeg is required for audio format conversion 
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .
RUN mkdir models output

EXPOSE 8000

CMD ["python", "server.py"]
