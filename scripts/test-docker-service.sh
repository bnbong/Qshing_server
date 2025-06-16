#!/bin/bash

# Qshing Server Docker 서비스 통합 테스트 스크립트
# Dockerfile로 빌드된 컨테이너가 제대로 동작하는지 확인

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정 변수
CONTAINER_NAME="qshing-server-test"
IMAGE_NAME="qshing-server-local"
SERVICE_PORT="8080"
HOST_PORT="8081"
TEST_URL="https://www.oracle.com/"

echo -e "${BLUE}🚀 Qshing Server Docker 서비스 통합 테스트 시작${NC}"
echo "=================================="

# 1. 기존 컨테이너 정리
echo -e "${YELLOW}🧹 1단계: 기존 테스트 환경 정리...${NC}"
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true
docker rmi $IMAGE_NAME 2>/dev/null || true

# 2. AI 모델 파일 확인
echo -e "${YELLOW}🔍 2단계: AI 모델 파일 확인...${NC}"
if [ ! -f "src/qshing_server/service/model/best_acc_model.pt" ]; then
    echo -e "${RED}❌ AI 모델 파일이 없습니다: src/qshing_server/service/model/best_acc_model.pt${NC}"
    echo "모델 파일을 다운로드하거나 경로를 확인해주세요."
    exit 1
fi
echo -e "${GREEN}✅ AI 모델 파일 확인 완료${NC}"

# 3. 환경 파일 생성
echo -e "${YELLOW}🔧 3단계: 테스트용 환경 파일 생성...${NC}"
cat > .env.test << EOF
# Test Environment Configuration
ENVIRONMENT=development

# Database Configuration (로컬 테스트용)
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=qshing_db

MONGODB_HOST=host.docker.internal
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASSWORD=password
MONGODB_NAME=phishing_feedback

REDIS_HOST=host.docker.internal
REDIS_PORT=6379
REDIS_DB=0

# Hugging Face 캐시 경로 설정 (권한 문제 해결)
HF_HOME=/tmp/huggingface
TRANSFORMERS_CACHE=/tmp/huggingface/transformers
HF_DATASETS_CACHE=/tmp/huggingface/datasets
HUGGINGFACE_HUB_CACHE=/tmp/huggingface/hub
TMPDIR=/tmp
EOF

echo -e "${GREEN}✅ 환경 파일 생성 완료${NC}"

# 4. 데이터베이스 서비스 시작
echo -e "${YELLOW}🗄️ 4단계: 데이터베이스 서비스 시작...${NC}"
docker-compose up -d
echo "데이터베이스 서비스 시작 대기 중..."
sleep 15

# 5. Docker 이미지 빌드
echo -e "${YELLOW}🔨 5단계: Docker 이미지 빌드...${NC}"
docker build -t $IMAGE_NAME .
echo -e "${GREEN}✅ Docker 이미지 빌드 완료${NC}"

# 6. 컨테이너 실행
echo -e "${YELLOW}🚀 6단계: 컨테이너 실행...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env.test \
    -p $HOST_PORT:$SERVICE_PORT \
    --add-host=host.docker.internal:host-gateway \
    $IMAGE_NAME

echo "컨테이너 시작 대기 중..."
sleep 30

# 7. 컨테이너 상태 확인
echo -e "${YELLOW}🔍 7단계: 컨테이너 상태 확인...${NC}"
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo -e "${RED}❌ 컨테이너가 실행되지 않았습니다${NC}"
    echo "컨테이너 로그:"
    docker logs $CONTAINER_NAME
    exit 1
fi
echo -e "${GREEN}✅ 컨테이너 정상 실행 중${NC}"

# 8. 서비스 응답 대기
echo -e "${YELLOW}⏳ 8단계: 서비스 응답 대기...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:$HOST_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 서비스 응답 확인 (${i}초 후)${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 서비스 응답 타임아웃${NC}"
        echo "컨테이너 로그:"
        docker logs $CONTAINER_NAME --tail=20
        exit 1
    fi
    echo "서비스 응답 대기 중... ($i/30)"
    sleep 2
done

# 9. Health Check 엔드포인트 테스트
echo -e "${YELLOW}🏥 9단계: Health Check 엔드포인트 테스트...${NC}"

