FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY scraper.py .
COPY vector_store_manager.py .


RUN mkdir articles
COPY articles/ ./articles/
COPY articles_metadata.json .

# Environment variables will be passed at runtime
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "main.py"]