# Qshing Server

CNN + BERT multimodal Phishing Detection Server 입니다.

## Base Stack

- Python 3.12
- FastAPI 0.115.7 + Pydantic 2.7.1 + Uvicorn 0.34.0
- Docker

## Project Structure

```
.
├── CHANGELOG.md
├── Dockerfile
├── README.md
├── log (auto-generated)
├── pdm.lock
├── pyproject.toml
├── requirements.txt
├── scripts
│   ├── fetch-dependency.sh
│   ├── format.sh
│   └── lint.sh
├── src
│   └── qshing_server
│       ├── __init__.py
│       ├── api
│       │   ├── __init__.py
│       │   └── phishing_routers.py
│       ├── core
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── exceptions.py
│       ├── dto
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── phishing_schema.py
│       ├── main.py
│       ├── py.typed
│       ├── service
│       │   ├── __init__.py
│       │   ├── model
│       │   │   ├── __init__.py
│       │   │   ├── best_acc_model.pt (**해당 폴더 위치에 모델 체크포인트 파일 필수**)
│       │   │   ├── model_manager.py
│       │   │   ├── preprocessor.py
│       │   │   ├── qbert.py
│       │   │   └── tokenizer.py
│       │   ├── parser
│       │   │   ├── __init__.py
│       │   │   └── html_loader.py
│       │   └── phishing_analyzer.py
│       └── utils
│           ├── __init__.py
│           ├── enums.py
│           └── logging.py
└── tests
```

## Setup

### 0. 프로젝트 로컬 설치 & 가상 환경 설정

저장소를 clone 합니다.

```bash
git clone https://github.com/capston-qrcode/Qshing_server.git
```

설치를 완료하면 `src/qshing_server/service/model` 폴더 위치에 ai 모델 파일을 __반드시__ 넣어주세요.

<br>

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
- `MODEL_NAME` : 모델 파일 이름

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
