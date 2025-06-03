FROM python:3.12-slim

WORKDIR /app

# Hugging Face 캐시 경로 빌드 인수 및 환경 변수 설정
ARG HF_HOME=/tmp/huggingface
ARG TRANSFORMERS_CACHE=/tmp/huggingface/transformers
ARG HF_DATASETS_CACHE=/tmp/huggingface/datasets
ARG HUGGINGFACE_HUB_CACHE=/tmp/huggingface/hub
ARG TMPDIR=/tmp

ENV HF_HOME=${HF_HOME}
ENV TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
ENV HF_DATASETS_CACHE=${HF_DATASETS_CACHE}
ENV HUGGINGFACE_HUB_CACHE=${HUGGINGFACE_HUB_CACHE}
ENV TMPDIR=${TMPDIR}

# install chromium (Architecture : ARM)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    apt-transport-https \
    ca-certificates \
    chromium \
    chromium-driver \
    && apt-get clean

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# check model file exists after copying files
RUN if [ ! -f "src/qshing_server/service/model/best_acc_model.pt" ]; then \
    echo "Model file not found. Please check the model file exists at src/qshing_server/service/model/best_acc_model.pt"; \
    exit 1; \
fi

EXPOSE 8080

CMD ["uvicorn", "src.qshing_server.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
