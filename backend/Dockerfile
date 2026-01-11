# Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirement files
COPY requirements_backend.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements_backend.txt

# Copy backend code
COPY backend ./backend
COPY template ./template

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "backend.api"]
