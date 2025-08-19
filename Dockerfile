FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for EasyOCR
RUN apt-get update && apt-get install -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD gunicorn --bind 0.0.0.0:${PORT} app:app
