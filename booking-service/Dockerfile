# Use an official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and requirements
COPY . .

# Install dependencies
# RUN pip install --no-cache-dir flask kafka-python

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
