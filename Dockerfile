FROM python:3.12-slim

WORKDIR /app

# install chromium (Architecture : ARM)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    apt-transport-https \
    ca-certificates \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/lib/chromium

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# check model file exists after copying files
RUN if [ ! -f "src/qshing_server/service/model/best_acc_model.pt" ]; then \
    echo "Model file not found. Please check the model file exists at src/qshing_server/service/model/best_acc_model.pt"; \
    exit 1; \
fi

CMD ["uvicorn", "src.qshing_server.main:app", "--host", "0.0.0.0", "--port", "8080"]
