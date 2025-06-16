#!/bin/bash

# Qshing Server 모니터링 스크립트
NAMESPACE="ns-green"

echo "📊 Qshing Server 모니터링 대시보드"
echo "=================================="

while true; do
    clear
    echo "📊 Qshing Server 모니터링 대시보드 - $(date)"
    echo "=================================="
    
    # 파드 상태
    echo "🔍 파드 상태:"
    kubectl get pods -n $NAMESPACE -l app=qshing-server -o wide
    echo ""
    
    # 파드 리소스 사용량
    echo "💾 파드 리소스 사용량:"
    kubectl top pods -n $NAMESPACE -l app=qshing-server --no-headers 2>/dev/null || echo "메트릭 서버가 설치되지 않았습니다."
    echo ""
    
    # HPA 상태
    echo "📈 HPA 상태:"
    kubectl get hpa -n $NAMESPACE
    echo ""
    
    # 서비스 상태
    echo "🌐 서비스 상태:"
    kubectl get svc -n $NAMESPACE
    echo ""
    
    # 최근 이벤트
    echo "📋 최근 이벤트 (최근 5분):"
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -5
    echo ""
    
    # 파드 로그 (에러만)
    echo "🚨 최근 에러 로그:"
    for pod in $(kubectl get pods -n $NAMESPACE -l app=qshing-server -o jsonpath='{.items[*].metadata.name}'); do
        echo "--- $pod ---"
        kubectl logs $pod -n $NAMESPACE --tail=3 --since=1m 2>/dev/null | grep -i error || echo "에러 없음"
    done
    echo ""
    
    # 헬스체크
    echo "🏥 헬스체크 상태:"
    for pod in $(kubectl get pods -n $NAMESPACE -l app=qshing-server -o jsonpath='{.items[*].metadata.name}'); do
        pod_ip=$(kubectl get pod $pod -n $NAMESPACE -o jsonpath='{.status.podIP}')
        if curl -s -f http://$pod_ip:8080/health > /dev/null 2>&1; then
            echo "✅ $pod: 정상"
        else
            echo "❌ $pod: 비정상"
        fi
    done
    echo ""
    
    echo "🔄 30초 후 새로고침... (Ctrl+C로 종료)"
    sleep 30
done 