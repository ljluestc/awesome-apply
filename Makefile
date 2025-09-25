# Job Automation System Development Makefile
# Inspired by CloudPods development environment

.PHONY: help build-images push-images deploy-k8s clean-k8s test lint format

# Default target
help:
	@echo "Job Automation System Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  build-images     Build all Docker images"
	@echo "  push-images      Push images to registry"
	@echo "  dev-up          Start development environment with docker-compose"
	@echo "  dev-down        Stop development environment"
	@echo "  dev-logs        View development logs"
	@echo ""
	@echo "Kubernetes Commands:"
	@echo "  k8s-setup       Set up Kubernetes cluster (minikube)"
	@echo "  deploy-k8s      Deploy to Kubernetes"
	@echo "  clean-k8s       Clean up Kubernetes deployment"
	@echo "  k8s-status      Show Kubernetes status"
	@echo "  k8s-logs        View Kubernetes logs"
	@echo ""
	@echo "Code Quality:"
	@echo "  test            Run all tests"
	@echo "  lint            Run linting checks"
	@echo "  format          Format code"
	@echo "  security-scan   Run security scans"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate      Run database migrations"
	@echo "  db-seed         Seed database with test data"
	@echo "  db-backup       Backup database"

# Variables
REGISTRY ?= localhost:5000
VERSION ?= latest
NAMESPACE = jobautomation

# Image names
SCRAPER_IMAGE = $(REGISTRY)/job-automation/scraper:$(VERSION)
AUTOMATION_IMAGE = $(REGISTRY)/job-automation/automation:$(VERSION)
WEB_IMAGE = $(REGISTRY)/job-automation/web:$(VERSION)

# Build all Docker images
build-images:
	@echo "Building Docker images..."
	docker build -f docker/scraper/Dockerfile -t $(SCRAPER_IMAGE) .
	docker build -f docker/automation/Dockerfile -t $(AUTOMATION_IMAGE) .
	docker build -f docker/web/Dockerfile -t $(WEB_IMAGE) .
	@echo "Images built successfully!"

# Push images to registry
push-images: build-images
	@echo "Pushing images to registry..."
	docker push $(SCRAPER_IMAGE)
	docker push $(AUTOMATION_IMAGE)
	docker push $(WEB_IMAGE)
	@echo "Images pushed successfully!"

# Development environment with docker-compose
dev-up:
	@echo "Starting development environment..."
	docker-compose up -d
	@echo "Development environment started!"
	@echo "Access the web interface at: http://localhost:5000"
	@echo "Access the automation API at: http://localhost:8080"
	@echo "Access ClickHouse at: http://localhost:8123"

dev-down:
	@echo "Stopping development environment..."
	docker-compose down
	@echo "Development environment stopped!"

dev-logs:
	docker-compose logs -f

dev-restart: dev-down dev-up

# Kubernetes setup and deployment
k8s-setup:
	@echo "Setting up Kubernetes cluster..."
	@if command -v minikube >/dev/null 2>&1; then \
		minikube start --driver=docker --memory=4096 --cpus=2; \
		minikube addons enable ingress; \
		kubectl create namespace $(NAMESPACE) || true; \
	else \
		echo "Minikube not found. Please install minikube."; \
		exit 1; \
	fi
	@echo "Kubernetes cluster ready!"

deploy-k8s: build-images
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/manifests/namespace.yaml
	kubectl apply -f k8s/manifests/secrets.yaml
	kubectl apply -f k8s/manifests/configmaps.yaml
	kubectl apply -f k8s/manifests/clickhouse-deployment.yaml
	kubectl apply -f k8s/manifests/redis-deployment.yaml
	kubectl wait --for=condition=ready pod -l app=clickhouse -n $(NAMESPACE) --timeout=300s
	kubectl wait --for=condition=ready pod -l app=redis -n $(NAMESPACE) --timeout=300s
	kubectl apply -f k8s/manifests/scraper-deployment.yaml
	kubectl apply -f k8s/manifests/automation-deployment.yaml
	kubectl apply -f k8s/manifests/web-deployment.yaml
	kubectl apply -f k8s/manifests/ingress.yaml
	@echo "Deployment complete!"

