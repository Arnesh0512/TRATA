# Use a stable official Python image with pre-compiled build tools
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for compilation and Git LFS models
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code and models into the container
COPY . .

# Expose port (Render automatically maps $PORT dynamically)
EXPOSE 8000

# Start FastAPI using Uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]