# Poll Service – End-to-End DevOps Project

## Overview

This project is a **complete end-to-end DevOps implementation** of a lightweight backend REST API called **Poll Service**, developed as part of a DevOps coursework assignment.

The goal of this project is to **practice DevOps concepts holistically**, covering:

- Backend development
- Containerization
- CI/CD automation
- Kubernetes deployment
- Observability (metrics, logs, dashboards)
- Security (SAST & DAST)

The service allows users to create polls, vote, and retrieve poll statistics, while being fully observable, secure, and automatically deployed.

---

## Objectives

This project fulfills the following objectives:

- Build a backend REST API
- Use **GitHub Issues & Pull Requests**
- Implement **CI/CD with GitHub Actions**
- Containerize the service with **Docker**
- Deploy to **Kubernetes (Kind)**
- Add **Observability**:
  - Metrics (Prometheus)
  - Dashboards (Grafana)
  - Structured logs
- Add **Security checks**:
  - SAST (Bandit)
  - DAST (OWASP ZAP)
- Provide clear documentation and reporting
---

## Technology Stack

| Category | Tool |
|--------|------|
Backend | FastAPI (Python 3.12)
Database | SQLite (SQLAlchemy)
CI/CD | GitHub Actions
Containerization | Docker
Orchestration | Kubernetes (Kind)
Ingress | NGINX Ingress Controller
Metrics | Prometheus
Visualization | Grafana
SAST | Bandit
DAST | OWASP ZAP

---

## API Features

### Core Endpoints

| Method | Endpoint | Description |
|------|---------|------------|
GET | `/health` | Health check
POST | `/polls` | Create a poll
DELETE | `/polls/{id}` | Delete a poll
POST | `/polls/{poll_id}/vote/{option_id}` | Vote
GET | `/polls/{poll_id}` | Poll results
GET | `/polls/{poll_id}/stats` | Poll statistics
POST | `/polls/{poll_id}/options` | Add option
DELETE | `/polls/{poll_id}/options/{option_id}` | Delete option
GET | `/metrics` | Prometheus metrics

---

## Observability

### Metrics (Prometheus)

The service exposes custom metrics:

- `poll_service_request_count`
- `poll_service_request_latency_seconds`
- `poll_service_db_operations_total`

Metrics are exposed at: /metrics


### Grafana Dashboard

A Grafana dashboard is automatically provisioned and includes:

- Request rate
- Latency
- Error rate
- Database operation counts


---

## Logging

- Structured logs using Python `logging`
- Logs include:
  - Incoming requests
  - Database operations
  - Errors and warnings


---

## Security

###  SAST – Static Analysis

- Tool: **Bandit**
- Executed during CI
- Scans Python source code for vulnerabilities

### DAST – Dynamic Analysis

- Tool: **OWASP ZAP**
- Runs against the live FastAPI service
- Reports generated:
  - HTML
  - JSON
  - Markdown

---
## CI/CD Pipeline
CI/CD Workflow (CI-CD.yml)

Triggered on:

- Push to dev or main

- Pull Requests

Pipeline steps:

1. Checkout code

2. Install dependencies

3. Run tests

4. Run Bandit (SAST)

5. Build Docker image

6. Push image to Docker Hub

7. Create Kind cluster

8. Deploy application

9. Deploy monitoring stack

## DAST Workflow (DAST.yml)

Triggered on:

- Pull Requests

Steps:

1. Start FastAPI service

2. Run OWASP ZAP scan

3. Upload security reports

## Docker

### Build Image

```bash
docker build -t poll-service .
```
### Run locally

```bash
docker run -p 8000:8000 poll-service
```
## Kubernetes Deployment

### Create Cluster

```bash
kind create cluster
```
### Deploy Application 

```bash
kubectl apply -f k8s/
```
## Repository Structure
```
.
├── app/
│   ├── main.py
│   ├── __init__.py
│   ├── database.py
│   ├── test_main.py
├── k8s/
│   ├── deployment.yml
│   ├── service.yml
│   ├── ingress.yml
│   └── monitoring/
│       ├── grafana-config.yml
│       ├── grafana-deployment.yml
│       ├── prometheus-deployment.yml
│       ├── prometheus-proxy.yaml
│       ├── grafana-dashboard-configmap.json
├── .github/workflows/
│   ├── ci-cd.yml
│   └── dast.yml
├── Dockerfile
├── requirements.txt
└── README.md
```