clean-k8s:
	@echo "Cleaning up Kubernetes deployment..."
	kubectl delete -f k8s/manifests/ || true
	kubectl delete namespace $(NAMESPACE) || true
	@echo "Kubernetes cleanup complete!"

k8s-status:
	@echo "Kubernetes Status:"
	@echo "=================="
	kubectl get all -n $(NAMESPACE)
	@echo ""
	@echo "Ingress:"
	kubectl get ingress -n $(NAMESPACE)

k8s-logs:
	@echo "Select service to view logs:"
	@echo "1) Scraper"
	@echo "2) Automation"
	@echo "3) Web"
	@echo "4) ClickHouse"
	@echo "5) All"
	@read -p "Enter choice (1-5): " choice; \
	case $$choice in \
		1) kubectl logs -f deployment/job-scraper-deployment -n $(NAMESPACE) ;; \
		2) kubectl logs -f deployment/job-automation-deployment -n $(NAMESPACE) ;; \
		3) kubectl logs -f deployment/job-web-deployment -n $(NAMESPACE) ;; \
		4) kubectl logs -f deployment/clickhouse-deployment -n $(NAMESPACE) ;; \
		5) kubectl logs -f --all-containers=true -n $(NAMESPACE) ;; \
		*) echo "Invalid choice" ;; \
	esac

# Testing and code quality
test:
	@echo "Running tests..."
	python -m pytest tests/ -v
	@echo "Tests completed!"

test-coverage:
	@echo "Running tests with coverage..."
	python -m pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

lint:
	@echo "Running linting checks..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	black . --line-length=127
	@echo "Code formatting complete!"

security-scan:
	@echo "Running security scans..."
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r . -x ./venv/,./tests/; \
	else \
		echo "Installing bandit..."; \
		pip install bandit; \
		bandit -r . -x ./venv/,./tests/; \
	fi
	@echo "Security scan complete!"

# Database operations
db-migrate:
	@echo "Running database migrations..."
	python -c "from comprehensive_job_automation_system import setup_database; setup_database()"
	@echo "Database migration complete!"

db-seed:
	@echo "Seeding database with test data..."
	python -c "from test_data_generator import seed_test_data; seed_test_data()"
	@echo "Database seeding complete!"

db-backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	kubectl exec deployment/clickhouse-deployment -n $(NAMESPACE) -- clickhouse-client --query "BACKUP DATABASE job_automation TO File('/var/lib/clickhouse/backup_$(shell date +%Y%m%d_%H%M%S).tar')"
	@echo "Database backup complete!"

# Performance testing
perf-test:
	@echo "Running performance tests..."
	python performance_tests.py
	@echo "Performance testing complete!"

# Monitoring setup
monitoring-up:
	@echo "Starting monitoring stack..."
	kubectl apply -f k8s/monitoring/
	@echo "Monitoring stack started!"
	@echo "Access Grafana at: http://localhost:3000 (admin/admin123)"
	@echo "Access Prometheus at: http://localhost:9090"

monitoring-down:
	@echo "Stopping monitoring stack..."
	kubectl delete -f k8s/monitoring/ || true
	@echo "Monitoring stack stopped!"

# Development utilities
install-deps:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "Dependencies installed!"

clean-python:
	@echo "Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Python cache cleaned!"

clean-all: clean-k8s dev-down clean-python
	@echo "Full cleanup complete!"

# Multi-architecture build
build-multiarch:
	@echo "Building multi-architecture images..."
	docker buildx create --use || true
	docker buildx build --platform linux/amd64,linux/arm64 -f docker/scraper/Dockerfile -t $(SCRAPER_IMAGE) --push .
	docker buildx build --platform linux/amd64,linux/arm64 -f docker/automation/Dockerfile -t $(AUTOMATION_IMAGE) --push .
	docker buildx build --platform linux/amd64,linux/arm64 -f docker/web/Dockerfile -t $(WEB_IMAGE) --push .
	@echo "Multi-architecture images built and pushed!"

# Production deployment
prod-deploy:
	@echo "Deploying to production..."
	@echo "WARNING: This will deploy to production environment!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		kubectl apply -f k8s/production/ --context=production; \
	else \
		echo "Production deployment cancelled."; \
	fi