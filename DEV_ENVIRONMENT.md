# Job Automation System - Development Environment

A CloudPods-inspired Kubernetes-native development environment for the Job Automation System.

## Overview

This development environment provides:

- **Containerized Services**: Docker containers for all components
- **Kubernetes Orchestration**: Full K8s deployment with monitoring
- **Development Workflows**: Automated build, test, and deployment pipelines
- **Service Mesh**: Inter-service communication and load balancing
- **Monitoring Stack**: Prometheus, Grafana, and custom metrics
- **CLI Tools**: Command-line interface for system management

## Architecture

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Web Interface │  │  Job Scraper    │  │   Automation    │
│    (Flask)      │  │   (Selenium)    │  │    Engine       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌┴─────────────────┐
         │     Redis       │    │    ClickHouse    │
         │    (Cache)      │    │   (Database)     │
         └─────────────────┘    └──────────────────┘
```

## Quick Start

### 1. Environment Setup

```bash
# Run the setup script
./scripts/setup-dev-env.sh

# Activate virtual environment
source venv/bin/activate

# Install dependencies
make install-deps
```

### 2. Development Mode

```bash
# Start development environment
make dev-up

# View logs
make dev-logs

# Stop environment
make dev-down
```

### 3. Kubernetes Development

```bash
# Set up local Kubernetes cluster
make k8s-setup

# Build and deploy services
make deploy-k8s

# Check deployment status
make k8s-status

# View logs
make k8s-logs
```

## Services

### Web Interface
- **Port**: 5000
- **URL**: http://localhost:5000
- **Purpose**: User interface for job browsing and application management

### Automation Engine
- **Port**: 8080
- **URL**: http://localhost:8080
- **Purpose**: Job application automation and API endpoints

### Job Scraper
- **Background Service**
- **Purpose**: Continuous job data collection from multiple sources

### ClickHouse Database
- **Port**: 8123 (HTTP), 9000 (Native)
- **URL**: http://localhost:8123
- **Purpose**: High-performance job data storage and analytics

### Redis Cache
- **Port**: 6379
- **Purpose**: Session management and caching

## CLI Tool - JobCtl

Similar to CloudPods' `climc`, we provide `jobctl` for system management:

```bash
# Configure the CLI
./scripts/jobctl config --set api_endpoint=http://localhost:8080

# List jobs
./scripts/jobctl jobs list --company "Google" --location "San Francisco"

# Get job statistics
./scripts/jobctl jobs stats

# Control scraper
./scripts/jobctl scraper start --source jobright
./scripts/jobctl scraper status
./scripts/jobctl scraper stop

# Submit applications
./scripts/jobctl apply submit --job-id "12345" --resume "/path/to/resume.pdf"

# View applications
./scripts/jobctl apply list

# Kubernetes management
./scripts/jobctl k8s deploy
./scripts/jobctl k8s status
./scripts/jobctl k8s logs

# Development environment
./scripts/jobctl dev up
./scripts/jobctl dev down
./scripts/jobctl dev restart
```

## Development Workflows

### Building Images

```bash
# Build all images
make build-images

# Build for multiple architectures
make build-multiarch

# Push to registry
make push-images
```

### Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Performance testing
make perf-test
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Security scan
make security-scan
```

### Database Operations

```bash
# Run migrations
make db-migrate

# Seed test data
make db-seed

# Create backup
make db-backup
```

## Kubernetes Manifests

### Namespace Structure
- **Namespace**: `jobautomation`
- **Services**: Web, Automation, Scraper, ClickHouse, Redis
- **Ingress**: Nginx-based routing
- **Monitoring**: Prometheus and Grafana

### Resource Allocation

| Service    | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------------|-------------|-----------|----------------|--------------|
| Web        | 250m        | 500m      | 512Mi          | 1Gi          |
| Automation | 1           | 2         | 2Gi            | 4Gi          |
| Scraper    | 500m        | 1         | 1Gi            | 2Gi          |
| ClickHouse | 500m        | 2         | 1Gi            | 4Gi          |
| Redis      | 100m        | 500m      | 256Mi          | 1Gi          |

