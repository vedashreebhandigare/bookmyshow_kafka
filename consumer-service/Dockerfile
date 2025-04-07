# Use an official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir flask kafka-python mysql-connector-python

# Expose consumer monitoring port (optional)
EXPOSE 5001

# Run the app
CMD ["python", "app.py"]
