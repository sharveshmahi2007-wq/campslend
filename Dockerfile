# Official lightweight Python 3.12 image
FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable unbuffered terminal logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install project dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py .
COPY index.html .
COPY translations.js .
COPY assets/ ./assets/

# Expose web & API port
EXPOSE 8080

# Environment variables
ENV PORT=8080
ENV MONGO_URI=mongodb://mongodb:27017/
ENV MONGO_DB_NAME=lend

# Run application
CMD ["python", "api.py"]

