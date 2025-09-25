#!/bin/bash
# Job Automation Development Environment Setup
# Inspired by CloudPods development environment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

install_docker() {
    print_status "Installing Docker..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Update package index
        sudo apt-get update

        # Install packages to allow apt to use a repository over HTTPS
        sudo apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # Add Docker's official GPG key
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        # Set up the repository
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker Engine
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Add user to docker group
        sudo usermod -aG docker $USER

        print_success "Docker installed successfully"
        print_warning "Please log out and log back in for docker group membership to take effect"
    else
        print_error "Unsupported OS for automatic Docker installation. Please install Docker manually."
        exit 1
    fi
}

install_kubectl() {
    print_status "Installing kubectl..."

    # Download the latest release
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

    # Validate the binary
    curl -LO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
    echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

    # Install kubectl
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

    # Clean up
    rm kubectl kubectl.sha256

    print_success "kubectl installed successfully"
}

install_minikube() {
    print_status "Installing Minikube..."

    # Download and install minikube
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    sudo install minikube-linux-amd64 /usr/local/bin/minikube
    rm minikube-linux-amd64

    print_success "Minikube installed successfully"
}

install_python_deps() {
    print_status "Installing Python dependencies..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Install development dependencies
    cat > requirements-dev.txt << 'EOF'
pytest==7.4.3
pytest-cov==4.1.0
black==23.11.0
flake8==6.1.0
bandit==1.7.5
pre-commit==3.5.0
mypy==1.7.1
isort==5.12.0
autopep8==2.0.4
safety==2.3.5
EOF

    pip install -r requirements-dev.txt

    print_success "Python dependencies installed"
}

setup_git_hooks() {
    print_status "Setting up Git hooks..."

    # Install pre-commit hooks
    source venv/bin/activate
    pre-commit install

    # Create pre-commit configuration
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-x", "tests/,venv/"]
EOF

    print_success "Git hooks configured"
}

create_dev_directories() {
    print_status "Creating development directories..."

    mkdir -p {logs,data,backups,tests,docs,scripts}
    mkdir -p k8s/{monitoring,production}
    mkdir -p docker/nginx

    print_success "Development directories created"
}

create_env_file() {
    print_status "Creating environment configuration..."

    cat > .env << 'EOF'
# Database Configuration
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=automation_user
CLICKHOUSE_PASSWORD=secure_password_123
CLICKHOUSE_DB=job_automation

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Flask Configuration
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-key-change-in-production

# Scraping Configuration
MAX_CONCURRENT_SCRAPERS=5
SCRAPE_INTERVAL=300
USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0)

# Automation Configuration
MAX_APPLICATIONS_PER_HOUR=10
SUCCESS_THRESHOLD=0.7
RETRY_ATTEMPTS=3

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
EOF

    print_success "Environment configuration created"
}

setup_monitoring() {
    print_status "Setting up monitoring configuration..."

    # Create Prometheus configuration
    mkdir -p docker/prometheus
    cat > docker/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'job-automation'
    static_configs:
      - targets: ['automation:8080']

  - job_name: 'job-scraper'
    static_configs:
      - targets: ['scraper:8080']

  - job_name: 'clickhouse'
    static_configs:
      - targets: ['clickhouse:8123']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

    # Create Grafana datasource configuration
    mkdir -p docker/grafana/{datasources,dashboards}
    cat > docker/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    print_success "Monitoring configuration created"
}

main() {
    print_status "Starting Job Automation Development Environment Setup"
    print_status "====================================================="

    # Check if we're in the right directory
    if [ ! -f "comprehensive_job_automation_system.py" ]; then
        print_error "Please run this script from the job automation project root directory"
        exit 1
    fi

    # Check for required tools and install if missing
    print_status "Checking system requirements..."

    if ! check_command python3; then
        print_error "Python 3 is required but not installed. Please install Python 3.8+."
        exit 1
    fi

    if ! check_command docker; then
        print_warning "Docker not found. Installing Docker..."
        install_docker
    fi

    if ! check_command kubectl; then
        print_warning "kubectl not found. Installing kubectl..."
        install_kubectl
    fi

    if ! check_command minikube; then
        print_warning "Minikube not found. Installing Minikube..."
        install_minikube
    fi

    # Set up Python environment
    install_python_deps

    # Create necessary directories
    create_dev_directories

    # Create environment configuration
    create_env_file

    # Set up Git hooks
    setup_git_hooks

    # Set up monitoring
    setup_monitoring

    print_success "Development environment setup complete!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Start development environment: make dev-up"
    print_status "2. Run tests: make test"
    print_status "3. Set up Kubernetes: make k8s-setup"
    print_status "4. Deploy to Kubernetes: make deploy-k8s"
    print_status ""
    print_status "Useful commands:"
    print_status "- make help           Show all available commands"
    print_status "- make dev-logs       View development logs"
    print_status "- make k8s-status     Check Kubernetes deployment status"
    print_status ""
    print_warning "Don't forget to activate your virtual environment: source venv/bin/activate"
}

main "$@"