# Kubernetes Deployment Guide (K8s)

This project utilizes Kubernetes (K8s) for container orchestration, ensuring a scalable and resilient environment for the MMSummary application.

## The Role of Kubernetes in This Project

Kubernetes provides several key benefits for our summarization tool:
1. **High Availability (HA)**: K8s ensures that the application remains accessible even if a container or node fails. It automatically restarts failed containers to maintain service uptime.
2. **Horizontal Scaling**: Since summarization is a computationally intensive task, K8s allows us to easily scale the number of backend replicas to handle spike loads.
3. **Service Discovery & Load Balancing**: Internal communication between the frontend and backend is managed via stable DNS names (e.g., `backend-service`), and traffic is distributed across all healthy replicas.
4. **Zero-Downtime Updates**: Using Rolling Updates, we can deploy new versions of the application without disrupting the user experience.
5. **Config & Secret Management**: Sensitive information like API keys and environment-specific settings are managed securely using K8s Secrets and ConfigMaps.

---

## Deployment Steps

### 1. Build Docker Images
Run these commands from the project root to build the container images:
```bash
# Build Backend Image
docker build -t mmsummary-backend:latest -f backend/Dockerfile .

# Build Frontend Image
docker build -t mmsummary-frontend:latest -f frontend/Dockerfile .
```

### 2. Configure Environment and Secrets
Create a `secrets.yaml` file based on `k8s/secrets.yaml.example` and fill in your actual API keys. Then apply the configurations:
```bash
kubectl apply -f k8s/secrets.yaml
```

### 3. Deploy Everything
Deploy all components to your cluster using the consolidated manifests:
```bash
# Apply Deployments (Namespace, ConfigMap, PVC, Deployments)
kubectl apply -f k8s/deploy.yaml

# Apply Services
kubectl apply -f k8s/services.yaml

# Apply Ingress (Optional, requires Ingress Controller)
kubectl apply -f k8s/ingress.yaml
```

### 4. Verify Deployment
Check the status of your pods, services, and deployments:
```bash
kubectl get all -n mmsummary
```

### 5. Cleanup (How to Delete)
To remove all deployed resources:
```bash
# Option 1: Delete using files (Sequential)
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/services.yaml
kubectl delete -f k8s/deploy.yaml

# Option 2: Delete the entire namespace (Total Cleanup)
kubectl delete namespace mmsummary
```

---

## Architecture Overview
- **Namespace**: `mmsummary` (All resources are isolated here)
- **MongoDB**: Deployed as a `ClusterIP` service on port 27017 with persistent storage (10Gi PVC)
- **Backend**: Exposed internally as a `ClusterIP` on port 8000.
- **Frontend**: Exposed via a `LoadBalancer` on port 80.
- **Ingress**: Configured for `mmsummary.local` to route `/api` to backend and `/` to frontend.
