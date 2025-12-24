# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install necessary system packages for mysqlclient
RUN apt-get update && apt-get install -y \
    pkg-config \
    libmariadb-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies (clean up apt cache to save space)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy the rest of the application
COPY . /app

# Create necessary directories for file uploads
RUN mkdir -p /app/MEDIA_ROOT /app/TEMP_MEDIA_ROOT /app/Reports

# Expose port 8000 for the application to listen on
EXPOSE 8000

# Set environment variables for Django
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.settings

# Run the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
