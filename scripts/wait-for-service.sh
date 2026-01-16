#!/bin/bash

# Usage: ./wait-for-service.sh <service_name> <namespace> <port> <timeout_seconds>
SERVICE_NAME=$1
NAMESPACE=${2:-default}
PORT=${3:-8000}
TIMEOUT=${4:-120}

echo "Waiting for service $SERVICE_NAME in namespace $NAMESPACE..."

# First, wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=$SERVICE_NAME --timeout=${TIMEOUT}s -n $NAMESPACE

if [ $? -eq 0 ]; then
    echo "Pods are ready. Getting service URL..."
    
    # For NodePort service, get the node port
    NODE_PORT=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')
    
    if [ -n "$NODE_PORT" ]; then
        echo "Service is available on NodePort: $NODE_PORT"
        
        # Try to get cluster IP (for Kind/minikube)
        CLUSTER_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
        
        if [ -n "$CLUSTER_IP" ]; then
            URL="http://$CLUSTER_IP:$NODE_PORT/health"
            echo "Testing at: $URL"
            
            for i in $(seq 1 30); do
                if curl -s -o /dev/null -w "%{http_code}" "$URL" | grep -q 200; then
                    echo "Service is responding!"
                    exit 0
                fi
                sleep 2
            done
        fi
    fi
fi

echo "Service did not become ready within timeout"
kubectl describe svc $SERVICE_NAME -n $NAMESPACE
kubectl get pods -n $NAMESPACE
exit 1