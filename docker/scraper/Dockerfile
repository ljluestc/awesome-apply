# Job scraper service container
FROM python:3.13-slim-bookworm

WORKDIR /app

# Install system dependencies for headless browsing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    unzip \
    gnupg2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for headless scraping
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/""$CHROMEDRIVER_VERSION""/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 scraperuser && \
    chown -R scraperuser:scraperuser /app
USER scraperuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Start Xvfb for headless browsing
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & python ultimate_job_scraper.py"]