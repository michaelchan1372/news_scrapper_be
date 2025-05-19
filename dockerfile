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

# Command
CMD ["conda", "run", "--no-capture-output", "-n", "scrapper_env", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
