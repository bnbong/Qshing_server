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
    && mkdir -p /usr/lib/chromium \
    && mkdir -p /home/chrome/.cache \
    && chmod 755 /home/chrome/.cache

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# Chrome 최적화 설정
ENV CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-extensions --disable-plugins --disable-images --disable-javascript --memory-pressure-off --max_old_space_size=4096"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# check model file exists after copying files
RUN if [ ! -f "src/qshing_server/service/model/best_acc_model.pt" ]; then \
    echo "Model file not found. Please check the model file exists at src/qshing_server/service/model/best_acc_model.pt"; \
    exit 1; \
fi

# 비root 사용자 생성 및 권한 설정
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /home/chrome

USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.qshing_server.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
