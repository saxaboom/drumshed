# Use an official Python image as base
FROM python:3.13-slim

# Install system dependencies needed for sounddevice
RUN apt-get update && apt-get install -y portaudio19-dev && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt into container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code into container
COPY drumshed.py .

# Expose port (Streamlit runs on 8501 by default)
EXPOSE 8501

# Run your app
CMD ["streamlit", "run", "drumshed.py"]