### Storage

- **ClickHouse Data**: 10Gi PersistentVolume
- **Redis Data**: 1Gi PersistentVolume
- **Resumes**: 1Gi ReadWriteMany PersistentVolume

## Monitoring and Observability

### Health Checks
- **Liveness Probes**: Basic service health
- **Readiness Probes**: Service readiness for traffic
- **Health Endpoints**: `/health`, `/health/ready`, `/health/live`

### Metrics
- **Endpoint**: `/metrics`
- **Format**: Prometheus format
- **Metrics**: CPU, Memory, Disk, Database connections, Job counts

### Dashboards
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090

## Configuration Management

### Environment Variables

```bash
# Database
CLICKHOUSE_HOST=clickhouse-service
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=automation_user
CLICKHOUSE_PASSWORD=secure_password_123
CLICKHOUSE_DB=job_automation

# Redis
REDIS_HOST=redis-service
REDIS_PORT=6379

# Application
FLASK_ENV=production
MAX_APPLICATIONS_PER_HOUR=50
```

### ConfigMaps and Secrets

- **clickhouse-config**: ClickHouse server configuration
- **clickhouse-init-scripts**: Database initialization SQL
- **app-config**: Application configuration
- **clickhouse-secret**: Database credentials
- **app-secrets**: Application secrets

## Security

### Container Security
- **Non-root users**: All containers run as non-root
- **Security scanning**: Automated vulnerability scanning
- **Resource limits**: CPU/Memory limits enforced
- **Network policies**: Restricted inter-service communication

### Secrets Management
- **Kubernetes Secrets**: Encrypted secret storage
- **Base64 Encoding**: Secret value encoding
- **Secret Rotation**: Automated secret rotation support

## Production Deployment

### Staging Environment

```bash
# Deploy to staging
kubectl apply -f k8s/staging/ --context=staging

# Run staging tests
make test-staging
```

### Production Environment

```bash
# Deploy to production (with confirmation)
make prod-deploy
```

## Troubleshooting

### Common Issues

1. **Docker daemon not running**
   ```bash
   sudo systemctl start docker
   ```

2. **Kubernetes cluster not ready**
   ```bash
   minikube start --driver=docker
   ```

3. **Database connection failed**
   ```bash
   kubectl logs deployment/clickhouse-deployment -n jobautomation
   ```

4. **Service not responding**
   ```bash
   ./scripts/jobctl k8s status
   kubectl describe pod <pod-name> -n jobautomation
   ```

### Log Collection

```bash
# All service logs
kubectl logs -f --all-containers=true -n jobautomation

# Specific service logs
kubectl logs -f deployment/job-automation-deployment -n jobautomation

# Development logs
make dev-logs
```

## Contributing

### Development Process

1. **Fork and Clone**: Fork the repository and clone locally
2. **Feature Branch**: Create a feature branch
3. **Development**: Use development environment for coding
4. **Testing**: Run tests and ensure coverage
5. **Code Quality**: Format and lint code
6. **Pull Request**: Submit PR with comprehensive description

### Code Standards

- **Python**: Follow PEP 8 with Black formatting
- **Docker**: Multi-stage builds and security best practices
- **Kubernetes**: Resource limits and health checks
- **Documentation**: Comprehensive inline and README docs

## Support

### Resources

- **Makefile**: `make help` for all available commands
- **CLI**: `./scripts/jobctl --help` for CLI usage
- **Health Checks**: Service health at `/health` endpoints
- **Metrics**: Prometheus metrics at `/metrics` endpoints

### Getting Help

1. **Check logs**: Use logging commands above
2. **Review config**: Verify configuration settings
3. **Test connectivity**: Use health check endpoints
4. **Community**: Join development discussions

---

**Built with ❤️ inspired by [CloudPods](https://www.cloudpods.org) development practices**