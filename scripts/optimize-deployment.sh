#!/bin/bash

# Qshing Server 최적화 배포 스크립트
# Oracle Linux 8, 1 OCPU, 6GB 메모리 환경 최적화

set -e

NAMESPACE="ns-green"
DEPLOYMENT_NAME="qshing-server-deployment"

echo "🚀 Qshing Server 최적화 배포를 시작합니다..."
echo "📋 환경: Oracle Linux 8, 1 OCPU, 6GB 메모리"

# 1. 현재 파드 상태 확인
echo "🔍 현재 파드 상태 확인..."
kubectl get pods -n $NAMESPACE -l app=qshing-server -o wide

# 2. 리소스 사용량 확인
echo "💾 현재 리소스 사용량 확인..."
kubectl top pods -n $NAMESPACE -l app=qshing-server 2>/dev/null || echo "메트릭 서버가 설치되지 않았습니다."

# 3. 최적화된 배포 적용
echo "🔄 최적화된 배포 적용 중..."
kubectl apply -f k8s/resource-optimization.yaml

# 4. 배포 상태 확인
echo "⏳ 배포 상태 확인 중..."
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=600s

# 5. 새로운 파드 상태 확인
echo "🔍 새로운 파드 상태 확인..."
kubectl get pods -n $NAMESPACE -l app=qshing-server -o wide

# 6. 헬스체크 수행
echo "🏥 헬스체크 수행 중..."
sleep 30  # 파드 완전 시작 대기

for pod in $(kubectl get pods -n $NAMESPACE -l app=qshing-server -o jsonpath='{.items[*].metadata.name}'); do
    echo "--- $pod 헬스체크 ---"
    pod_ip=$(kubectl get pod $pod -n $NAMESPACE -o jsonpath='{.status.podIP}')
    
    # 헬스체크 시도
    if kubectl exec $pod -n $NAMESPACE -- curl -f http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ $pod: 헬스체크 성공"
    else
        echo "❌ $pod: 헬스체크 실패"
    fi
    
    # 준비 상태 확인
    if kubectl exec $pod -n $NAMESPACE -- curl -f http://localhost:8080/ready > /dev/null 2>&1; then
        echo "✅ $pod: 준비 상태 확인"
    else
        echo "❌ $pod: 준비 상태 실패"
    fi
done

# 7. 메모리 사용량 모니터링
echo "📊 메모리 사용량 모니터링..."
for pod in $(kubectl get pods -n $NAMESPACE -l app=qshing-server -o jsonpath='{.items[*].metadata.name}'); do
    echo "--- $pod 메모리 사용량 ---"
    kubectl top pod $pod -n $NAMESPACE 2>/dev/null || echo "메트릭을 가져올 수 없습니다."
done

# 8. 로그 확인 (에러 체크)
echo "📋 최근 로그 확인..."
for pod in $(kubectl get pods -n $NAMESPACE -l app=qshing-server -o jsonpath='{.items[*].metadata.name}'); do
    echo "--- $pod 로그 (최근 10줄) ---"
    kubectl logs $pod -n $NAMESPACE --tail=10 | grep -E "(ERROR|WARN|Exception)" || echo "에러 없음"
done

# 9. HPA 상태 확인
echo "📈 HPA 상태 확인..."
kubectl get hpa -n $NAMESPACE

echo "✅ 최적화 배포가 완료되었습니다!"
echo ""
echo "📋 최적화 적용 사항:"
echo "  - 메모리 제한: 2.5GB (기존 대비 최적화)"
echo "  - CPU 제한: 800m (1 OCPU의 80%)"
echo "  - Chrome 메모리: 512MB로 제한"
echo "  - 타임아웃: 20초로 단축"
echo "  - 재시도: 2회로 단축"
echo "  - 캐시 TTL: 12시간으로 단축"
echo ""
echo "🔍 모니터링 명령어:"
echo "  kubectl get pods -n $NAMESPACE -l app=qshing-server -o wide"
echo "  kubectl top pods -n $NAMESPACE -l app=qshing-server"
echo "  ./scripts/monitor.sh" 