# /health 엔드포인트 테스트
echo "Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:$HOST_PORT/health)
HTTP_CODE="${HEALTH_RESPONSE: -3}"
HEALTH_BODY="${HEALTH_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ /health 엔드포인트 정상 (HTTP $HTTP_CODE)${NC}"
    echo "Response: $HEALTH_BODY"
else
    echo -e "${RED}❌ /health 엔드포인트 실패 (HTTP $HTTP_CODE)${NC}"
    echo "Response: $HEALTH_BODY"
fi

# /ready 엔드포인트 테스트
echo "Testing /ready endpoint..."
READY_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:$HOST_PORT/ready)
HTTP_CODE="${READY_RESPONSE: -3}"
READY_BODY="${READY_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ /ready 엔드포인트 정상 (HTTP $HTTP_CODE)${NC}"
    echo "Response: $READY_BODY"
else
    echo -e "${RED}❌ /ready 엔드포인트 실패 (HTTP $HTTP_CODE)${NC}"
    echo "Response: $READY_BODY"
fi

# 10. Analyze 엔드포인트 테스트
echo -e "${YELLOW}🔍 10단계: Analyze 엔드포인트 테스트...${NC}"
echo "Testing analyze endpoint with URL: $TEST_URL"

ANALYZE_RESPONSE=$(curl -s -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$TEST_URL\"}" \
    http://localhost:$HOST_PORT/phishing-detection/analyze)

HTTP_CODE="${ANALYZE_RESPONSE: -3}"
ANALYZE_BODY="${ANALYZE_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ /analyze 엔드포인트 정상 (HTTP $HTTP_CODE)${NC}"
    echo "Response: $ANALYZE_BODY"
else
    echo -e "${RED}❌ /analyze 엔드포인트 실패 (HTTP $HTTP_CODE)${NC}"
    echo "Response: $ANALYZE_BODY"
    echo "컨테이너 로그 (최근 20줄):"
    docker logs $CONTAINER_NAME --tail=20
fi

# 11. 컨테이너 리소스 사용량 확인
echo -e "${YELLOW}📊 11단계: 컨테이너 리소스 사용량 확인...${NC}"
docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 12. 컨테이너 로그 확인
echo -e "${YELLOW}📋 12단계: 컨테이너 로그 확인...${NC}"
echo "최근 로그 (마지막 10줄):"
docker logs $CONTAINER_NAME --tail=10

# 13. pytest 실행 (선택사항)
echo -e "${YELLOW}🧪 13단계: pytest 실행...${NC}"
if command -v pytest &> /dev/null; then
    echo "pytest를 사용하여 추가 테스트 실행..."
    
    # 테스트용 환경 변수 설정
    export QSHING_SERVER_URL="http://localhost:$HOST_PORT"
    export TEST_URL="$TEST_URL"
    
    # pytest 실행 (테스트 파일이 있는 경우)
    if [ -d "tests" ]; then
        python -m pytest tests/ -v --tb=short || echo "일부 테스트가 실패했습니다."
    else
        echo "tests 디렉토리가 없습니다. pytest 건너뛰기."
    fi
else
    echo "pytest가 설치되지 않았습니다. 건너뛰기."
fi

# 14. 정리
echo -e "${YELLOW}🧹 14단계: 테스트 환경 정리...${NC}"
read -p "테스트 환경을 정리하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "컨테이너 및 이미지 정리 중..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    docker rmi $IMAGE_NAME
    docker-compose down
    rm -f .env.test
    echo -e "${GREEN}✅ 정리 완료${NC}"
else
    echo -e "${BLUE}ℹ️ 테스트 환경이 유지됩니다.${NC}"
    echo "컨테이너 이름: $CONTAINER_NAME"
    echo "서비스 URL: http://localhost:$HOST_PORT"
    echo "수동 정리 명령어:"
    echo "  docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
    echo "  docker rmi $IMAGE_NAME"
    echo "  docker-compose down"
    echo "  rm -f .env.test"
fi

echo -e "${BLUE}🎉 Docker 서비스 통합 테스트 완료!${NC}"
echo "==================================" 