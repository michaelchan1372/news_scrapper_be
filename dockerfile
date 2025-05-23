FROM continuumio/miniconda3

# Copy environment and install
COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

# Activate environment
SHELL ["conda", "run", "-n", "fastapi-env", "/bin/bash", "-c"]

# Copy app
WORKDIR /app
COPY app /app

# Expose port
EXPOSE 8000

# Install required packages
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 \
    libxss1 libappindicator1 libasound2 xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver (match version to Chrome)
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Set display port to avoid crashing
ENV DISPLAY=:99

# Command
CMD ["conda", "run", "--no-capture-output", "-n", "scrapper_env", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
