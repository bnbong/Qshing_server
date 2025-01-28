# Qshing Server

CNN + BERT multimodal Phishing Detection Server 입니다.

## Base Stack

- Python 3.12
- FastAPI 0.115.7 + Pydantic 2.7.1 + Uvicorn 0.34.0
- Docker

## Setup

### 0. 가상 환경 설정

로컬에 Python 3.12 이상 버전이 설치되어 있어야 합니다.

```bash
# virtualenv 사용 시
python -m venv venv

source venv/bin/activate  # MacOS
venv/Scripts/activate  # Windows
```

<details>
<summary><b>PDM 사용 시) 가상 환경 동기화</b></summary>
<div markdown="1">

PDM 사용 시 가상 환경 동기화가 필요합니다.

```bash
pdm use -f <방금 생성한 venv 경로>
```

</div>
</details>

### 1. 패키지 설치

가상 환경에서 다음 명령어를 실행합니다.

```bash
# pip 사용 시
pip install -r requirements.txt

# PDM 사용 시
pdm install -G dev
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env.dev` 파일의 특정 항목을 수정합니다.

- `SECRET_KEY` : 32자 이상의 랜덤 문자열

수정 이후 다음 명령어를 실행합니다.

```bash
cp .env.dev .env
```

### 3. 서버 실행

프로젝트 루트에서 실행합니다.

```bash
# 기본 실행 명령어
uvicorn src.qshing_server.main:app --reload

# PDM 사용 시
pdm run uvicorn src.qshing_server.main:app --reload
```
